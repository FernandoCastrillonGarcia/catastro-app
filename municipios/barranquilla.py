"""Barranquilla (Gerencia de Gestión Catastral): dirección -> NPN -> destino y pisos.

Capas de la Alcaldía en ArcGIS Online. El servicio `catastro/datosabiertos` (con año y uso LADM)
está detrás de Cloudflare y respondió 403 el 2026-09-27; no se usa (FUENTES_VARIABLES.md).
"""
import requests

from direccion import analizar, filtro_sql, formatos_barranquilla
from resumen import DESTINOS_IGAC

URL_BASE = "https://services3.arcgis.com/oGYAc07w6wsvgUYr/arcgis/rest/services"
URL_DIRECCION = URL_BASE + "/Direccion/FeatureServer/0/query"
URL_PREDIO = URL_BASE + "/Mapa_Distrito_de_Barranquilla_WFL1/FeatureServer/1/query"
URL_UNIDAD = URL_BASE + "/Mapa_Distrito_de_Barranquilla_WFL1/FeatureServer/3/query"
TIMEOUT = 20


def _consulta(url: str, where: str, campos: str, geometria: bool = False) -> list[dict]:
    params = {"where": where, "outFields": campos, "returnGeometry": str(geometria).lower(),
              "f": "json"}
    if geometria:
        params["outSR"] = "4326"
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    datos = resp.json()
    if "error" in datos:
        raise requests.RequestException(datos["error"])
    return datos["features"]


def buscar(direccion: str) -> list[dict]:
    """Puntos de la capa Dirección (con `Codigo_1` = NPN) para la dirección, con o sin complemento."""
    partes = analizar(direccion)
    if partes is None:
        return []
    where = filtro_sql("UPPER(Direccion)", formatos_barranquilla(partes))
    return _consulta(URL_DIRECCION, where, "Direccion,Codigo_1", geometria=True)


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5).

    Se agrega por terreno: predios y unidades cuyo NPN empieza con los 21 dígitos del terreno
    (depto, municipio, zona, sector, comuna, barrio, manzana, terreno), así un PH sale completo.
    """
    puntos = [p for p in buscar(direccion) if (p["attributes"].get("Codigo_1") or "").isdigit()]
    if not puntos:
        return None
    puntos.sort(key=lambda p: len(p["attributes"]["Direccion"]))
    principal = puntos[0]
    terreno = principal["attributes"]["Codigo_1"][:21]
    predios = _consulta(URL_PREDIO, f"CODIGO LIKE '{terreno}%'", "CODIGO,DESTINO_g")
    unidades = _consulta(URL_UNIDAD, f"Name LIKE '{terreno}%'",
                         "OBJECTID,Name,Identificador,Numero_Pisos,Area_Construccion")
    destino = next((p["attributes"]["DESTINO_g"] for p in predios
                    if p["attributes"].get("DESTINO_g")), None)
    pisos = max((u["attributes"]["Numero_Pisos"] or 0 for u in unidades), default=0)
    npns = {p["attributes"]["Codigo_1"] for p in puntos}
    return {
        "direccion_oficial": principal["attributes"]["Direccion"],
        "aproximada": False,
        "codigo": principal["attributes"]["Codigo_1"] if len(npns) == 1
        else f"{terreno}… ({len(npns)} predios)",
        "lat": (principal.get("geometry") or {}).get("y"),
        "lon": (principal.get("geometry") or {}).get("x"),
        "destino": DESTINOS_IGAC.get(destino, destino),
        "pisos": pisos or None,
        "construcciones": [
            {"anio": None, "area": u["attributes"]["Area_Construccion"], "uso": None,
             "estructura": None}
            for u in unidades
        ],
    }
