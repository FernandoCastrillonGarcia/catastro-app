# Fuentes oficiales verificadas

Verificado con peticiones reales el **2026-09-25**. Todas las fuentes son de la UAECD (Catastro
Bogotá) / IDECA. Respuestas crudas de ejemplo en `tests/fixtures/bogota/`.

## Resumen

| Paso | Servicio | Entrada | Salida útil |
|---|---|---|---|
| 1. Dirección → lote | Geocodificador de Mapas Bogotá (UAECD) | dirección en texto libre | `lotcodigo`, `latitude`, `longitude`, `dirtrad`, `tipo_direccion` |
| 1b. Coordenada → lote (plan B) | ArcGIS REST `catastro/lote/MapServer/0` | punto lon/lat | `LOTCODIGO` |
| 2+3. Lote → año | ArcGIS REST `catastro/lote/MapServer/3` (tabla **Predio**) | `BARMANPRE` = código de lote | **`PREVETUSTZ`** (año de construcción) por unidad, con `PREAUSO` (área) y `PREUCALIF` (unidad) |

**Campo del año: `PREVETUSTZ`** (alias "Vetustez", entero). En el diccionario oficial de IDECA
(`https://www.ideca.gov.co/sites/default/files/CO_Predio_MR.pdf`) su definición es
literalmente *"Año de la construcción"*. Los valores reales son años de 4 dígitos (1948, 1970,
2012…). Es `null` en lotes sin construcción (`PREACONST` = 0).

No confundir con `PREVFORMA` (vigencia de formación catastral) ni `PREVACTUAL` (vigencia de
actualización, hoy 2026): no son años de construcción.

La capa `catastro/construccion/MapServer/0` (polígonos de construcción) **no tiene campo de año**
(solo pisos, sótanos, altura, `LOTECODIGO`). No sirve para este objetivo.

---

## 1. Geocodificador (dirección → lote y coordenadas)

- **URL:** `https://catalogopmb.catastrobogota.gov.co/PMBWeb/web/api`
- **Método:** GET
- **Parámetros:**
  - `cmd=geocodificar`
  - `apikey=e2d6f043-7b63-417e-8fbe-db515898576f`
  - `query=<dirección>`
- **Inverso (no necesario para la app):** `cmd=geocodificar_inverso&LATITUD=..&LONGITUD=..`

```bash
curl -s -G "https://catalogopmb.catastrobogota.gov.co/PMBWeb/web/api" \
  --data-urlencode "cmd=geocodificar" \
  --data-urlencode "apikey=e2d6f043-7b63-417e-8fbe-db515898576f" \
  --data-urlencode "query=Calle 48 Sur # 4B-42 Este"
```

Respuesta real (`tests/fixtures/bogota/geocodificar_cl48sur_4b42este.json`):

```json
{"response":{"data":{"estado":"success","lotcodigo":"001328010005",
  "latitude":"4.541102868","longitude":"-74.094116527",
  "dirinput":"Calle 48 Sur # 4B-42 Este","dirtrad":"CL 48 S 4B 42 E","diraprox":"CL 48 S 4B 42 E",
  "tipo_direccion":"Asignada por Catastro","mancodigo":"001328010","codseccat":"001328",
  "localidad":"SAN CRISTOBAL","codloc":"04","cpocodigo":"110411", "...": "..."},
  "success":true,"message":"Geocodificación Exitosa."},"status":true}
```

Fallo (`tests/fixtures/bogota/geocodificar_fallo.json`): HTTP 200 con
`{"response":{"success":false,"message":"Geocodificación Fallo."},"status":true}`.
Sin `apikey` o con una inválida: `{"message":"API Key no valida","status":false}`.

**Campos útiles:** `response.success`, `data.lotcodigo` (12 dígitos, = `LOTCODIGO` = `BARMANPRE`),
`data.latitude`/`data.longitude` (texto; grados decimales), `data.dirtrad` (dirección normalizada),
`data.tipo_direccion`.

