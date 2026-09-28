"""Registro de municipios: datos completos y casos_prueba.csv (sin red)."""
import csv
from pathlib import Path

from municipios import MUNICIPIOS

RAIZ = Path(__file__).parent.parent
VARIABLES = {"anio", "estructura", "uso", "ciiu", "pisos", "coordenadas", "tipologia"}


def test_registro():
    assert list(MUNICIPIOS) == ["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga",
                                "Manizales"]
    for nombre, m in MUNICIPIOS.items():
        assert m["gestor"] and m["nombre_codigo"] and callable(m["consultar"]), nombre
        assert set(m["sin_dato"]) <= VARIABLES and m["sin_dato"]["ciiu"], nombre
        if nombre != "Bogotá":
            assert "https://" in m["sin_dato"]["anio"] and ".gov.co" in m["sin_dato"]["anio"]


def test_casos_prueba_tienen_municipio():
    for archivo in ("casos_prueba.csv", "casos_variables.csv"):
        with open(RAIZ / archivo, encoding="utf-8") as f:
            for fila in csv.DictReader(f):
                assert fila["municipio"] in MUNICIPIOS, (archivo, fila)
