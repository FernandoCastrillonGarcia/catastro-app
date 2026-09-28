"""Paso 3 (común a todas las ciudades): construcciones del predio -> año de construcción."""


def elegir_anio(construcciones: list[tuple]) -> dict | None:
    """Calcula el año de construcción a partir de pares (año, área_m2) crudos de la ciudad.

    Un lote puede tener varias unidades de construcción con años distintos (ampliaciones,
    varios predios en propiedad horizontal). Decisión: se descartan los pares sin año (nulo o 0),
    se suma el área construida por año, y el año principal es el de mayor área;
    en empate, el más antiguo. Se devuelven también todos los años con su área.

    Retorna {"anio": int, "detalle": [(anio, area_m2), ...]} ordenado por área descendente,
    o None si ningún par tiene año.
    """
    areas: dict[int, float] = {}
    for anio, area in construcciones:
        if anio:
            areas[anio] = areas.get(anio, 0.0) + max(area or 0.0, 0.0)
    if not areas:
        return None
    detalle = sorted(((a, round(m2, 2)) for a, m2 in areas.items()), key=lambda x: (-x[1], x[0]))
    return {"anio": detalle[0][0], "detalle": detalle}
