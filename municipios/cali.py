"""Cali (Subdirección de Catastro): dirección -> terrenos (WFS IDESC) con destino, uso y pisos.

Una sola petición: la capa catastro:cat_bas_terrenos trae por fila la dirección, el NPN, el
destino, el uso principal, pisos y área de hasta dos construcciones y el polígono. Sin año ni
material (FUENTES_VARIABLES.md).
"""
import requests

from direccion import analizar, filtro_sql, formatos_cali
from resumen import DESTINOS_IGAC

URL_WFS = "https://ws-idesc.cali.gov.co/geoserver/ows"
CAMPOS = ("id,npn,direpred,condicion,destinacio,uso_princi,total_pis1,area_cons1,total_pis2,"
          "area_cons2,the_geom")
TIMEOUT = 20


def buscar(candidatos: list[str]) -> list[dict]:
    """Features GeoJSON (EPSG:4326) de los terrenos cuya dirección es un candidato, con o sin
    complemento (en PH hay una fila por unidad)."""
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": "catastro:cat_bas_terrenos", "outputFormat": "application/json",
        "srsName": "EPSG:4326", "propertyName": CAMPOS,
        "CQL_FILTER": filtro_sql("direpred", candidatos),
    }
    resp = requests.get(URL_WFS, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()["features"]


def centro(geometria: dict | None) -> tuple[float, float] | tuple[None, None]:
    """(lat, lon) = promedio de los vértices del primer anillo del polígono."""
    if not geometria:
        return None, None
    anillo = geometria["coordinates"][0][0] if geometria["type"] == "MultiPolygon" \
        else geometria["coordinates"][0]
    puntos = anillo[:-1] or anillo  # el último vértice repite el primero
    lon = sum(p[0] for p in puntos) / len(puntos)
    lat = sum(p[1] for p in puntos) / len(puntos)
    return round(lat, 7), round(lon, 7)


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5). Filas repetidas (mismo `id`) se cuentan una vez."""
    partes = analizar(direccion)
    if partes is None:
        return None
    filas = {f["properties"]["id"]: f for f in buscar(formatos_cali(partes))}
    if not filas:
        return None
    features = sorted(filas.values(), key=lambda f: f["properties"]["npn"] or "")
    props = [f["properties"] for f in features]
    npns = sorted({p["npn"] for p in props if p["npn"]}) or ["sin NPN"]
    lat, lon = centro(features[0].get("geometry"))
    destino = next((p["destinacio"] for p in props if p.get("destinacio")), None)
    construcciones = []
    for p in props:
        for n in (1, 2):
            if p.get(f"area_cons{n}"):
                construcciones.append({"anio": None, "area": p[f"area_cons{n}"],
                                       "uso": (p.get("uso_princi") or "").capitalize() or None,
                                       "estructura": None})
    pisos = max((p.get(f"total_pis{n}") or 0 for p in props for n in (1, 2)), default=0)
    return {
        "direccion_oficial": min((p["direpred"] for p in props), key=len),
        "aproximada": False,
        "codigo": npns[0] if len(npns) == 1 else f"{npns[0][:21]}… ({len(npns)} predios)",
        "lat": lat,
        "lon": lon,
        "destino": DESTINOS_IGAC.get(destino, destino),
        "pisos": pisos or None,
        "construcciones": construcciones,
    }