**Formato de dirección aceptado:** texto libre bastante tolerante. Verificado que acepta
`Carrera 7 # 1-34 Sur`, `KR 7 1 34 SUR`, `Cl 72 10 34`, `Calle 26 # 13-19`,
`Avenida Carrera 68 # 1A-56`, `Diagonal 40A Sur # 34A-62`, `Calle 45A Bis # 19-61`. El frontend
oficial solo le quita `#` y tildes antes de enviarla; no hace falta un normalizador complejo, pero
conviene hacer lo mismo (quitar `#` y diacríticos).

**Limitaciones / cuidados:**
- **`tipo_direccion`**: `"Asignada por Catastro"` = coincidencia exacta con una placa oficial.
  `"Dirección por aproximación"` = el servicio devolvió la placa más cercana que conoce
  (p. ej. `Avenida Calle 26 59 41` → `AC 26 59 00`; `KR 13 BIS 17 44` → `KR 13 17 44`, **se comió
  el BIS**). En ese caso el lote puede no ser el del inmueble: la app debe avisarlo.
- En aproximaciones `lotcodigo` puede **faltar** (p. ej. `Diagonal 40A Bis 15 20`, fixture
  `geocodificar_aproximada_sin_lote.json`) y el punto cae en la vía, por lo que tampoco hay lote
  por coordenada. Tratar como "no encontrado".
- **Sobre la `apikey`:** es la clave pública que el propio visor oficial `mapas.bogota.gov.co`
  incrusta en su JavaScript (`js/newindex_*.js`, variable `apiKeyMB`). No hay documentación
  pública del API para terceros, y la ayuda de Mapas Bogotá dice que la geocodificación
  *masiva* es solo para funcionarios del Distrito. La clave puede rotar sin aviso. Recomendación:
  dejarla en una constante/config fácil de cambiar, y si se va a usar más allá de pruebas
  personales, solicitar acceso formal a UAECD/IDECA. Hay plan B sin clave (sección 4).
- Coordenadas: el servicio no declara SR; el visor usa MAGNA-SIRGAS (EPSG:4686), que en la
  práctica coincide con WGS84 (EPSG:4326) a nivel de metros. Se verificó que el punto devuelto
  cae dentro del lote correcto al consultarlo con `inSR=4326`.

---

## 2. Lote por coordenada (plan B / verificación)

- **URL:** `https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/catastro/lote/MapServer/0/query`
- **SR de la capa:** wkid 4326. `maxRecordCount` 2000.
- Campos: `LOTCODIGO` (12 car.), `MANZCODIGO`, `LOTUPREDIA`, …

```bash
curl -s -G ".../catastro/lote/MapServer/0/query" \
  --data-urlencode "geometry=-74.094116527,4.541102868" \
  --data-urlencode "geometryType=esriGeometryPoint" --data-urlencode "inSR=4326" \
  --data-urlencode "spatialRel=esriSpatialRelIntersects" \
  --data-urlencode "outFields=LOTCODIGO,MANZCODIGO" --data-urlencode "returnGeometry=false" \
  --data-urlencode "f=json"
# -> "features":[{"attributes":{"LOTCODIGO":"001328010005","MANZCODIGO":"001328010"}}]
```

Fixture: `tests/fixtures/bogota/lote_por_punto_001328010005.json`. Con `lotcodigo` del geocodificador
este paso no es necesario.

---

## 3. Tabla Predio (lote → año de construcción)

- **URL:** `https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/catastro/lote/MapServer/3/query`
  (tabla "Predio" del servicio `catastro/lote`; es el recurso "Servicio REST" del dataset
  *Predios. Bogotá D.C* de datosabiertos.bogota.gov.co, publicado por la UAECD).
- Sin geometría (tabla). `maxRecordCount` 2000; soporta paginación (`resultOffset`),
  `returnDistinctValues`, `outStatistics`, `orderByFields`.

```bash
curl -s -G "https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/catastro/lote/MapServer/3/query" \
  --data-urlencode "where=BARMANPRE='001328010005'" \
  --data-urlencode "outFields=PRECHIP,PREDIRECC,PREVETUSTZ,PREUCALIF,PRECUSO,PREAUSO,PREACONST,PRECCONS,PRECRESTO,PRETPROP,BARMANPRE" \
  --data-urlencode "returnDistinctValues=true" \
  --data-urlencode "returnGeometry=false" --data-urlencode "f=json"
```

Respuesta real recortada (`tests/fixtures/bogota/predio_lote_001328010005.json`):

