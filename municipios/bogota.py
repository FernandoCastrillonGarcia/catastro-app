"""Bogotá (Catastro Bogotá, UAECD): dirección -> lote -> construcciones, uso, estructura y pisos.

Paso 1: geocodificador de Mapas Bogotá. Paso 2: tabla Predio y capa de construcciones del
catastro. Ver FUENTES.md y FUENTES_VARIABLES.md.
"""
import functools
import re
import unicodedata

import requests

# Clave pública que el visor oficial Mapas Bogotá (mapas.bogota.gov.co) incrusta en su
# JavaScript. No es una credencial privada y puede rotar sin aviso: si deja de funcionar,
# actualizarla aquí (ver FUENTES.md).
API_KEY = "e2d6f043-7b63-417e-8fbe-db515898576f"
URL_GEOCODIFICADOR = "https://catalogopmb.catastrobogota.gov.co/PMBWeb/web/api"
URL_CATASTRO = "https://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/catastro"
URL_PREDIO = URL_CATASTRO + "/lote/MapServer/3"
URL_CONSTRUCCION = URL_CATASTRO + "/construccion/MapServer/0/query"
CAMPOS = "PRECHIP,PREDIRECC,PREVETUSTZ,PREUCALIF,PRECUSO,PREAUSO,PRECDESTIN,PREEARMAZ,PREEMUROS"
TIMEOUT = 15

# Calificación de la estructura. El servicio no publica estos dominios; vienen del catálogo
# oficial de IDECA/UAECD CO_Predio_MR.pdf, "Dominios de los atributos de Calificación".
ARMAZON = {"111": "Madera", "112": "Prefabricado", "113": "Ladrillo, bloque",
           "114": "Concreto hasta tres pisos", "115": "Concreto cuatro o más pisos"}
MUROS = {"121": "Materiales de desecho, esterilla", "122": "Bahareque, adobe, tapia",
         "123": "Madera", "124": "Concreto prefabricado", "125": "Bloque, ladrillo"}


def normalizar_direccion(texto: str) -> str:
    """Quita '#', tildes y espacios sobrantes (lo mismo que hace el visor oficial)."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return re.sub(r"\s+", " ", sin_tildes.replace("#", " ")).strip()


def _json(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    datos = resp.json()
    if "error" in datos:
        raise requests.RequestException(datos["error"])
    return datos


def geocodificar(direccion: str) -> dict | None:
    """Devuelve {lotcodigo, direccion_oficial, aproximada, lat, lon} o None si no se encuentra."""
    params = {"cmd": "geocodificar", "apikey": API_KEY, "query": normalizar_direccion(direccion)}
    resp = requests.get(URL_GEOCODIFICADOR, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    cuerpo = resp.json()
    if cuerpo.get("status") is False:  # p. ej. {"message": "API Key no valida", "status": false}
        raise requests.RequestException(cuerpo.get("message", "Error del geocodificador"))
    respuesta = cuerpo.get("response") or {}
    data = respuesta.get("data") or {}
    if not respuesta.get("success") or not data.get("lotcodigo"):
        return None
    return {
        "lotcodigo": data["lotcodigo"],
        "direccion_oficial": data.get("dirtrad"),
        "aproximada": data.get("tipo_direccion") != "Asignada por Catastro",
        "lat": float(data["latitude"]) if data.get("latitude") else None,
        "lon": float(data["longitude"]) if data.get("longitude") else None,
    }


@functools.cache
def dominios() -> dict[str, dict[str, str]]:
    """Dominios que publica la tabla Predio: {"PRECUSO": {"001": "Habitacional…"}, "PRECDESTIN": …}.
    Se piden una vez por sesión."""
    campos = _json(URL_PREDIO, {"f": "json"})["fields"]
    return {f["name"]: {str(c["code"]): c["name"] for c in f["domain"]["codedValues"]}
            for f in campos if f["name"] in ("PRECUSO", "PRECDESTIN") and f.get("domain")}


def consultar_predio(lotcodigo: str) -> list[dict]:
    """Devuelve los atributos crudos de todas las filas del lote (paginando si hace falta)."""
    if not lotcodigo.isdigit():
        raise ValueError(f"Código de lote inválido: {lotcodigo!r}")
    registros = []
    while True:
        params = {
            "where": f"BARMANPRE='{lotcodigo}'",
            "outFields": CAMPOS,
            "returnDistinctValues": "true",
            "returnGeometry": "false",
            "resultOffset": len(registros),
            # Sin orderByFields, resultOffset anula returnDistinctValues (verificado 2026-09-25).
            "orderByFields": CAMPOS,
            "f": "json",
        }
        datos = _json(URL_PREDIO + "/query", params)
        registros += [f["attributes"] for f in datos.get("features", [])]
        if not datos.get("exceededTransferLimit") or not datos.get("features"):
            return registros


def consultar_pisos(lotcodigo: str) -> int | None:
    """Máximo número de pisos entre los volúmenes de construcción del lote."""
    params = {
        "where": f"LOTECODIGO='{lotcodigo}'",
        "outStatistics": '[{"statisticType":"max","onStatisticField":"CONNPISOS",'
                         '"outStatisticFieldName":"PISOS"}]',
        "f": "json",
    }
    filas = _json(URL_CONSTRUCCION, params).get("features") or [{"attributes": {}}]
    pisos = filas[0]["attributes"].get("PISOS")
    return int(pisos) if pisos else None


def estructura(armazon: str | None, muros: str | None) -> str | None:
    """'113', '125' -> 'Armazón: ladrillo, bloque; muros: bloque, ladrillo'. Códigos fuera de la
    tabla oficial (000, nulos, basura) cuentan como sin dato."""
    partes = []
    if (armazon or "").strip() in ARMAZON:
        partes.append("armazón: " + ARMAZON[armazon.strip()].lower())
    if (muros or "").strip() in MUROS:
        partes.append("muros: " + MUROS[muros.strip()].lower())
    return "; ".join(partes).capitalize() or None


def consultar(direccion: str) -> dict | None:
    """Contrato de ciudad v2 (ARQUITECTURA.md 5): ficha del lote, o None si no se encuentra.

    Las filas repetidas ya las quita el servidor (returnDistinctValues sobre la fila completa).
    """
    ubicacion = geocodificar(direccion)
    if ubicacion is None:
        return None
    lote = ubicacion["lotcodigo"]
    registros = consultar_predio(lote)
    usos, destinos = dominios().get("PRECUSO", {}), dominios().get("PRECDESTIN", {})
    destino = next((r["PRECDESTIN"] for r in registros if r.get("PRECDESTIN")), None)
    return {
        "direccion_oficial": ubicacion["direccion_oficial"],
        "aproximada": ubicacion["aproximada"],
        "codigo": lote,
        "lat": ubicacion["lat"],
        "lon": ubicacion["lon"],
        "destino": destinos.get(destino, destino),
        "pisos": consultar_pisos(lote),
        "construcciones": [
            {"anio": r.get("PREVETUSTZ"), "area": r.get("PREAUSO"),
             "uso": usos.get(r.get("PRECUSO"), r.get("PRECUSO")),
             "estructura": estructura(r.get("PREEARMAZ"), r.get("PREEMUROS"))}
            for r in registros
        ],
    }
