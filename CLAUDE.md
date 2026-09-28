# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado del repositorio

Implementado (git, repositorio privado en GitHub; ver "Despliegue"): `app.py` (UI), comunes `anio.py` (regla del año), `resumen.py` (uso,
material y tipología de la ficha), `direccion.py` (analizador de direcciones y formatos por
ciudad) y `mapa.py` (mapa folium del inmueble), `municipios/` (registro `MUNICIPIOS` en `__init__.py` + un archivo por ciudad; las 6
consultan), pruebas en `tests/`, evaluación real con `python evaluar.py` (`casos_prueba.csv` y
`casos_variables.csv`). Estructura, contrato de ciudad v2 y decisiones: `ARQUITECTURA.md`
sección 5 (la 3 queda como historia del contrato v1).

## Objetivo

Aplicación Streamlit muy simple: el usuario elige un municipio (Bogotá, Medellín, Cali,
Barranquilla, Bucaramanga o Manizales), escribe una dirección y la app devuelve la ficha del
inmueble desde fuentes catastrales oficiales: **año de construcción, material de la estructura,
uso (con CIIU si hubiera fuente), número de pisos, coordenadas y tipología** (casa, edificio de
apartamentos, bodega, oficina…). Lo que una ciudad no publica se muestra como "Sin dato" con el
motivo (`MUNICIPIOS[ciudad]["sin_dato"]`), nunca inventado. Hoy: año y material solo en Bogotá;
CIIU en ninguna; uso, pisos, coordenadas y tipología en las 6.

## Restricciones (no negociables)

- **Solo Python.** Es el único lenguaje que el usuario maneja. Nada de JS/TS, Docker, Terraform,
  ni servicios auxiliares en otros lenguajes.
- **Local + Streamlit Community Cloud.** Se ejecuta con `streamlit run` y, desde el 2026-09-27
  (autorizado por el usuario), también en Streamlit Community Cloud (ver "Despliegue"). No
  introducir otros despliegues, contenedores, CI, bases de datos ni infraestructura sin que el
  usuario lo pida.
- **Solo fuentes gubernamentales.** Los datos de dirección, geocodificación y catastro deben venir
  de servicios oficiales: gestores catastrales municipales oficiales (UAECD / Catastro Bogotá,
  Catastro de Medellín, Subdirección de Catastro de Cali, Gerencia de Gestión Catastral de
  Barranquilla, AMB, MASORA…), sus geoportales y portales de datos abiertos (IDECA, Datos Abiertos
  Bogotá, MEData, datos.cali.gov.co…), el IGAC y datos.gov.co.
  No usar Google Maps, Mapbox, OpenStreetMap/Nominatim ni scraping de portales privados. No
  saltarse logins, captchas, bloqueos anti-bots ni pagos.
- **Alcance mínimo.** No expandir a "territorio inexplorado": si una funcionalidad no es necesaria
  para ir de una dirección al año de construcción, no se implementa.

## Arquitectura

Tres pasos, mantenidos como funciones separadas para que cada uno se pueda probar aislado: pasos 1
y 2 en `municipios/<ciudad>.py`, paso 3 común en `anio.py` y `resumen.py`, registro en
`municipios/__init__.py`; receta para agregar una ciudad en `ARQUITECTURA.md` 5.4.

1. **Dirección → coordenadas / identificador predial.** Geocodificación contra el servicio oficial
   de Bogotá. La normalización de direcciones bogotanas (nomenclatura `Calle/Carrera/Diagonal`,
   `#`, `bis`, `sur`) es la parte frágil: aislarla en su propia función pura.
2. **Coordenadas / CHIP o matrícula → registro catastral.** Consulta al servicio de Catastro
   Multipropósito para obtener los atributos del predio.
3. **Registro → ficha.** Año (mayor área por año, empate el más antiguo), uso y material (el de
   mayor área), pisos (máximo del lote), tipología derivada del uso y los pisos (`resumen.py`).

`app.py` es solo la capa Streamlit: input, llamada a los pasos, presentación. Sin lógica de
consulta dentro del archivo de UI.

## Antes de escribir código contra un servicio

