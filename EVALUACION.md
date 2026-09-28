# Evaluación v2 (2026-09-26): municipios

Evaluador independiente, 2026-09-26. Alcance: selector de 6 municipios, Bogotá con fuente y 5 ciudades
con aviso "sin fuente". No se tocó código ni pruebas. Los scripts de verificación están en el
scratchpad de la sesión (`eval_*.py`, `nonet.py`, `csv_check.py`, `scan_*.py`, `eval_ui/ui_eval.py`).

**Veredicto: NO APROBADO.** Bogotá da 8/8, la UI no tiene excepciones, las pruebas no usan la red y
se cumplen las restricciones. Falla un criterio: **la conclusión "sin fuente" no se sostiene para
Barranquilla.** La Alcaldía publica un servicio catastral oficial abierto de 2026
(`miciudad.barranquilla.gov.co/.../catastro/datosabiertos/MapServer`). Su campo `anio_construccion`
tiene valor en las **506.672 de 506.672** unidades de construcción, y hay una cadena completa
dirección → predio → año. Con él, el caso de referencia "sin fuente" del Investigador
(Carrera 55 # 48-26) da **2001**. Para Medellín, Cali, Bucaramanga y Manizales la conclusión sí se
sostiene, aunque el motivo que muestra la app para Medellín no es exacto.

## 1. Pruebas unitarias (`uv run pytest`)

`28 passed in 0.66s`: test_anio 4, test_app 4, test_bogota 17 y test_municipios 3. Coincide con
ARQUITECTURA.md 3.2.

**Ninguna prueba usa la red.** Se comprobó de dos formas independientes:

- Con un plugin propio (`-p nonet`) que reemplaza `socket.connect` y `getaddrinfo` por funciones
  que fallan y registran cada intento: `28 passed`, **0 intentos de red**.
- Con `unshare -rn`, que corre las pruebas en un namespace sin interfaces de red: `28 passed`.

## 2. Casos por municipio

### 2.1 Bogotá: `uv run python evaluar.py` contra los servicios reales

| Dirección | Esperado | Obtenido | Lote | ✔/✘ |
|---|---|---|---|---|
| Carrera 7 # 1-34 Sur | 1970 | 1970 | 001101001009 | ✔ |
| Calle 45A Bis # 19-61 | 1950 | 1950 | 007205026008 | ✔ |
| Avenida Carrera 68 # 1A-56 | 1971 | 1971 | 004304093003 | ✔ |
| Diagonal 40A Sur # 34A-62 | 1984 | 1984 | 002311021046 | ✔ |
| Calle 48 Sur # 4B-42 Este | 1984 | 1984 | 001328010005 | ✔ |
| Calle 26 # 13-19 | 1948 | 1948 | 003101009008 | ✔ |
| Calle 72 # 10-34 | 1978 | 1978 | 008306017001 | ✔ |
| Calle 127 # 7-25 | 1970 | 1970 | 008413024020 | ✔ |

**8/8 = 100 %.** Todas son exactas (`Aprox. False`), el script sale con código 0 y tarda unos 6 s.

**Verificación independiente, por caminos distintos a los de la app:**

- **Archivo masivo de Datos Abiertos Bogotá** (`tpredio.csv.08.26.zip`, 169 MB, `TPREDIO.csv` del
  2026-09-03): se leyó completo, sin REST ni geocodificador. Se filtró por `BARMANPRE`, se quitaron
  las filas repetidas y se aplicó la regla de mayor área. Los **8 lotes coinciden**: 1970 (81,5 m²),
  1970 (465,02), 1978 (490 filas, 33.847 m²), 1984 (120,47), 1984 (204,6) + 2012 (51,6),
  1971 (1.000,91) + 2021 (11,52), 1950 (225,48) y 1948 (289 filas).
- **Tabla Predio consultada por dirección** (`PREDIRECC LIKE`), sin geocodificador:
  `DG 40A SUR 34A 62` da el lote 002311021046 y 1984. `AK 68 1A 56` da 004304093003 y 1971; sin
  `returnDistinctValues` suma 6.005 m² para 1971 contra 69 m² para 2021, es decir, las filas
  duplicadas multiplican el área, pero el año principal no cambia. `CL 45A BIS  19 61` da
  007205026008 y 1950.

### 2.2 Ciudades sin fuente (AppTest, con `requests.get` y `socket.connect` prohibidos)

| Ciudad | Aviso esperado (ARQUITECTURA 3.4) | Aviso obtenido | ✔/✘ UI | ¿Es verdad lo que dice el aviso? |
|---|---|---|---|---|
| Medellín | warning "Sin fuente oficial pública para este municipio." + gestor/motivo + "Consulta directa con el gestor:" | idéntico, sin campo de dirección, 0 llamadas | ✔ | En parte: el motivo dice que las capas "no incluyen el año", pero sí lo incluyen, vacío en más del 99 % (§3) |
| Cali | ídem | idéntico, 0 llamadas | ✔ | Sí |
| Barranquilla | ídem | idéntico, 0 llamadas | ✔ | **No**: sí existe una fuente oficial abierta con año (§3) |
| Bucaramanga | ídem | idéntico, 0 llamadas | ✔ | Sí |
| Manizales | ídem | idéntico, 0 llamadas | ✔ | Sí |

## 3. Auditoría de la conclusión "sin fuente"

| Ciudad | Afirmación del Investigador | Verificación propia (2026-09-26) | ¿Se sostiene? |
|---|---|---|---|
| **Medellín** | Las capas públicas Lote y Construcción (`servidormapas`) y MEData no tienen campo de año. `www.medellin.gov.co` daba 404 en todo el dominio. Esquemas tomados del índice de ArcGIS Hub. | El portal **volvió** (200) y `servidormapas/rest/services` responde con 30 carpetas. En `ServiciosCatastro` hay 11 servicios que el Investigador no pudo ver. **El campo de año sí existe**, pero casi vacío: `ConsultaOperadorCatastral/MapServer/11` (UConstruccion_LADM) `anio_construccion>0` en 675 de 236.284 (0,29 %), con valores que no son años de construcción (2025×541, 2024×72, 2022×21, y 1, 2, 3, 29, 32767); `ide_catastro/MapServer/6` `anioconstruccion>0` en 100 de 1.144.339 (todos 2021); `HistoricoCatastral/MapServer/154` en 261 de 1.160.211 (2021, 1, 52, 400); `ConsultaOperadorCatastral_geo/21` y `vivienda_ciudad_terri/VA_ConsultaOperadorCatastral/17` en 0 de ~307.140. El GP `vivienda_ciudad_terri/infouconstlote` (`info_uconst_cbml`) dio 0 de 20 lotes al azar con año. El GP `infopredio` falla con error del servidor e `infoGDB` no trae año. En la org de ArcGIS Online `FZVaYraI7sEGQ6rF` (1.085 capas) solo hay años de ciclorrutas, puentes y licencias. MEData "Información Predios" no tiene año (confirmado). La ficha catastral individual sí trae "EDAD DE LA CONSTRUCCIÓN (EN AÑOS)", pero es un PDF por predio que pide usuario. | **Sí**, no hay fuente utilizable (confianza alta). Hay que corregir el motivo y el dato del 404. |
| **Cali** | `agserver1/.../Catastro/MapServer` no tiene año (`SE_ANNO_CAD_DATA` es un blob CAD). El WFS de la IDESC y datos.cali.gov.co tampoco. `edad_const` aparece solo en las ofertas del OIC. | Esquema de la capa 3 Construcciones confirmado: `SE_ANNO_CAD_DATA` es de tipo `esriFieldTypeBlob`. Se barrió todo `agserver1` (8 carpetas, 393 capas): los únicos campos de año son `anio_construccion` "Año aproximado de construcción" en formularios Survey123 de gestión del riesgo (solo edificios visitados) y `edad_const` en `OFERTAS2026`. El WFS `catastro:` tiene 3 tipos (terrenos, construcciones, manzanas) y ninguno tiene año. En `predios-municipio-2024.xlsx` (datos.cali) las 18 columnas no incluyen año (`VIGENCIA` es la de avalúo). | **Sí** (alta) |
| **Barranquilla** | `Catastro25/FeatureServer/1` tiene `anio_const` > 0 en solo 340 de 291.182. `Mapa_Distrito…/3` y `LADM_COL_ESQUEMA` están vacíos. El portal bloquea clientes automáticos (Cloudflare). Se revisaron 1.343 servicios. | El conteo se **confirma**: 291.182 en total, 340 con valor > 0 y 0 nulos, con la misma distribución. `Mapa_Distrito_de_Barranquilla_WFL1/3`, `Mapabase_…_V3/1` y `Mapa_ladm/0` dan 0 con año, y `LADM_COL_ESQUEMA/4,38,76` están vacías. **Pero se pasó por alto una fuente:** el item público **"Catastro_Entidad"** (`154d5320cba74e6f8fdfbdde2ba309bd`, dueño `planeacion_territorial_baq` de la org de la Alcaldía, snippet "Informacion oficial castasstro en linea 2026", tags "datos abiertos", 5.171 vistas; lo usa el mapa público "WM PANORAMA URBANO" como "Catastro en linea") apunta a `https://miciudad.barranquilla.gov.co/gis/rest/services/catastro/datosabiertos/MapServer`. En esa URL, la tabla `505 Caracteristicas Unidad de Construcción` tiene el campo **`anio_construccion`** (alias "Año Construcción", dominio 1512–2500), con **506.672 de 506.672 > 0**. Hay 105 años distintos: 1980–2029 concentra el 95 %, 1986 suma 50.093 (posible valor por defecto) y 2.417 filas están en los límites del dominio (1512/2500), que no son válidos. Cadena verificada: capa `105 Dirección` (`clase_via_principal`, `valor_via_principal`, `valor_via_generadora`, `numero_predio`) → relación `CR_Predio` (500, `numero_predial_nacional`) → `CR_UnidadConstruccion` (305) → `CR_CaracteristicasUnidadConstruccion` (505). **Ejemplo real:** "Carrera 55 48 26" da el NPN 080010101000002110002000000000, con la unidad A de **2001** (227 m², residencial) y la unidad B de 1981 (2 m², anexo). Con la regla de `anio.py` el resultado es **2001**. En una muestra al azar de 25 direcciones principales, 17 dan un año plausible; las otras no tienen unidades de construcción (lotes, uso religioso, etc.). Sobre el acceso: con `requests`, el cliente de la app, responde 200; con `curl` y su User-Agent por defecto responde 403 de Cloudflare, que es lo que vio el Investigador. No se cambió el User-Agent ni se evadió nada. Evidencia cruda: `eval_baq_evidencia.json` en el scratchpad. | **No** (confianza alta) |
| **Bucaramanga** | `anio_const` está vacío en el visor AMB y `anio_construccion` es nulo en la GDB 2023. R1 y R2 no tienen año. El RIC no tiene unidades de construcción de Bucaramanga. | `VISOR/Alturas_Registradas/0`: 230.635 registros, `anio_const>0` en 0. `VISOR/MyMapService/0`, que es una copia, también da 0. En `mapa.amb.gov.co/server` (72 servicios, 563 capas) no hay otras capas con año. En datos.gov.co no aparece ningún dataset con "vetustez" ni con `anio_construccion`. La GDB 2023 (57 MB) **no** se volvió a leer. | **Sí** (alta; la GDB no se reverificó) |
| **Manizales** | SISMAS (MASORA) exige registro, captcha y pago. El geoportal de la Alcaldía no tiene capas prediales. En el RIC el año es nulo. | RIC `numero_predial = 170010101000000730012000000000`: 2 unidades (36,6 y 79,9 m²) con `anio_construccion` nulo. El RIC tiene 120.310 unidades en Manizales. En la org `PtpS85InlUyG2Gqs` (324 servicios, 920 capas) no hay capas prediales con año. En ArcGIS Online no hay contenido de MASORA. No se entró a SISMAS (evitar el login). | **Sí** (alta-media) |
| **IGAC RIC** (común) | `anio_construccion IS NOT NULL` da 0 en los 8.016.896 registros. | `IS NOT NULL` → `{"count":0}`; `> 0` → `{"count":0}`. | **Sí** |

## 4. UI (AppTest y servidor real)

Script `eval_ui/ui_eval.py`. Bogotá se probó con red real. En las 5 ciudades se reemplazaron
`requests.get` y `socket.connect` por funciones que fallan si se llaman.

| Escenario | Resultado | Excepción |
|---|---|---|
| Bogotá válida, "Calle 72 # 10-34" + clic | métrica 1978, pie "CL 72 10 34 · Lote: 008306017001" | no |
| Bogotá con varias construcciones, "Calle 48 Sur # 4B-42 Este" | 1984; desglose 1984: 204.6 m² / 2012: 51.6 m² | no |
| Bogotá aproximada, "Carrera 13 Bis # 17-44" | warning "Dirección aproximada: se usó KR 13 17 44…", métrica 1975 | no |
| Bogotá inválida: "asdf", "Calle 999 # 999-99", "'; DROP--" | "Dirección no encontrada." | no |
| Vacía + clic, o solo espacios + clic | "Escribe una dirección." | no |
| Errores simulados: Timeout, ConnectionError, HTTP 500, respuesta no JSON | "Servicio no disponible. Intenta de nuevo más tarde." | no |
| Cada una de las 5 ciudades sin fuente | warning + 2 textos exactos, sin `text_input`, **0 llamadas de red** | no |
| Bogotá (1984) → Medellín → Bogotá, y luego "Carrera 7 # 1-34 Sur" | aviso de Medellín; al volver el campo aparece vacío y la consulta da 1970 | no |
| Recorrer las 6 ciudades y volver a Bogotá | campo de dirección presente, sin errores | no |

**21/21 escenarios correctos (incluye la carga inicial de Bogotá) y 0 excepciones no controladas.**
`uv run streamlit run app.py --server.headless true --server.port 8599`: `/_stcore/health` responde
200 "ok" y `GET /` responde 200 (7.260 B). Después se detuvo el servidor; el puerto quedó cerrado
(`000`).

## 5. Restricciones

| Restricción | Estado |
|---|---|
| Solo URLs oficiales | ✔ Se llaman solo `catalogopmb.catastrobogota.gov.co` y `serviciosgis.catastrobogota.gov.co` (municipios/bogota.py:14-15). Las 5 URLs de `municipios/__init__.py` (:16, :24, :33, :41, :49) son solo texto que se muestra, y todas son `.gov.co`. |
| `app.py` sin lógica de consulta | ✔ Importa `requests` solo para el `except` (app.py:24) y llama únicamente `municipio["consultar"]` y `elegir_anio`. |
| Solo Python y solo local | ✔ El proyecto no tiene archivos que no sean `.py/.md/.csv/.json/.txt`. `requirements.txt` = streamlit, requests, pytest. |
| Timeouts | ✔ `timeout=TIMEOUT` (15 s) en bogota.py:32 y :64, y `falso_get` exige timeout en cada llamada. Las ciudades sin fuente no hacen ninguna llamada. |
| Tamaño y simplicidad | ✔ 206 líneas de app (app 45, anio 22, `__init__` 51, bogota 88), evaluar 33 y pruebas 227, como dice ARQUITECTURA §4. |
| Receta 3.5 (agregar una ciudad sin tocar las otras) | ✔ `app.py` solo lee claves genéricas (`gestor`, `consultar`, `nombre_codigo`, `direccion_oficial`, `aproximada`, `codigo`, `construcciones`). Agregar Barranquilla sería: crear `municipios/barranquilla.py`, reemplazar su entrada en `MUNICIPIOS`, agregar filas al CSV y ~5 líneas en `evaluar.py`, sin tocar `bogota.py`, `anio.py` ni `app.py`. Detalle menor: el texto "Construcciones en el lote:" (app.py:43) está pensado para Bogotá. |

**Enlaces de "Consulta directa con el gestor"** (probados con curl con UA de navegador y con `requests`):

| Ciudad | URL | Resultado |
|---|---|---|
| Medellín | https://www.medellin.gov.co | 200. También responde 200 el enlace directo https://www.medellin.gov.co/es/tramites-y-servicios/ficha-catastral-predio/ |
| Cali | …/hacienda/publicaciones/164112/como-tramitar-facil-y-rapido-su-certificado-catastral/ | 200 ("¿Cómo tramitar fácil y rápido su certificado catastral?") |
| Barranquilla | https://catastro.barranquilla.gov.co/identifica-tu-predio/ | **403 de Cloudflare** a clientes automáticos (curl y requests). No se pudo comprobar en un navegador. |
| Bucaramanga | https://www.amb.gov.co/consultas-catastro/ | 200 con UA de navegador; 403 con el UA de python-requests |
| Manizales | https://masora.gov.co/gestion-catastral-manizales/ | 200 ("Gestión Catastral Manizales - Masora") |

## 6. Coherencia de documentos con el código y con la realidad

- ✔ ARQUITECTURA.md 3.2 y §4: la estructura, el contrato, los 28 tests y los tamaños coinciden con
  el código. Existen todos los fixtures que citan CLAUDE.md, FUENTES.md y FUENTES_MUNICIPIOS.md.
  FUENTES.md ya nombra `municipios/bogota.py`.
- ✔ Las observaciones de la v1 están resueltas: la API key rechazada lanza `RequestException`
  (bogota.py:35-36); hay aviso para entrada vacía (app.py:18-19); se quitaron `lat` y `lon`; las
  áreas negativas cuentan como 0 (anio.py:18); CLAUDE.md ya no dice "Repositorio vacío".
- ✘ **Barranquilla:** CLAUDE.md:16-18 y :83-84 ("Solo Bogotá tiene fuente", "ninguna de las 5…"),
  CLAUDE.md:92-95, FUENTES_MUNICIPIOS.md:9 (conclusión), :176-181 y :397 ("Carrera 55 # 48-26 → sin
  fuente oficial pública") contradicen el servicio `catastro/datosabiertos` (§3).
- ✘ **Medellín:** CLAUDE.md:86-87 y FUENTES_MUNICIPIOS.md:86-88 dicen que el dominio da 404 y que las
  capas no tienen campo de año. Hoy responde 200 y el campo existe, casi vacío.
  FUENTES_MUNICIPIOS.md ("No se pudo comprobar si la ficha individual trae el año"): la ficha trae
  "EDAD DE LA CONSTRUCCIÓN (EN AÑOS)".

## 7. Fallas

1. **Barranquilla aparece "sin fuente" pero tiene fuente oficial abierta con año.** Está en
   municipios/__init__.py:27-35 (`"consultar": None`, motivo en :30-31). *Causa probable:* el barrido
   del Investigador revisó las capas "hosted" de ArcGIS Online (`Catastro25`, `LADM_COL_ESQUEMA`,
   `Mapa_Distrito…`), que están vacías, pero no el servicio del servidor propio
   `miciudad.barranquilla.gov.co`, registrado en la misma org como "Catastro_Entidad". Además, el 403
   de Cloudflare a `curl` en `*.barranquilla.gov.co` se leyó como bloqueo total. *Corrección:*
   documentar la fuente en FUENTES_MUNICIPIOS.md y crear `municipios/barranquilla.py` con la receta
   3.5:
   - Normalizar la dirección a componentes: tipo de vía en palabra completa, número, letra, vía
     generadora y placa.
   - Consultar la capa 105 y seguir `queryRelatedRecords` 105→500→305→505 hasta obtener los pares
     (`anio_construccion`, `area_construida`).
   - Descartar años fuera de un rango plausible, como 1512 y 2500 del dominio.
   - Agregar al menos 5 filas en `casos_prueba.csv` con el año confirmado por otra vía, más el
     umbral por municipio en `evaluar.py`.
   - Usar `requests` y **no** curl: curl recibe 403 de Cloudflare.

   Si el usuario prefiere no implementarlo todavía, el motivo actual igual es falso ("vale 0 en el
   99,9 %"): hay que decir que existe una fuente todavía sin integrar.
2. **El motivo de Medellín no es exacto** (municipios/__init__.py:13-14): dice "no incluyen el año",
   pero el campo existe en `ConsultaOperadorCatastral` e `ide_catastro` y está vacío o tiene valores
   no válidos en más del 99 %. Sugerencia: "…tienen el campo de año, pero vacío o sin valores válidos
   en más del 99 % (revisado 2026-09-26)". En :15-16 conviene usar el enlace directo
   `https://www.medellin.gov.co/es/tramites-y-servicios/ficha-catastral-predio/` y avisar que pide
   usuario.
3. **Documentos desactualizados** (§6): CLAUDE.md:16-18, 83-87 y 92-95; FUENTES_MUNICIPIOS.md:9,
   86-88, 176-181, 397 y la sección "Qué reverificar" (:424-431), que ya se puede cumplir para
   Medellín.
4. *Menor:* el enlace de Barranquilla (municipios/__init__.py:33-34) responde 403 a clientes
   automáticos. No se pudo confirmar que abra en un navegador.
5. *Menor, latente:* anio.py:17 acepta cualquier año distinto de 0 o nulo. Con Barranquilla
   entrarían 1512 y 2500 (límites del dominio). Conviene filtrar un rango en el adaptador.

## Criterio de aceptación

| Criterio | Resultado |
|---|---|
| Bogotá 8/8 | ✔ 8/8, confirmado además con el CSV masivo y por `PREDIRECC` |
| Cada ciudad con fuente ≥ 80 % | ✔ Bogotá 100 %, la única con adaptador (Barranquilla debería tenerlo; ver falla 1) |
| Ciudades sin fuente con el aviso correcto | ✔ 5/5 en la UI, con 0 llamadas de red |
| Conclusión "sin fuente" sostenida por verificación independiente | ✘ **Barranquilla**. ✔ Medellín (motivo inexacto), Cali, Bucaramanga y Manizales |
| 0 excepciones no controladas en la UI | ✔ 21/21 escenarios |
| Restricciones cumplidas | ✔ |

**NO APROBADO**, por la falla 1. Para aprobar hay que integrar Barranquilla con la fuente
`catastro/datosabiertos` y pasar ≥ 80 % en sus casos, o, si el usuario decide no integrarla, cambiar
su aviso por uno verdadero y aceptar ese desvío de forma explícita. En cualquiera de los dos casos
hay que corregir el motivo de Medellín y los documentos.

---

# Evaluación v1 (2026-09-25)

**Veredicto: APROBADO** — 8/8 casos correctos (100 %), 0 errores no controlados en la UI,
restricciones cumplidas. Hay 3 observaciones menores, ninguna bloqueante (ver §7).

## 1. Pruebas unitarias (`uv run pytest`)

`17 passed in 0.07s` (test_anio 4, test_normalizar 7, test_servicios 6). Todas usan fixtures sin red.

## 2. Casos de prueba de punta a punta contra los servicios reales (`uv run python evaluar.py`)

| Dirección | Esperado | Obtenido | Lote | ✔/✘ |
|---|---|---|---|---|
| Carrera 7 # 1-34 Sur | 1970 | 1970 | 001101001009 | ✔ |
| Calle 45A Bis # 19-61 | 1950 | 1950 | 007205026008 | ✔ |
| Avenida Carrera 68 # 1A-56 | 1971 | 1971 | 004304093003 | ✔ |
| Diagonal 40A Sur # 34A-62 | 1984 | 1984 | 002311021046 | ✔ |
| Calle 48 Sur # 4B-42 Este | 1984 | 1984 | 001328010005 | ✔ |
| Calle 26 # 13-19 | 1948 | 1948 | 003101009008 | ✔ |
| Calle 72 # 10-34 | 1978 | 1978 | 008306017001 | ✔ |
| Calle 127 # 7-25 | 1970 | 1970 | 008413024020 | ✔ |

**8/8 = 100 %.** Todas geocodificadas como "Asignada por Catastro" (exactas). Tiempo total ≈ 5 s.

## 3. Verificación independiente del año esperado (curl propio)

Para descartar que la "verdad" del CSV venga del mismo camino que la app, se usaron vías distintas:

| Caso | Vía independiente | Resultado |
|---|---|---|
| Carrera 7 # 1-34 Sur | Tabla Predio por `PREDIRECC='KR 7 1 34 SUR'` (sin geocodificador) | lote 001101001009, `PREVETUSTZ`=1970 ✔ |
| Calle 127 # 7-25 | Tabla Predio por `PREDIRECC LIKE 'AC 127 7 23%'` (sin geocodificador) | lote 008413024020, 1970 ✔ |
| Calle 72 # 10-34 | `outStatistics` count agrupado por `PREVETUSTZ` | {1978: 490 filas}, único año ✔ |
| Calle 48 Sur # 4B-42 Este | Consulta directa `BARMANPRE` | A=1984 (204.6 m²), B=2012 (51.6 m²) → principal 1984 ✔ |
| 4 casos (127, 72, KR 7, CL 48 S) | Punto del geocodificador → `lote/MapServer/0` (intersección espacial) | Mismo `LOTCODIGO` que `lotcodigo` ✔ |

Hallazgo lateral: el punto de Calle 127 intersecta **dos** lotes en la capa 0: el del predio
(008413024020) y 008413018099 (`LOTDISTRIT=1`, `AC 127 7 91`, `PREVETUSTZ` nulo: lote distrital/espacio
público superpuesto). Confirma que es correcto usar `lotcodigo` del geocodificador y no la consulta por
punto como vía principal.

## 4. Direcciones adicionales (no incluidas en el CSV)

| Entrada | Dirección catastral | Resultado |
|---|---|---|
| `Cl 72 10 34` | CL 72 10 34 (exacta) | 1978 ✔ |
| `Kr 7 1-34 sur` (minúsculas) | KR 7 1 34 S (exacta) | 1970 ✔ |
| `Cra 7 No. 1-34 Sur` | KR 7 1 34 S (exacta) | 1970 ✔ |
| `cra. 7 # 1 - 34 sur` | KR 7 1 34 S (exacta) | 1970 ✔ |
| `calle 45a bis # 19-61` | CL 45ABIS 19 61 (exacta) | 1950 ✔ |
| `Diagonal 40A Sur N° 34A-62` | DG 40A S 34A 62 (exacta) | 1984 ✔ |
| `Avenida Carrera 68 No 1A-56` | AK 68 1A 56 (exacta) | 1971 ✔ |
| `Cll 127 # 7-25` | AC 127 7 25 (exacta) | 1970 ✔ |
| `Calle 26 # 13-19 Of 3102` | CL 26 13 19 (exacta) | 1948 ✔ |
| `Carrera 13 Bis # 17-44` | KR 13 17 44 (**aproximada**, se come el BIS) | 1975 + aviso en UI ✔ |
| `Diagonal 40A Bis 15 20` | aproximada sin lote | "no encontrada" ✔ |
| `asdf`, `12345`, `Calle 999 # 999-99`, `'; DROP--` | — | "no encontrada", sin excepción ✔ |
| `""`, `"   "` | — | sin consulta, sin excepción ✔ |

La normalización es mínima (quitar `#`, tildes, espacios) y el geocodificador oficial tolera bien
`Cl/Kr/Cra/Cll/No./N°`, minúsculas y guiones con espacios. La inyección en `where` está bloqueada
por `lotcodigo.isdigit()` (catastro.py:12).

## 5. La app en ejecución

- `uv run streamlit run app.py --server.headless true --server.port 8599`: `GET /` → 200,
  `GET /_stcore/health` → `ok` 200. Detenida después (puerto cerrado, `000`).
- `streamlit.testing.v1.AppTest` (escribir dirección + clic en "Consultar"):

| Escenario | Lo que muestra la UI | Excepción |
|---|---|---|
| Calle 48 Sur # 4B-42 Este | métrica 1984, caption "CL 48 S 4B 42 E · Lote 001328010005", desglose 1984: 204.6 m² / 2012: 51.6 m² | no |
| Calle 72 # 10-34 (PH, 490 filas) | métrica 1978 | no |
| Carrera 13 Bis # 17-44 | warning "Dirección aproximada: se usó KR 13 17 44…", métrica 1975 | no |
| asdf | error "Dirección no encontrada." | no |
| vacía / solo espacios | nada (el botón no hace nada) | no |
| `requests.Timeout` simulado | error "Servicio no disponible…" | no |
| respuesta no JSON simulada | error "Servicio no disponible…" | no |
| latitud vacía simulada | error "Servicio no disponible…" | no |
| apikey rechazada simulada (`{"message":"API Key no valida","status":false}`) | error "Dirección no encontrada." (**engañoso**, ver §7) | no |

**0 errores no controlados.**

## 6. Restricciones

| Restricción | Estado |
|---|---|
| URLs solo gubernamentales | ✔ solo `catalogopmb.catastrobogota.gov.co` (geocodificar.py:11) y `serviciosgis.catastrobogota.gov.co` (catastro.py:4) |
| `app.py` sin lógica de consulta | ✔ solo llama `geocodificar` → `consultar_predio` → `extraer_anio`; importa `requests` únicamente para capturar la excepción |
| Solo Python / solo local | ✔ sin Docker, CI, JS, BD; `requirements.txt` = streamlit, requests, pytest |
| Timeouts | ✔ `timeout=15` en las dos llamadas `requests.get` (geocodificar.py:26, catastro.py:26); los tests lo verifican |
| Simplicidad | ✔ 131 líneas en los 4 módulos (app 37, geocodificar 38, catastro 33, anio 23) |
| Tres pasos separados y probables aislados | ✔ |
| Decisión de "qué año mostrar" documentada | ✔ docstring de anio.py y FUENTES.md (mayor área, empate → más antiguo, desglose visible) |

## 7. Observaciones (ninguna bloqueante)

1. **Clave rechazada se reporta como "Dirección no encontrada"** — geocodificar.py:28-31. Si la
   `apikey` pública rota, la respuesta es `{"message":"API Key no valida","status":false}` (sin
   `response`), y la app diría "no encontrada" para *toda* dirección, ocultando la causa real.
   Causa: servicio. Sugerencia: `if not resp.json().get("status"): raise requests.RequestException(...)`
   antes de leer `response`, para que la UI muestre "Servicio no disponible".
2. **Entrada vacía sin feedback** — app.py:12. Al pulsar "Consultar" con el campo vacío no pasa nada.
   No es error, pero un `st.warning("Escribe una dirección.")` sería más claro.
3. **`lat`/`lon` no se usan** — geocodificar.py:34-35. `float(None)` lanzaría `TypeError` (no capturado
   en app.py:17) si el servicio alguna vez devolviera `lotcodigo` sin coordenadas. Sugerencia: quitar
   esos dos campos (alcance mínimo) o capturar `TypeError` también.
4. Menores: `PREAUSO` puede ser `-1.0` en el servicio (visto en un lote sin año); anio.py:19 lo sumaría
   si apareciera en una fila con año. CLAUDE.md:7 aún dice "Repositorio vacío".

## Criterio de aceptación

| Criterio | Resultado |
|---|---|
| ≥ 80 % de casos correctos | 100 % (8/8) ✔ |
| 0 errores no controlados en la UI | 0 ✔ |
| Restricciones cumplidas | ✔ |

**APROBADO.**
