# Fuentes oficiales por variable (6 ciudades)

Verificado con peticiones reales el **2026-09-27** (scripts Python cortos con `requests`, IP
residencial colombiana). Complementa `FUENTES.md` (Bogotá, año) y `FUENTES_MUNICIPIOS.md` (año en
las otras 5). Respuestas crudas en `tests/fixtures/<ciudad>/`.

## Matriz resumen

| Variable | Bogotá | Medellín | Cali | Barranquilla | Bucaramanga | Manizales |
|---|---|---|---|---|---|---|
| 1. Año de construcción | ✔ `PREVETUSTZ` | ✘ vacío (>99,9 %) | ✘ no existe | ✘ nulo en ArcGIS Online; `datosabiertos` bloqueado por Cloudflare | ✘ vacío | ✘ nulo (RIC) |
| 2. Material (estructura) | ✔ `PREEARMAZ` + `PREEMUROS` | ✘ | ✘ | ✘ | ✘ | ✘ |
| 3. Uso | ✔ `PRECUSO` (dominio) | ✔ capa 18 `uso` (dominio LADM, cobertura parcial) + capa 6 `destinacion` | ✔ `uso_princi` + `destinacio` | ✔ `DESTINO_g` (dominio) | ✔ R1 `destino_economico` (2021) | ✔ RIC `destinacion_economica` |
| 3b. CIIU | ✘ | ✘ | ✘ | ✘ | ✘ | ✘ |
| 4. Pisos | ✔ `CONNPISOS` (capa construcción) | ✔ capa 19 `numero_pisos` | ✔ `total_pis1`/`total_pis2` | ✔ `Numero_Pisos` | ✔ R2 `pisos_1..3` (2021) | ✔ RIC `numero_pisos` |
| 5. Coordenadas | ✔ geocodificador | ✔ geocodificador (`p13`, `p12`) | ✔ polígono del terreno (WFS, EPSG:4326) | ✔ punto de la dirección (`outSR=4326`) | ✔ polígono del terreno AMB (solo NPH) | ✔ centroide RIC (`returnCentroid`, `outSR=4326`) |
| 6. Tipología | del uso | del uso | del uso + pisos | del destino + pisos | del destino + pisos | del destino + pisos |

✔ = dato oficial publicado. ✘ = no hay fuente oficial pública con el dato (o el campo está vacío).
"Tipología" no es un campo de ninguna fuente: se **deriva** del uso oficial con reglas fijas
(`resumen.py`, sección "Tipología" abajo) y la app lo dice.

## CIIU: sin fuente oficial pública por dirección (las 6 ciudades)

Ningún catastro guarda CIIU; el catastro clasifica por *uso* y *destino económico*. Se buscó una
fuente oficial que ligue una dirección o un predio con una actividad CIIU:

- **Bogotá:** Datos Abiertos Bogotá (CKAN, `q=ciiu`, 6 resultados). "Dinámica empresarial" (SDDE,
  `desarrolloeconomico/dinamicaempresarial/MapServer`) solo agrega empresas por **localidad**.
  "Recaudo ICA sector CIIU" (SDH) es agregado por sector. Ninguno tiene dirección.
- **Nacional:** RUES en datos.gov.co (Confecámaras, `nb3d-v3n7` establecimientos y `c82u-588k`
  personas) tiene CIIU pero **no tiene dirección**. Hay listados de cámaras de comercio con dirección,
  pero de otras ciudades o por sector (farmacias, constructoras…), y las cámaras son entidades
  privadas.
- **Medellín:** datasets de la Cámara de Comercio de Medellín en datos.gov.co agregados por comuna.
- **Cali:** datos.cali.gov.co sin CIIU (`q=ciiu` → 0); solo directorios sectoriales (gastronomía,
  alojamiento).
- **Bucaramanga:** `VISOR/Empresas_Activas_AMB_2022` es un **ráster** (mapa de calor), sin registros.
- **Barranquilla, Manizales:** nada con CIIU y dirección.

La app muestra "CIIU: sin fuente oficial pública por dirección" y el uso catastral oficial.
**No** se convierte el uso catastral a CIIU: sería inventar un código.

---

## Bogotá (UAECD)