Los endpoints oficiales cambian y no están asumidos aquí. Verificar la URL, los parámetros y el
formato de respuesta reales (con `curl` o un script corto) y anotar el hallazgo en este archivo
antes de construir sobre ellos. No inventar nombres de campos.

### Hallazgos verificados (2026-09-25) — detalle en `FUENTES.md`

- **Geocodificación:** `GET https://catalogopmb.catastrobogota.gov.co/PMBWeb/web/api`
  con `cmd=geocodificar`, `apikey=e2d6f043-7b63-417e-8fbe-db515898576f` (clave pública del visor
  oficial mapas.bogota.gov.co; no documentada para terceros, puede rotar) y `query=<dirección>`
  (acepta texto libre; quitar `#` y tildes). Campos: `response.success`,
  `response.data.lotcodigo`, `latitude`, `longitude`, `dirtrad`, `tipo_direccion`
  (`"Asignada por Catastro"` exacta / `"Dirección por aproximación"` → avisar; puede venir sin
  `lotcodigo`).
- **Año de construcción:** tabla Predio
  `GET https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/catastro/lote/MapServer/3/query`
  con `where=BARMANPRE='<lotcodigo>'`, `returnDistinctValues=true`, `f=json`.
  Campo del año: **`PREVETUSTZ`** ("Vetustez", definido por IDECA como "Año de la construcción").
  Una fila por predio (`PRECHIP`) × unidad (`PREUCALIF`) × uso (`PRECUSO`), con área `PREAUSO`.
  Hay filas duplicadas si no se usa `returnDistinctValues`. `maxRecordCount` 2000 (paginar en PH).
- **Qué año mostrar:** el `PREVETUSTZ` con mayor suma de `PREAUSO` en el lote; listar los demás.
- `catastro/construccion/MapServer/0` **no** tiene año. `catastro/lote/MapServer/0` da
  `LOTCODIGO` por punto (wkid 4326) como respaldo.
- Casos de prueba: `casos_prueba.csv` (columna `municipio`; hoy solo filas de Bogotá). Respuestas
  crudas: `tests/fixtures/<ciudad>/` (Bogotá en `tests/fixtures/bogota/`).

### Hallazgos verificados (2026-09-26): otros municipios. Detalle en `FUENTES_MUNICIPIOS.md`

Resumen: **ninguna de las 5 ciudades publica el año de construcción en una fuente oficial
abierta** que se pueda consultar hoy. Desde el 2026-09-27 la app sí las consulta (uso, pisos,
coordenadas) y muestra el año como "Sin dato" con este motivo.

- **Medellín** (Catastro de Medellín, reverificado 2026-09-27 sobre el geovisor MapGIS y los 301
  servicios de `servidormapas`): dirección→CBML sí funciona (`GET .../servicios5/GEOCOD_WEB_MAPGIS9/
  geocodificador/service/geocod?dir=...&accion=11111111111` → `cbml`, `p13` lat, `p12` lon). El
  año existe (`anio_construccion`/`anioconstruccion` en capas LADM, `ide_catastro/6` e
  `HistoricoCatastral`; `anio_const` en el GP `info_uconst_cbml`) pero está vacío en más del 99,9 %
  y los pocos valores son 2025/2024/2021 o basura. Solo la ficha catastral (con login) trae la edad.
- **Cali** (Subdirección de Catastro): dirección→`npn` sí funciona (WFS
  `ws-idesc.cali.gov.co/geoserver`, capa `catastro:cat_bas_terrenos`, campo `direpred`), pero
  `arcgisportal.cali.gov.co/agserver1/.../Catastro/MapServer` no tiene año
  (`SE_ANNO_CAD_DATA` es un blob CAD, no un año). `geoportal.cali.gov.co` ya no existe.
- **Barranquilla** (Gerencia de Gestión Catastral): dirección→NPN sí funciona (ArcGIS Online de la
  Alcaldía, `Direccion/FeatureServer/0`, `Direccion`→`Codigo_1`). `Catastro25/FeatureServer/1`
  tiene `anio_const`, pero vale 0 en el 99,9 % (290.842 de 291.182). El portal de catastro bloquea
  clientes automáticos (Cloudflare).
