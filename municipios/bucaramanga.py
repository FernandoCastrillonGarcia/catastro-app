"""Bucaramanga (AMB): dirección -> número predial (R1) -> destino, pisos (R2) y terreno (AMB).

R1 y R2 son los registros catastrales que el AMB publica en datos.gov.co (vigencia 2021). Las
coordenadas salen del terreno en el servidor del AMB (2023), que solo se liga con R1 en predios no
PH. Sin año ni material (FUENTES_VARIABLES.md).
"""
import requests

from direccion import analizar, filtro_sql, formatos_igac
from resumen import DESTINOS_IGAC

URL_R1 = "https://www.datos.gov.co/resource/3qja-8idc.json"
URL_R2 = "https://www.datos.gov.co/resource/mjv3-q3v6.json"
URL_TERRENO = ("https://mapa.amb.gov.co/server/rest/services/Unidad_terreno_BGA/MapServer/1/"
               "query")
TIMEOUT = 20


def _get(url: str, params: dict):
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    datos = resp.json()
    if isinstance(datos, dict) and ("error" in datos or "errorCode" in datos):
        raise requests.RequestException(datos.get("error") or datos.get("message"))
    return datos


def buscar(direccion: str) -> list[dict]:
    """Filas de R1 con esa dirección, con o sin complemento ('OFC 202', 'BR CHAPINERO')."""
    partes = analizar(direccion)
    if partes is None:
        return []
    return _get(URL_R1, {"$where": filtro_sql("direccion", formatos_igac(partes)),
                         "$limit": 2000})


def consultar_r2(numeros: list[str]) -> list[dict]:
    lista = ",".join(f"'{n}'" for n in numeros if n.isdigit())
    return _get(URL_R2, {"$where": f"numero_del_predio in({lista})", "$limit": 5000})


def coordenadas(numero: str) -> tuple[float, float] | tuple[None, None]:
    """(lat, lon) del terreno AMB cuyo local_id es 68001 + número de R1 (solo predios no PH,
    condición 000). Promedio de los vértices del primer anillo."""
    if not (numero.isdigit() and numero.endswith("000")):
        return None, None
    params = {"where": f"local_id='68001{numero}'", "outFields": "local_id",
              "returnGeometry": "true", "outSR": "4326", "f": "json"}
    features = _get(URL_TERRENO, params).get("features") or []
    if not features:
        return None, None
    anillo = features[0]["geometry"]["rings"][0]
    puntos = anillo[:-1] or anillo
    return (round(sum(p[1] for p in puntos) / len(puntos), 7),
            round(sum(p[0] for p in puntos) / len(puntos), 7))


def _numero(valor) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5). R2 trae hasta tres construcciones por fila
    (`pisos_1..3`, `area_construida_1..3`); las filas repetidas se cuentan una vez."""
    filas = [f for f in buscar(direccion) if (f.get("numero_del_predio") or "").isdigit()]
    if not filas:
        return None
    filas.sort(key=lambda f: (len(f.get("direccion") or ""), f["numero_del_predio"]))
    principal = filas[0]
    numeros = sorted({f["numero_del_predio"] for f in filas})
    r2 = list({tuple(sorted(f.items())): f for f in consultar_r2(numeros)}.values())
    construcciones = [{"anio": None, "area": _numero(f.get(f"area_construida_{n}")), "uso": None,
                       "estructura": None}
                      for f in r2 for n in (1, 2, 3) if _numero(f.get(f"area_construida_{n}"))]
    pisos = max((_numero(f.get(f"pisos_{n}")) for f in r2 for n in (1, 2, 3)), default=0)
    no_ph = next((n for n in numeros if n.endswith("000")), None)
    lat, lon = coordenadas(no_ph) if no_ph else (None, None)
    notas = []
    if no_ph is None:  # En PH, R2 da los pisos de cada unidad, no los del edificio.
        pisos = 0
        notas.append("Propiedad horizontal: los registros de 2021 dan los pisos de cada unidad, "
                     "no los del edificio, y su número predial no se liga con un terreno del "
                     "AMB. Pisos y coordenadas quedan sin dato.")
    destino = principal.get("destino_economico")
    return {
        "direccion_oficial": principal.get("direccion"),
        "aproximada": False,
        "codigo": numeros[0] if len(numeros) == 1 else f"{numeros[0]}… ({len(numeros)} predios)",
        "lat": lat,
        "lon": lon,
        "destino": DESTINOS_IGAC.get(destino, destino),
        "pisos": int(pisos) or None,
        "construcciones": construcciones,
        "notas": notas,
    }