Paso 1 sin cambios (geocodificador, `FUENTES.md`): ya trae `latitude` y `longitude`.

**Tabla Predio** `catastro/lote/MapServer/3` (misma consulta por `BARMANPRE`), campos nuevos:

| Campo | Alias | Uso |
|---|---|---|
| `PRECUSO` | Código Uso | dominio `D_UsoTUso` en el propio servicio: `001` "Habitacional menor o igual a 3 pisos en NPH", `038` "Habitacional mayor o igual a 4 pisos en PH", `045` "Oficinas y Consultorios en PH", `025` "Bodega de Almacenamiento en NPH"… (94 valores) |
| `PRECDESTIN` | Destino Económico | dominio `D_PreDestino`: `01` Residencial, `21` Comercio en corredor comercial… |
| `PREEARMAZ` | Armazón Estructura | códigos 111–115 (tabla abajo) |
| `PREEMUROS` | Muros Estructura | códigos 121–125 (tabla abajo) |

El servicio no publica dominio para `PREEARMAZ`/`PREEMUROS`. Su significado está en el catálogo
oficial de IDECA/UAECD `https://www.ideca.gov.co/sites/default/files/CO_Predio_MR.pdf`
("Dominios de los atributos de Calificación", v1.2, 2022-04-25):

| Código | Armazón (`PREEARMAZ`) | Código | Muros (`PREEMUROS`) |
|---|---|---|---|
| 111 | Madera | 121 | Materiales de desecho, Esterilla |
| 112 | Prefabricado | 122 | Bahareque, Adobe, Tapia |
| 113 | Ladrillo, Bloque | 123 | Madera |
| 114 | Concreto hasta tres pisos | 124 | Concreto prefabricado |
| 115 | Concreto cuatro o más pisos | 125 | Bloque, Ladrillo |

Distribución real (conteo de filas de la tabla Predio): armazón 115 = 1.836.375, 113 = 1.239.568,
114 = 563.987, 111 = 24.268, 112 = 23.823, `000` = 13.813, nulo = 155.492 y 103 filas con basura
(`3`, `22`, `6`…). Muros 125 = 3.124.212, 124 = 58.051, 121 = 46.672, 123 = 7.468, 122 = 4.480,
`000` = 95.483, nulo = 521.063. **Códigos fuera de la tabla = sin dato.**

**Pisos:** `catastro/construccion/MapServer/0` (`LOTECODIGO`, `CONNPISOS`, `CONNSOTANO`). Hay un
polígono por volumen; el número de pisos del inmueble = **máximo `CONNPISOS`** del lote.
Ejemplo `001328010005`: volúmenes de 2, 1 y 3 pisos → 3.

## Medellín (Catastro de Medellín)

**Red:** `www.medellin.gov.co` publica un registro AAAA (IPv6) que no responde desde esta red:
`requests` espera 45–120 s por petición antes de caer a IPv4. Con IPv4 responde en 0,1–0,3 s.
`municipios/medellin.py` fuerza IPv4 solo para ese dominio (adaptador con `source_address`).
`curl` recibe 403 (su User-Agent); `requests` recibe 200. No se falsifica el User-Agent.

Base: `https://www.medellin.gov.co/servidormapas/rest/services/ServiciosCatastro/ConsultaOperadorCatastral_geo/MapServer` (`{M}`).

1. **Geocodificador** `.../servicios5/GEOCOD_WEB_MAPGIS9/geocodificador/service/geocod`
   (`dir`, `accion=11111111111`): acepta texto libre (`Calle 44 # 52-165`, `KR 43A 1 50`).
   `tipo` `"CATASTRO"` = placa oficial; `"MALLA VIAL"` = punto interpolado sobre la vía
   (**aproximada**). No encontrada: `[{"latitud":0,"longitud":"null","x":0,"y":0}]`.
   Campos: `cbml`, `p13` latitud, `p12` longitud, `p9` dirección normalizada (`CL04405216500000`).
2. **`{M}/6` Ubicacion_Predio** por `cbml`: `destinacion` (Residencial 711.129, Complementario
   305.347, Comercial y Servicios 107.830, Lote, Equipamiento, Industrial, Otros, Vía, Sin Uso),
   `direccion` (`CL  044   052  165 00000`), `numero_predial` (NPN), `latitud`/`longitud`.
