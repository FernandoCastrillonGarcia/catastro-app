"""Reglas comunes: uso principal por área, tipología derivada y resumen de la ficha."""
import pytest

from resumen import por_area, resumir, tipologia


def test_por_area():
    assert por_area([("Bodega", 600), ("Casa", 100), ("Casa", 150), (None, 999), ("Oficina", None)]) \
        == [("Bodega", 600.0), ("Casa", 250.0), ("Oficina", 0.0)]
    assert por_area([("B", 10), ("A", 10)]) == [("A", 10.0), ("B", 10.0)]
    assert por_area([]) == []


@pytest.mark.parametrize("uso,pisos,esperado", [
    ("Habitacional menor o igual a 3 pisos en NPH", 5, "Casa"),
    ("Habitacional menor o igual a 3 pisos en PH", None,
     "Vivienda en propiedad horizontal (hasta 3 pisos)"),
    ("Habitacional mayor o igual a 4 pisos en PH", 1, "Edificio de apartamentos"),
    ("(Residencial) Apartamentos mas de 4 Pisos", 4, "Edificio de apartamentos"),
    ("(Residencial) Vivienda hasta 3 pisos", None, "Casa"),
    ("Oficinas y Consultorios en PH", 20, "Oficina"),
    ("Bodega Economica", 1, "Bodega"),
    ("Depositos de Almacenamiento en NPH", 1, "Bodega"),
    ("(Comercial) Oficinas - Consultorios", 3, "Oficina"),
    ("Corredor Comercial en NPH", 2, "Local comercial"),
    ("Comercial y Servicios", 12, "Local comercial"),
    ("(Residencial) Garajes en PH", 1, "Parqueadero"),
    ("Clinicas Hospitales Centro Medicos", 5, "Institucional"),
    ("Habitacional", 1, "Casa"),
    ("Residencial", 12, "Edificio de apartamentos"),
    ("Residencial", None, "Vivienda"),
    ("Lote urbanizado no construido o edificado", None, None),
    (None, 3, None),
])
def test_tipologia(uso, pisos, esperado):
    assert tipologia(uso, pisos) == esperado


def _ficha(construcciones, destino="Habitacional", pisos=2):
    return {"direccion_oficial": "X", "aproximada": False, "codigo": "1", "lat": 1.0, "lon": 2.0,
            "destino": destino, "pisos": pisos, "construcciones": construcciones}


def test_resumir_con_todo():
    r = resumir(_ficha([
        {"anio": 1971, "area": 629.26, "uso": "Bodega Economica", "estructura": "E1"},
        {"anio": 1971, "area": 133.83, "uso": "Casa X", "estructura": "E2"},
        {"anio": 2021, "area": 11.52, "uso": "Casa X", "estructura": "E2"},
    ], destino="Comercio en corredor comercial"))
    assert r["anio"] == {"anio": 1971, "detalle": [(1971, 763.09), (2021, 11.52)]}
    assert (r["uso"], r["estructura"], r["tipologia"]) == ("Bodega Economica", "E1", "Bodega")
    assert r["usos"] == [("Bodega Economica", 629.26), ("Casa X", 145.35)]
    assert (r["destino"], r["pisos"], r["lat"], r["lon"]) == (
        "Comercio en corredor comercial", 2, 1.0, 2.0)


def test_resumir_sin_uso_usa_destino():
    r = resumir(_ficha([{"anio": None, "area": 126, "uso": None, "estructura": None}], pisos=1))
    assert (r["anio"], r["estructura"], r["uso"], r["usos"], r["tipologia"]) == (
        None, None, "Habitacional", [], "Casa")
