"""Analizador de direcciones y formatos por ciudad (puro, sin red)."""
import pytest

from direccion import (analizar, filtro_sql, formatos_barranquilla, formatos_cali,
                       formatos_igac)


def _c(numero, letra="", bis=False, letra_bis="", cuadrante=""):
    return {"numero": numero, "letra": letra, "bis": bis, "letra_bis": letra_bis,
            "cuadrante": cuadrante}


@pytest.mark.parametrize("entrada,esperado", [
    ("Calle 48 Sur # 4B-42 Este",
     {"tipo": "CALLE", "via": _c("48", cuadrante="SUR"), "cruce": _c("4", "B"), "placa": "42",
      "cuadrante": "ESTE"}),
    ("Carrera 100 # 11A-25",
     {"tipo": "CARRERA", "via": _c("100"), "cruce": _c("11", "A"), "placa": "25",
      "cuadrante": ""}),
    ("Calle 45A Bis # 19-61",
     {"tipo": "CALLE", "via": _c("45", "A", True), "cruce": _c("19"), "placa": "61",
      "cuadrante": ""}),
    ("Avenida Carrera 68 No. 1A-56",
     {"tipo": "AVENIDA CARRERA", "via": _c("68"), "cruce": _c("1", "A"), "placa": "56",
      "cuadrante": ""}),
    ("AV 2 E # 50 NORTE - 44",
     {"tipo": "AVENIDA", "via": _c("2", "E"), "cruce": _c("50", cuadrante="NORTE"),
      "placa": "44", "cuadrante": ""}),
    ("Cl 101 b 50 37 apto 101",
     {"tipo": "CALLE", "via": _c("101", "B"), "cruce": _c("50"), "placa": "37",
      "cuadrante": ""}),
    ("K 20A 63 57",
     {"tipo": "CARRERA", "via": _c("20", "A"), "cruce": _c("63"), "placa": "57",
      "cuadrante": ""}),
])
def test_analizar(entrada, esperado):
    assert analizar(entrada) == esperado


@pytest.mark.parametrize("entrada", ["", "xyz", "Calle 44", "Calle 44 # 52", "Barrio Centro 5 6"])
def test_analizar_incompleta(entrada):
    assert analizar(entrada) is None


def test_formatos_cali():
    assert formatos_cali(analizar("Carrera 100 # 11A-25")) == ["KR 100 # 11 A - 25"]
    assert formatos_cali(analizar("Calle 44 # 47C-4")) == ["CL 44 # 47 C - 4", "CL 44 # 47 C - 04"]
    assert formatos_cali(analizar("Avenida 2E # 50-44 Norte")) == ["AV 2 E # 50 NORTE - 44"]


def test_formatos_barranquilla():
    assert formatos_barranquilla(analizar("Carrera 55 # 48-26")) == ["CARRERA 55 48 26"]
    assert formatos_barranquilla(analizar("Calle 79A # 21B-325")) == [
        "CALLE 79A 21B 325", "CALLE 79A 21 B 325"]
    assert formatos_barranquilla(analizar("Carrera 8 Sur # 48-74")) == ["CARRERA 8 SUR 48 74"]


def test_formatos_igac():
    assert formatos_igac(analizar("Calle 63 # 12A-31")) == ["C 63 12A 31", "CL 63 12A 31"]
    assert formatos_igac(analizar("Carrera 21 # 63-5")) == [
        "K 21 63 5", "K 21 63 05", "KR 21 63 5", "KR 21 63 05", "CR 21 63 5", "CR 21 63 05"]


def test_filtro_sql():
    assert filtro_sql("direccion", ["C 1 2 3", "O'Neil"]) == (
        "(direccion = 'C 1 2 3' OR direccion LIKE 'C 1 2 3 %' OR "
        "direccion = 'O''Neil' OR direccion LIKE 'O''Neil %')")
