"""Manizales (MASORA por contrato): dirección -> NPN -> destino y pisos, desde el RIC del IGAC.

El sistema de MASORA exige login, captcha y pago; el reporte nacional del IGAC (SINIC/RIC, foto
2025-06-18) es la única fuente abierta. Sin año ni material (FUENTES_VARIABLES.md).
"""
import requests

from direccion import analizar, filtro_sql, formatos_igac

URL_RIC = "https://sigi.igac.gov.co/habilitacion/rest/services/sinic/ric/FeatureServer"
TIMEOUT = 20


def _consulta(capa: int, params: dict) -> list[dict]:
    params = {"returnGeometry": "false", "f": "json", **params}
    resp = requests.get(f"{URL_RIC}/{capa}/query", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    datos = resp.json()
    if "error" in datos:
        raise requests.RequestException(datos["error"])
    return datos["features"]


def buscar(direccion: str) -> list[dict]:
    """Terrenos del RIC con esa dirección (con o sin complemento), con centroide en WGS84."""
    partes = analizar(direccion)
    if partes is None:
        return []
    where = "municipio='MANIZALES' AND " + filtro_sql("direccion", formatos_igac(partes))
    return _consulta(0, {"where": where, "returnCentroid": "true", "outSR": "4326",
                         "outFields": "numero_predial,direccion,destinacion_economica"})


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5). El RIC repite filas idénticas: las unidades se
    deduplican por fila completa. Las unidades se reúnen por los 21 dígitos del terreno."""
    terrenos = [t for t in buscar(direccion)
                if (t["attributes"].get("numero_predial") or "").strip().isdigit()]
    if not terrenos:
        return None
    terrenos.sort(key=lambda t: len(t["attributes"]["direccion"]))
    principal = terrenos[0]["attributes"]
    terreno = principal["numero_predial"][:21]
    campos = "numero_predial,identificador,numero_pisos,area_construccion"
    filas = _consulta(2, {"where": f"numero_predial LIKE '{terreno}%'", "outFields": campos})
    unidades = list({tuple(sorted(f["attributes"].items())): f["attributes"] for f in filas}.values())
    pisos = max((u["numero_pisos"] or 0 for u in unidades), default=0)
    npns = {t["attributes"]["numero_predial"] for t in terrenos}
    centroide = terrenos[0].get("centroid") or {}
    return {
        "direccion_oficial": principal["direccion"],
        "aproximada": False,
        "codigo": principal["numero_predial"] if len(npns) == 1
        else f"{terreno}… ({len(npns)} predios)",
        "lat": centroide.get("y"),
        "lon": centroide.get("x"),
        "destino": principal.get("destinacion_economica"),
        "pisos": pisos or None,
        "construcciones": [{"anio": None, "area": u["area_construccion"], "uso": None,
                            "estructura": None} for u in unidades],
    }