```json
"features":[
 {"attributes":{"PRECHIP":"AAA0005XNFZ","PREDIRECC":"CL 48 SUR 4B 42 ESTE","PREVETUSTZ":2012,
   "PREUCALIF":"B","PRECUSO":"001","PREAUSO":51.6,"PREACONST":256.2,"BARMANPRE":"001328010005", "...":"..."}},
 {"attributes":{"PRECHIP":"AAA0005XNFZ","PREDIRECC":"CL 48 SUR 4B 42 ESTE","PREVETUSTZ":1984,
   "PREUCALIF":"A","PRECUSO":"001","PREAUSO":204.6,"PREACONST":256.2,"BARMANPRE":"001328010005", "...":"..."}}
]
```

**Estructura de la tabla (clave para interpretar):** hay **una fila por predio × unidad de
construcción calificada × uso**, no una por predio.

| Campo | Alias oficial | Uso en la app |
|---|---|---|
| `BARMANPRE` | (código de lote, 12 car.) | = `LOTCODIGO` = `lotcodigo` del geocodificador. Clave de consulta |
| `PRECHIP` | Código CHIP | identificador del predio (en PH, uno por apartamento/garaje/local) |
| `PREDIRECC` | Dirección Oficial | p. ej. `KR 7 1 34 SUR`, `CL 26 13 19 OF 3102` |
| `PREVETUSTZ` | Vetustez = *Año de la construcción* | **el dato buscado** |
| `PREUCALIF` | Unidad Calificada: "letra con la que se identifica cada una de las unidades de construcción dentro del predio" | A, B, C… |
| `PREAUSO` | Área Uso (m² de construcción con ese uso) | peso para elegir el año principal |
| `PREACONST` | Área Construcción del predio | = suma de `PREAUSO` (verificado: 204.6+51.6 = 256.2) |
| `PRECUSO` | Código Uso | 001 residencial, 049/022 garajes/depósitos, etc. |
| `PRETPROP`, `PREUSOPH` | tipo de predio, uso PH | informativos |

**Limitaciones verificadas:**
- **Filas duplicadas exactas**: sin `returnDistinctValues=true` el servicio repite filas
  (p. ej. `CL 45A BIS 19 61` devuelve 3 filas idénticas; `AK 68 1A 56` devuelve 36 filas que son
  6 distintas). Usar siempre `returnDistinctValues=true` e incluir `PREUCALIF`, `PRECUSO` y
  `PREAUSO` en `outFields` para no fusionar unidades reales. Si no, sumar áreas da resultados
  inflados.
