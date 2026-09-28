"""Medellín (Catastro de Medellín): dirección -> CBML -> destinación, pisos y uso.

Paso 1: buscador de direcciones del geovisor MapGIS. Paso 2: capas 6, 19 y 18 del servicio
ConsultaOperadorCatastral_geo. Sin año ni material (FUENTES_VARIABLES.md).
"""
import functools

import requests
from requests.adapters import HTTPAdapter

URL_GEOCODIFICADOR = ("https://www.medellin.gov.co/servicios5/GEOCOD_WEB_MAPGIS9/"
                      "geocodificador/service/geocod")
URL_CATASTRO = ("https://www.medellin.gov.co/servidormapas/rest/services/ServiciosCatastro/"
                "ConsultaOperadorCatastral_geo/MapServer")
TIMEOUT = 20


class _SoloIPv4(HTTPAdapter):
    """www.medellin.gov.co publica una dirección IPv6 que no responde: cada petición esperaba
    45–120 s antes de caer a IPv4. Atar la conexión a 0.0.0.0 descarta IPv6 (verificado
    2026-09-27: 0,1–0,3 s)."""

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = ("0.0.0.0", 0)
        super().init_poolmanager(*args, **kwargs)


SESION = requests.Session()
SESION.mount("https://www.medellin.gov.co", _SoloIPv4())


def _json(url: str, params: dict):
    resp = SESION.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    datos = resp.json()
    if isinstance(datos, dict) and "error" in datos:
        raise requests.RequestException(datos["error"])
    return datos


def geocodificar(direccion: str) -> dict | None:
    """Devuelve {cbml, direccion_oficial, aproximada, lat, lon} o None si no se encuentra.
    tipo "CATASTRO" es una placa oficial; "MALLA VIAL" es un punto interpolado en la vía."""
    datos = _json(URL_GEOCODIFICADOR, {"dir": direccion, "accion": "11111111111"})
    primero = datos[0] if datos else {}
    if not primero.get("cbml") or str(primero.get("x")) == "0":
        return None
    return {
        "cbml": primero["cbml"],
        "direccion_oficial": primero.get("p9"),
        "aproximada": primero.get("tipo") != "CATASTRO",
        "lat": primero.get("p13"),
        "lon": primero.get("p12"),
    }


def _capa(numero: int, cbml: str, campos: str) -> list[dict]:
    if not cbml.isdigit():
        raise ValueError(f"CBML inválido: {cbml!r}")
    params = {"where": f"cbml='{cbml}'", "outFields": campos, "returnGeometry": "false",
              "f": "json"}
    return [f["attributes"] for f in _json(f"{URL_CATASTRO}/{numero}/query", params)["features"]]


@functools.cache
def usos() -> dict[int, str]:
    """Dominio LADM del campo `uso` de la capa 18 (102 valores). Se pide una vez por sesión."""
    campos = _json(f"{URL_CATASTRO}/18", {"f": "json"})["fields"]
    dominio = next(f["domain"] for f in campos if f["name"] == "uso")
    return {c["code"]: c["name"] for c in dominio["codedValues"]}


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5).

    Pisos: capa 19 (todas las construcciones del lote). Uso: capa 18 (LADM), que cubre solo parte
    de la ciudad; si el lote no tiene filas ahí, el uso sale del destino (capa 6).
    """
    ubicacion = geocodificar(direccion)
    if ubicacion is None:
        return None
    cbml = ubicacion["cbml"]
    predios = _capa(6, cbml, "destinacion")
    volumenes = _capa(19, cbml, "numero_pisos,area_construida")
    unidades = _capa(18, cbml, "identificador,uso,area_construida")
    dominio = usos() if unidades else {}
    pisos = max((v["numero_pisos"] or 0 for v in volumenes), default=0)
    filas = unidades or volumenes
    return {
        "direccion_oficial": ubicacion["direccion_oficial"],
        "aproximada": ubicacion["aproximada"],
        "codigo": cbml,
        "lat": ubicacion["lat"],
        "lon": ubicacion["lon"],
        "destino": next((p["destinacion"] for p in predios if p.get("destinacion")), None),
        "pisos": int(pisos) or None,
        "construcciones": [
            {"anio": None, "area": f.get("area_construida"),
             "uso": dominio.get(f.get("uso")), "estructura": None}
            for f in filas
        ],
        "notas": [] if unidades else [
            "El catastro LADM de Medellín todavía no cubre este lote: el uso es la destinación "
            "del predio."],
    }