3. **`{M}/19` Construccion** por `cbml`: `numero_pisos`, `numero_sotanos`, `area_construida`,
   `tipo_construccion` (dominio: N Normal, E Edificio, BQ Bloque, TO Torre, PQ Parqueadero…).
   Cobertura completa. Pisos = máximo `numero_pisos`.
4. **`{M}/18` UConstruccion_LADM** por `cbml`: `uso` (dominio LADM de 102 valores, p. ej. `2`
   "(Residencial) Apartamentos mas de 4 Pisos", `11` "(Residencial) Vivienda hasta 3 pisos",
   `26` "(Comercial) Oficinas - Consultorios"), `area_construida`, `total_pisos`. **Cobertura
   parcial:** 236.284 unidades (p. ej. `10100030004` no tiene filas; `04100190003` tiene 4).
   `anio_construccion` **no se usa** (ver `FUENTES_MUNICIPIOS.md`: 641 valores, casi todos 2025/2024).

## Cali (Subdirección de Catastro)

Una sola petición al WFS de la IDESC (`https://ws-idesc.cali.gov.co/geoserver/ows`,
`catastro:cat_bas_terrenos`, `srsName=EPSG:4326`), filtrando `direpred`:

- `direpred`: `KR 100 # 11 A - 25`, `AV 2 E # 50 NORTE - 44`, `CL 44 # 47 C - 04 AP 201` (en PH,
  una fila por unidad con complemento). Placa con cero a la izquierda (`04`, `07`).
- `destinacio`: letra del destino económico IGAC (A 95 % en una muestra de 3.000; C, S, B, P, I, J, F, K, G).
- `uso_princi`: RESIDENCIAL, COMERCIAL, INDUSTRIAL, INSTITUCIONAL, OTROS.
- `total_pis1`, `area_cons1`, `total_pis2`, `area_cons2`: pisos y área de las construcciones 1 y 2.
  `uso_id1`/`uso_id2` son códigos sin diccionario publicado: **no se usan**.
- `condicion`: 0 NPH, 9 PH, 5 mejora, 8 condominio.
- Geometría del terreno (MultiPolygon). Coordenadas = promedio de los vértices del primer anillo.
- `agserver1/.../Catastro/MapServer/3` `TIPO_CONS` es Convencional/No convencional, **no** material.

## Barranquilla (Gerencia de Gestión Catastral)

`catastro/datosabiertos` (con año y uso LADM, `FUENTES_MUNICIPIOS.md`) respondió **403 de
Cloudflare** a la primera petición del 2026-09-27 (metadatos de la tabla 505). No se reintentó.
Se usan las capas de la Alcaldía en ArcGIS Online (`services3.arcgis.com/oGYAc07w6wsvgUYr`), sin
Cloudflare:

1. `Direccion/FeatureServer/0` (`Direccion`, `Codigo_1` = NPN, punto; `outSR=4326`).
   `Direccion`: `Carrera 55 48 26`, `Calle 79A 21B 325`, `Carrera 8 SUR 48 74`,
   `Calle 101B 50 37 AP 101` (PH: una fila por unidad + una de la matriz).
2. `Mapa_Distrito_de_Barranquilla_WFL1/FeatureServer/1` LC_Predio: `CODIGO` (NPN), `DESTINO_g`
   (dominio publicado: A-Habitacional, B-Industrial, C-Comercial, … T-Lote no urbanizable).
3. `.../FeatureServer/3` LC_Unidad_de_Construccion: `Name` (NPN), `Numero_Pisos`,
   `Area_Construccion`, `Tipo_Construccion` (Convencional/No_Convencional), `Anio_Construccion`
   (nulo).

Pasos 2 y 3 se consultan por los **primeros 21 dígitos del NPN** (terreno: depto, municipio, zona,
sector, comuna, barrio, manzana, terreno) con `LIKE '<21>%'`, para reunir todo el edificio o PH.
Ejemplo `Carrera 55 48 26` → NPN `080010101000002110002000000000`, destino A, unidades de 1 piso
(126 y 2 m²).

## Bucaramanga (AMB)

