"""Común: ficha de una ciudad -> las variables que muestra la app (FUENTES_VARIABLES.md).

La ficha (contrato v2, ARQUITECTURA.md sección 5) trae una fila cruda por construcción; aquí se
decide qué se muestra, con las mismas reglas para todas las ciudades.
"""
import re
import unicodedata

from anio import elegir_anio

# Destino económico: dominio que publica Barranquilla (DESTINO_g). Cali y Bucaramanga usan las
# mismas letras del IGAC.
DESTINOS_IGAC = {
    "A": "Habitacional", "B": "Industrial", "C": "Comercial", "D": "Agropecuario",
    "E": "Minero", "F": "Cultural", "G": "Recreacional", "H": "Salubridad",
    "I": "Institucional", "J": "Educativo", "K": "Religioso", "L": "Agrícola", "M": "Pecuario",
    "N": "Agroindustrial", "O": "Forestal", "P": "Uso público", "Q": "Servicios especiales",
    "R": "Lote urbanizable no urbanizado", "S": "Lote urbanizado no construido o edificado",
    "T": "Lote no urbanizable",
}

# Tipología derivada del uso oficial, en orden: gana la primera regla que aplica.
_REGLAS = [
    (r"apartamento|mayor o igual a 4 pisos|4 y mas pisos|mas de 4 pisos", "Edificio de apartamentos"),
    (r"oficina|consultorio", "Oficina"),
    (r"bodega|deposito|almacenamiento", "Bodega"),
    (r"centro comercial", "Centro comercial"),
    (r"hotel|motel|residencias|pensiones", "Hotel"),
    (r"industria|taller", "Industria"),
    (r"parqueadero|parqueo|garaje", "Parqueadero"),
    (r"comercio|comercial|restaurante", "Local comercial"),
    (r"colegio|universidad|aula|clinica|hospital|iglesia|culto|institucional|dotacional"
     r"|educativo|salubridad|religioso|equipamiento", "Institucional"),
]
_RESIDENCIAL = r"habitacional|vivienda|residencial"
_HASTA_3 = r"menor o igual a 3 pisos|hasta 3 pisos"


def _simple(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto.lower())
                   if not unicodedata.combining(c))


def por_area(pares: list[tuple]) -> list[tuple[str, float]]:
    """(valor, área) -> [(valor, área sumada)] de mayor a menor área; empate: orden alfabético.
    Se descartan los pares sin valor. Un área nula cuenta 0."""
    areas: dict[str, float] = {}
    for valor, area in pares:
        if valor:
            areas[valor] = areas.get(valor, 0.0) + max(area or 0.0, 0.0)
    return sorted(((v, round(m2, 2)) for v, m2 in areas.items()), key=lambda x: (-x[1], x[0]))


def tipologia(uso: str | None, pisos: int | None) -> str | None:
    """'Habitacional mayor o igual a 4 pisos en PH' -> 'Edificio de apartamentos'.
    Si el uso es residencial y no dice pisos, decide el número de pisos (3/4, como las
    clasificaciones oficiales). None si ninguna regla aplica."""
    if not uso:
        return None
    texto = _simple(uso)
    for patron, nombre in _REGLAS:
        if re.search(patron, texto):
            return nombre
    if not re.search(_RESIDENCIAL, texto):
        return None
    hasta_3 = bool(re.search(_HASTA_3, texto)) or (pisos is not None and 0 < pisos <= 3)
    if hasta_3:
        return "Vivienda en propiedad horizontal (hasta 3 pisos)" if re.search(r"\bph\b", texto) else "Casa"
    if pisos and pisos >= 4:
        return "Edificio de apartamentos"
    return "Vivienda"


def resumir(ficha: dict) -> dict:
    """Ficha v2 -> {"anio": {...} | None, "estructura", "uso", "usos", "destino", "pisos",
    "tipologia", "lat", "lon"}. "uso" es el de mayor área; si la fuente no da uso por
    construcción, se usa el destino económico del predio."""
    construcciones = ficha["construcciones"]
    usos = por_area([(c["uso"], c["area"]) for c in construcciones])
    estructuras = por_area([(c["estructura"], c["area"]) for c in construcciones])
    uso = usos[0][0] if usos else ficha["destino"]
    return {
        "anio": elegir_anio([(c["anio"], c["area"]) for c in construcciones]),
        "estructura": estructuras[0][0] if estructuras else None,
        "uso": uso,
        "usos": usos,
        "destino": ficha["destino"],
        "pisos": ficha["pisos"],
        "tipologia": tipologia(uso, ficha["pisos"]),
        "lat": ficha["lat"],
        "lon": ficha["lon"],
    }
