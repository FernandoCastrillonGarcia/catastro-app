"""Común: dirección colombiana en texto libre -> componentes -> formatos de cada catastro.

Bogotá y Medellín tienen geocodificador de texto libre y no usan este módulo. Cali, Barranquilla,
Bucaramanga y Manizales buscan la dirección por igualdad de texto, cada una con su propio formato
(FUENTES_VARIABLES.md), así que aquí se desarma la dirección y cada ciudad la vuelve a armar.
Todo es puro (sin red).
"""
import re
import unicodedata

# Nombre canónico -> formas que puede escribir el usuario (la primera palabra, o las dos primeras).
TIPOS_VIA = {
    "AVENIDA CALLE": ("AVENIDA CALLE", "AC"),
    "AVENIDA CARRERA": ("AVENIDA CARRERA", "AK"),
    "CALLE": ("CALLE", "CL", "CLL", "C"),
    "CARRERA": ("CARRERA", "KR", "KRA", "CRA", "CR", "K"),
    "DIAGONAL": ("DIAGONAL", "DG", "DIAG", "D"),
    "TRANSVERSAL": ("TRANSVERSAL", "TV", "TRANSV", "TR", "T"),
    "AVENIDA": ("AVENIDA", "AV", "A"),
    "CIRCULAR": ("CIRCULAR", "CQ", "CIR"),
    "VIA": ("VIA",),
}
CUADRANTES = ("SUR", "ESTE", "NORTE", "OESTE")
_NUMERO = re.compile(r"^(\d+)([A-Z]?)(BIS)?([A-Z]?)$")  # 45, 45A, 45ABIS, 45BISB


def _limpiar(texto: str) -> list[str]:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFKD", texto.upper()) if not unicodedata.combining(c)
    )
    sin_signos = re.sub(r"[#\-,.°º]", " ", sin_tildes)
    return re.sub(r"\bN[OR]?\b(?=\s*\d)|\bNUMERO\b", " ", sin_signos).split()


def _tipo(tokens: list[str]) -> tuple[str, int] | None:
    for canonico, formas in TIPOS_VIA.items():
        for forma in formas:
            partes = forma.split()
            if tokens[:len(partes)] == partes:
                return canonico, len(partes)
    return None


def _componente(tokens: list[str], i: int) -> tuple[dict, int] | None:
    """Lee 'número [letra] [BIS [letra]] [cuadrante]' desde tokens[i]."""
    if i >= len(tokens):
        return None
    m = _NUMERO.match(tokens[i])
    if not m:
        return None
    numero, letra, bis, letra_bis = m.groups()
    i += 1
    if not letra and not bis and i < len(tokens) and re.fullmatch(r"[A-Z]", tokens[i]):
        letra, i = tokens[i], i + 1
    if not bis and i < len(tokens) and tokens[i] == "BIS":
        bis, i = "BIS", i + 1
        if i < len(tokens) and re.fullmatch(r"[A-Z]", tokens[i]):
            letra_bis, i = tokens[i], i + 1
    cuadrante = ""
    if i < len(tokens) and tokens[i] in CUADRANTES:
        cuadrante, i = tokens[i], i + 1
    return {"numero": numero, "letra": letra, "bis": bool(bis), "letra_bis": letra_bis,
            "cuadrante": cuadrante}, i


def analizar(texto: str) -> dict | None:
    """'Calle 48 Sur # 4B-42 Este' -> {"tipo": "CALLE", "via": {...}, "cruce": {...},
    "placa": "42", "cuadrante": "ESTE"}. None si no tiene la forma 'vía número placa'.
    El complemento (apartamento, local…) se ignora: la búsqueda reúne todo el edificio."""
    tokens = _limpiar(texto)
    tipo = _tipo(tokens)
    if not tipo:
        return None
    via = _componente(tokens, tipo[1])
    cruce = via and _componente(tokens, via[1])
    if not cruce or cruce[1] >= len(tokens) or not tokens[cruce[1]].isdigit():
        return None
    i = cruce[1] + 1
    cuadrante = tokens[i] if i < len(tokens) and tokens[i] in CUADRANTES else ""
    return {"tipo": tipo[0], "via": via[0], "cruce": cruce[0], "placa": tokens[cruce[1]],
            "cuadrante": cuadrante}


def _placas(placa: str) -> list[str]:
    """La placa '4' puede estar guardada como '4' o '04', y '04' como '4'."""
    return list(dict.fromkeys([placa, placa.zfill(2), placa.lstrip("0") or "0"]))


def _armar(tipos, via, cruce, placas, cuadrante, *, sep_letra, formato):
    """Todas las combinaciones de tipo de vía, forma de letra y placa, sin repetir."""
    salida = []
    for tipo in tipos:
        for sep in sep_letra:
            for placa in placas:
                salida.append(formato(tipo, via, cruce, placa, cuadrante, sep).strip())
    return list(dict.fromkeys(re.sub(r"\s+", " ", s) for s in salida))