1. **R1** datos.gov.co `3qja-8idc` (vigencia 2021): `direccion` (`K 15B 6 15 BR CHAPINERO`,
   `CL 36 17 37 OFC 202`; prefijos C, K, D, CL…), `numero_del_predio` (15 dígitos: zona 2, sector 2,
   manzana 4, predio 4, condición 3), `destino_economico` (letra IGAC).
2. **R2** `mjv3-q3v6` por `numero_del_predio`: `pisos_1..3`, `area_construida_1..3`,
   `uso_1..3` (código sin diccionario publicado: **no se usa**).
3. **Terreno AMB** `https://mapa.amb.gov.co/server/rest/services/Unidad_terreno_BGA/MapServer/1`
   (u_lc_terreno, 2023): `local_id` = `68001` + los 15 dígitos de R1 (verificado en 4 de 4 predios
   NPH, p. ej. `010601090020000` → `68001010601090020000`). Con `outSR=4326` da el polígono.
   En PH (condición 9xx) el número de R1 no corresponde a un terreno del AMB: **sin coordenadas**.
- El RIC tiene dirección en solo 6.594 de 118.522 terrenos de Bucaramanga: no sirve para el paso 1.
- `VISOR/Alturas_Registradas` (2023) tiene pisos por NPN, pero solo se liga con R1 en NPH: no se usa.

## Manizales (MASORA; datos vía IGAC RIC)

`https://sigi.igac.gov.co/habilitacion/rest/services/sinic/ric/FeatureServer` (foto 2025-06-18):

1. `0` ric_terreno con `municipio='MANIZALES'` y `direccion`: `C 63 12A 31`, `K 20A 63 57`
   (prefijos C 56.871, K 72.163, VIA, A, T, D, CL, CR, AV, TV, KR…). Filas duplicadas.
   `destinacion_economica` (Habitacional…). Con `returnCentroid=true&outSR=4326` da el centroide.
2. `2` ric_caracteristicas_unidad_construccion por `numero_predial LIKE '<21>%'`: `numero_pisos`,
   `area_construccion`, `tipo_construccion` (Convencional/No_Convencional), `anio_construccion` (nulo).

## Tipología (derivada, `resumen.py`)

Ninguna fuente tiene un campo "casa / edificio / bodega / oficina". Se deriva del **uso principal**
(el de mayor área) con palabras clave del texto oficial, en este orden:

| Si el uso oficial contiene… | Tipología |
|---|---|
| apartamento, "mayor o igual a 4 pisos", "4 y más pisos", "más de 4 pisos" | Edificio de apartamentos |
| oficina, consultorio | Oficina |
| bodega, depósito, almacenamiento | Bodega |
| centro comercial | Centro comercial |
| hotel, motel, residencias, pensiones | Hotel |
| industria, taller | Industria |
| parqueadero, parqueo, garaje | Parqueadero |
| comercio, comercial, restaurante | Local comercial |
| colegio, universidad, aula, clínica, hospital, iglesia, culto, institucional, dotacional, educativo, salubridad, religioso | Institucional |
| habitacional, vivienda, residencial | Casa (hasta 3 pisos) o Edificio de apartamentos (4 o más pisos) |

La frontera de 3/4 pisos es la de las propias clasificaciones oficiales (Bogotá "Habitacional
menor o igual a 3 pisos" / "mayor o igual a 4 pisos"; LADM "Vivienda hasta 3 pisos" /
"Apartamentos 4 y más pisos"). Si el uso no dice pisos, se usa el número de pisos del inmueble.
Si no hay regla que aplique, la tipología queda sin dato.

## Destino económico (letras IGAC)

Barranquilla publica el dominio en su servicio (`DESTINO_g`): A Habitacional, B Industrial,
C Comercial, D Agropecuario, E Minero, F Cultural, G Recreacional, H Salubridad,
I Institucionales, J Educativo, K Religioso, L Agrícola, M Pecuario, N Agroindustrial, O Forestal,
P Uso Público, Q Servicios Especiales, R Lote urbanizable no urbanizado, S Lote urbanizado no
construido o edificado, T Lote no urbanizable. Se usa la misma tabla para las letras de Cali
(`destinacio`) y Bucaramanga (`destino_economico`).