- **Propiedad horizontal**: un lote puede tener cientos de CHIPs (Calle 72 # 10-34: 489). Si una
  consulta devuelve `exceededTransferLimit: true`, paginar con `resultOffset`/`resultRecordCount`
  (o usar `outStatistics` con `groupByFieldsForStatistics=PREVETUSTZ`, recordando que cuenta
  duplicados).
- **`resultOffset` anula `returnDistinctValues`** salvo que se añada `orderByFields`
  (verificado 2026-09-25: `AK 68 1A 56` con `resultOffset=0` → 36 filas; con
  `resultOffset=0&orderByFields=<todos los outFields>` → 6 filas, y la paginación con
  `resultRecordCount` sigue siendo distinta y estable). `municipios/bogota.py` (`consultar_predio`) envía siempre ambos.
- `PREDIRECC` tiene rarezas de formato (doble espacio tras `BIS`: `CL 45A BIS  19 61`; usa `SUR`
  / `ESTE` completos, mientras el geocodificador devuelve `S` / `E`). Por eso se consulta por
  `BARMANPRE`, no por dirección.
- Un lote puede tener direcciones de varias fachadas (Calle 72 # 10-34 tiene unidades con
  `KR 10 72 57 …`), y la placa digitada puede no ser la "oficial" del predio
  (`Calle 127 # 7-25` → predio `AC 127 7 23`). Otra razón para ir por lote.
- `PREVETUSTZ` es `null` en lotes sin construcción.
- Datos actualizados mensualmente por la UAECD (el dataset abierto va por la versión 08.26).

---

## 4. Plan B sin `apikey`: búsqueda directa por dirección oficial

La misma tabla Predio permite `where=PREDIRECC='KR 7 1 34 SUR'` (verificado → lote
001101001009, 1970). Funciona **solo** si la dirección está escrita exactamente como la
nomenclatura oficial (`CL`, `KR`, `AK`, `AC`, `DG`, `TV`; `SUR`/`ESTE` completos; doble espacio
tras `BIS`; sin `#` ni guion). `PREDIRECC LIKE 'CL 72 10 34%'` sirve para PH (añade `OF`, `AP`,
`GS`, `LC`…). Es más frágil que el geocodificador; útil como respaldo si la clave deja de
funcionar. También existe la capa `catastro/placadomiciliaria/MapServer/0` (campos `PDONVIAL`
= vía, p. ej. `'KR 7 '`, `PDOTEXTO` = placa, p. ej. `'0 90 S'`, `PDOCLOTE` = lote), con la misma
fragilidad de formato.

---

## Contraste con otra fuente oficial

CSV completo de predios de Datos Abiertos Bogotá (UAECD), versión 08.26:
`https://datosabiertos.bogota.gov.co/dataset/e812efbe-acc3-4e70-9bfc-30fd2134afdd/resource/300378cb-bb87-4096-b3eb-2aadc1a79767/download/tpredio.csv.08.26.zip`
(169 MB zip, 1.38 GB CSV, mismas columnas). Para los 8 casos de `casos_prueba.csv` los valores de
`PREVETUSTZ`, `PREUCALIF` y `PREAUSO` coinciden exactamente con el servicio REST. No sirve para
la app en línea (demasiado grande) y el `datastore_search` CKAN de esos recursos devuelve 0
registros (no está poblado).

## Descartado

- Carpeta `Utilities` de serviciosgis (posible GeocodeServer): exige token (`499 Token Required`).
- `catastro/construccion`: sin campo de año.
- Datastore CKAN de datosabiertos.bogota.gov.co: vacío.
- El visor oficial también usa Nominatim/OSM y el geocodificador mundial de ArcGIS como apoyo:
  **no usarlos** (no son fuentes gubernamentales).

---

## Camino recomendado (verificado de punta a punta)

1. Limpiar la entrada: quitar `#` y tildes, recortar espacios.
2. `GET catalogopmb.../PMBWeb/web/api?cmd=geocodificar&apikey=…&query=<dirección>`.
   - `response.success == false` → "Dirección no encontrada".
   - Sin `lotcodigo` → "No se pudo ubicar un predio para esa dirección".
   - `tipo_direccion == "Dirección por aproximación"` → continuar, pero mostrar aviso con
     `dirtrad` ("se usó la dirección aproximada X").
3. `GET serviciosgis.../catastro/lote/MapServer/3/query` con `where=BARMANPRE='<lotcodigo>'`,
   `returnDistinctValues=true`, `outFields=PRECHIP,PREDIRECC,PREVETUSTZ,PREUCALIF,PRECUSO,PREAUSO`,
   paginando si `exceededTransferLimit`.
4. Descartar filas con `PREVETUSTZ` nulo. Si no queda ninguna → "El predio no tiene
   construcciones registradas".
5. Agrupar por `PREVETUSTZ` sumando `PREAUSO`.

Ejemplo real: `Calle 48 Sur # 4B-42 Este` → lote `001328010005` → {1984: 204.6 m², 2012: 51.6 m²}
→ **1984** (y "también hay 51.6 m² construidos en 2012").

## Qué año mostrar cuando hay varias construcciones

Recomendación: **año principal = el `PREVETUSTZ` con mayor área construida (suma de `PREAUSO`)
en todo el lote**, y debajo el desglose de todos los años con su área. En caso de empate de
área, el año más antiguo. Motivos:
- `PREAUSO` existe y suma exactamente `PREACONST`, así que el peso por área es fiel.
- Las ampliaciones pequeñas posteriores (Avenida Carrera 68 # 1A-56: 11.5 m² de 2021 frente a
  1000.9 m² de 1971) no deben desplazar el año del edificio.
- En PH todas las unidades del edificio suelen compartir el mismo año (verificado en los dos casos
  PH), así que agregar a nivel lote da el año del edificio sin pedir al usuario el apartamento.