def _num(c: dict, sep: str) -> str:
    """'45', '45A', '45 A', '45A BIS', '45 BIS B' según cómo se separe la letra."""
    texto = c["numero"] + (sep + c["letra"] if c["letra"] else "")
    if c["bis"]:
        texto += " BIS" + (" " + c["letra_bis"] if c["letra_bis"] else "")
    return texto


# Abreviaturas de cada fuente, verificadas contra los datos (FUENTES_VARIABLES.md).
_IGAC = {"CALLE": ("C", "CL"), "CARRERA": ("K", "KR", "CR"), "DIAGONAL": ("D", "DG"),
         "TRANSVERSAL": ("T", "TV"), "AVENIDA": ("AV", "A"), "CIRCULAR": ("CQ", "CIR"),
         "VIA": ("VIA",), "AVENIDA CALLE": ("AC", "C", "CL"), "AVENIDA CARRERA": ("AK", "K", "KR")}
_CALI = {"CALLE": ("CL",), "CARRERA": ("KR",), "DIAGONAL": ("DG",), "TRANSVERSAL": ("TV",),
         "AVENIDA": ("AV",), "CIRCULAR": ("CQ",), "VIA": ("VIA",),
         "AVENIDA CALLE": ("AV", "CL"), "AVENIDA CARRERA": ("AV", "KR")}
_BARRANQUILLA = {"CALLE": ("CALLE",), "CARRERA": ("CARRERA",), "DIAGONAL": ("DIAGONAL",),
                 "TRANSVERSAL": ("TRANSVERSAL",), "AVENIDA": ("AVENIDA",),
                 "CIRCULAR": ("CIRCUNVALAR", "CIRCULAR"), "VIA": ("VIA",),
                 "AVENIDA CALLE": ("AVENIDA", "CALLE"), "AVENIDA CARRERA": ("AVENIDA", "CARRERA")}


def formatos_igac(d: dict) -> list[str]:
    """Bucaramanga (R1) y Manizales (RIC): 'C 63 12A 31', 'K 15B 6 15', 'C 48 SUR 4B 42'."""
    def fmt(tipo, via, cruce, placa, cuadrante, sep):
        cv = " " + via["cuadrante"] if via["cuadrante"] else ""
        cc = " " + cruce["cuadrante"] if cruce["cuadrante"] else ""
        cp = " " + cuadrante if cuadrante else ""
        return f"{tipo} {_num(via, sep)}{cv} {_num(cruce, sep)}{cc} {placa}{cp}"
    return _armar(_IGAC[d["tipo"]], d["via"], d["cruce"], _placas(d["placa"]), d["cuadrante"],
                  sep_letra=("",), formato=fmt)


def formatos_cali(d: dict) -> list[str]:
    """'KR 100 # 11 A - 25', 'AV 2 E # 50 NORTE - 44', 'CL 44 # 47 C - 04'."""
    def fmt(tipo, via, cruce, placa, cuadrante, sep):
        cv = " " + via["cuadrante"] if via["cuadrante"] else ""
        cc = " " + (cruce["cuadrante"] or cuadrante) if (cruce["cuadrante"] or cuadrante) else ""
        return f"{tipo} {_num(via, sep)}{cv} # {_num(cruce, sep)}{cc} - {placa}"
    return _armar(_CALI[d["tipo"]], d["via"], d["cruce"], _placas(d["placa"]), d["cuadrante"],
                  sep_letra=(" ",), formato=fmt)


def formatos_barranquilla(d: dict) -> list[str]:
    """'Carrera 55 48 26', 'Calle 79A 21B 325' o 'Calle 79A 21 B 325', 'Carrera 8 SUR 48 74'.
    Se devuelven en mayúsculas: la búsqueda compara con UPPER(Direccion)."""
    def fmt(tipo, via, cruce, placa, cuadrante, sep):
        cv = " " + via["cuadrante"] if via["cuadrante"] else ""
        cc = " " + cruce["cuadrante"] if cruce["cuadrante"] else ""
        cp = " " + cuadrante if cuadrante else ""
        return f"{tipo} {_num(via, '')}{cv} {_num(cruce, sep)}{cc} {placa}{cp}"
    return _armar(_BARRANQUILLA[d["tipo"]], d["via"], d["cruce"], _placas(d["placa"]),
                  d["cuadrante"], sep_letra=("", " "), formato=fmt)


def filtro_sql(campo: str, candidatos: list[str]) -> str:
    """WHERE (SQL de ArcGIS, SoQL de datos.gov.co y CQL de GeoServer): igualdad exacta con cada
    candidato, o candidato seguido de un complemento ('... AP 101'), para reunir todo el edificio."""
    partes = []
    for c in candidatos:
        c = c.replace("'", "''")
        partes += [f"{campo} = '{c}'", f"{campo} LIKE '{c} %'"]
    return "(" + " OR ".join(partes) + ")"