- **Bucaramanga** (AMB, gestor desde 2020): `anio_construccion`/`anio_const` vacíos en la GDB
  oficial 2023 y en el visor AMB; R1/R2 (datos.gov.co, vigencia 2021) sin año.
- **Manizales** (MASORA, por contrato desde 2021): el portal SISMAS exige registro, login, captcha y
  pago; el geoportal de la Alcaldía no tiene capas catastrales.
- **Nacional:** el IGAC SINIC/RIC (`sigi.igac.gov.co/habilitacion/rest/services/sinic/ric/FeatureServer`)
  tiene `anio_construccion` para todo el país, pero nulo en los 8.016.896 registros (en las 6
  ciudades la foto es del 2025-06-18). Reverificar periódicamente: si se llena, serviría como fuente común.
- **Varias construcciones:** si alguna ciudad publica el año, aplicar la misma regla de Bogotá
  (mayor suma de área por año, empate = el más antiguo), tratando 0/nulo como sin dato.

### Hallazgos verificados (2026-09-27): las 6 variables. Detalle en `FUENTES_VARIABLES.md`

- **Bogotá:** tabla Predio también da `PRECUSO`/`PRECDESTIN` (dominios en el servicio) y
  `PREEARMAZ`/`PREEMUROS` (códigos 111–115 y 121–125, tabla del catálogo IDECA `CO_Predio_MR.pdf`).
  Pisos: máximo `CONNPISOS` de `catastro/construccion/MapServer/0` por `LOTECODIGO`.
- **Medellín:** geocodificador MapGIS → `cbml`, `p13`/`p12`; capa 6 `destinacion`, capa 19
  `numero_pisos`, capa 18 `uso` (dominio LADM, cobertura parcial). IPv6 de medellin.gov.co no
  responde: el adaptador fuerza IPv4.
- **Cali:** WFS `catastro:cat_bas_terrenos` por `direpred` (`KR 100 # 11 A - 25`): `destinacio`,
  `uso_princi`, `total_pis1/2`, `area_cons1/2`, polígono en EPSG:4326.
- **Barranquilla:** ArcGIS Online de la Alcaldía: `Direccion/FeatureServer/0` → NPN y punto;
  `Mapa_Distrito_de_Barranquilla_WFL1` capas 1 (`DESTINO_g`) y 3 (`Numero_Pisos`).
  `catastro/datosabiertos` respondió 403 (Cloudflare) el 2026-09-27: no se usa.
- **Bucaramanga:** R1/R2 datos.gov.co (2021) + terreno AMB `Unidad_terreno_BGA/MapServer/1`
  (`local_id` = `68001` + número R1, solo NPH).
- **Manizales:** RIC IGAC capa 0 (`direccion`, `destinacion_economica`, centroide) y capa 2
  (`numero_pisos`) por los 21 dígitos del terreno.
- **CIIU:** ninguna fuente oficial pública liga dirección y CIIU (RUES en datos.gov.co no trae
  dirección; los datos distritales son agregados). No convertir uso catastral a CIIU.
- **Mapa base (folium):** "World Street Map" de Esri (estilo Google Maps, solo visual; no es
  fuente de datos), un marcador sin texto. No usar teselas de Google (términos) ni OpenStreetMap.

## Comandos

Entorno con `uv` (disponible en la máquina):

```bash
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
streamlit run app.py
```

Pruebas (sin red, con fixtures) y evaluación real:

```bash
uv run pytest              # todas
uv run pytest -k nombre    # una sola
uv run python evaluar.py   # punta a punta contra los servicios reales (casos_prueba.csv)
```

## Despliegue

Streamlit Community Cloud (gratis) desde el repositorio **privado** de GitHub, rama `main`,
archivo `app.py`, Python 3.13. La app está marcada como pública en Settings → Sharing para que el
link abra sin login. Cada `git push` a `main` la actualiza sola (1–2 min). Dependencias:
`requirements.txt`. Límites: se duerme tras 12 h sin visitas (se despierta con un clic) y corre
en servidores de EE. UU., así que un servicio oficial podría rechazar esa IP aunque funcione
desde Colombia. Antes de hacer push: `uv run pytest` en verde.
