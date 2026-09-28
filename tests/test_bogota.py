"""Bogotá sin red: normalización pura y parseo de respuestas reales (fixtures)."""
import pytest
import requests

from municipios import bogota


@pytest.mark.parametrize("entrada,esperado", [
    ("Calle 48 Sur # 4B-42 Este", "Calle 48 Sur 4B-42 Este"),
    ("  Carrera 7 #1-34   Sur ", "Carrera 7 1-34 Sur"),
    ("Diagonal 40A Sur # 34A-62", "Diagonal 40A Sur 34A-62"),
    ("Avenida Carrera 68 # 1A-56", "Avenida Carrera 68 1A-56"),
    ("Calle 45A Bis # 19-61", "Calle 45A Bis 19-61"),
    ("Tránsversal 5 Número 3", "Transversal 5 Numero 3"),
    ("KR 7 1 34 SUR", "KR 7 1 34 SUR"),
])
def test_normalizar(entrada, esperado):
    assert bogota.normalizar_direccion(entrada) == esperado


def test_geocodificar_exacta(falso_get, fixture):
    llamadas = falso_get(fixture("bogota/geocodificar_cl48sur_4b42este.json"))
    r = bogota.geocodificar("Calle 48 Sur # 4B-42 Este")
    assert llamadas[0][1]["query"] == "Calle 48 Sur 4B-42 Este"
    assert r == {"lotcodigo": "001328010005", "direccion_oficial": "CL 48 S 4B 42 E",
                 "aproximada": False, "lat": 4.541102868, "lon": -74.094116527}


def test_geocodificar_api_key_invalida(falso_get):
    falso_get({"message": "API Key no valida", "status": False})
    with pytest.raises(requests.RequestException):
        bogota.geocodificar("Calle 72 # 10-34")


def test_geocodificar_fallo(falso_get, fixture):
    falso_get(fixture("bogota/geocodificar_fallo.json"))
    assert bogota.geocodificar("xyz") is None


def test_geocodificar_aproximada_sin_lote(falso_get, fixture):
    falso_get(fixture("bogota/geocodificar_aproximada_sin_lote.json"))
    assert bogota.geocodificar("Diagonal 40A Bis 15 20") is None


def test_geocodificar_aproximada_con_lote(falso_get, fixture):
    data = fixture("bogota/geocodificar_cl48sur_4b42este.json")
    data["response"]["data"]["tipo_direccion"] = "Dirección por aproximación"
    falso_get(data)
    assert bogota.geocodificar("Calle 48 Sur 4B 42 Este")["aproximada"] is True


def test_consultar_predio(falso_get, fixture):
    llamadas = falso_get(fixture("bogota/predio_lote_001328010005.json"))
    regs = bogota.consultar_predio("001328010005")
    assert [r["PREVETUSTZ"] for r in regs] == [2012, 1984]
    params = llamadas[0][1]
    assert params["where"] == "BARMANPRE='001328010005'"
    assert params["returnDistinctValues"] == "true"
    assert params["orderByFields"]  # necesario para que distinct funcione con resultOffset


def test_consultar_predio_pagina(falso_get, fixture):
    pagina1 = fixture("bogota/predio_lote_004304093003.json")
    pagina1["exceededTransferLimit"] = True
    llamadas = falso_get(pagina1, fixture("bogota/predio_lote_001328010005.json"))
    regs = bogota.consultar_predio("004304093003")
    assert len(regs) == 8
    assert [p["resultOffset"] for _, p in llamadas] == [0, 6]


def test_consultar_pisos(falso_get, fixture):
    llamadas = falso_get(fixture("bogota/construccion_pisos_001328010005.json"))
    assert bogota.consultar_pisos("001328010005") == 3
    assert llamadas[0][1]["where"] == "LOTECODIGO='001328010005'"


def test_consultar_pisos_sin_construccion(falso_get):
    falso_get({"features": [{"attributes": {"PISOS": None}}]})
    assert bogota.consultar_pisos("001328010005") is None


@pytest.mark.parametrize("armazon,muros,esperado", [
    ("113", "125", "Armazón: ladrillo, bloque; muros: bloque, ladrillo"),
    ("115", None, "Armazón: concreto cuatro o más pisos"),
    ("000", "122", "Muros: bahareque, adobe, tapia"),
    ("22 ", "000", None),
    (None, None, None),
])
def test_estructura(armazon, muros, esperado):
    assert bogota.estructura(armazon, muros) == esperado


def _consultar(falso_get, fixture, lote):
    return falso_get(fixture("bogota/geocodificar_cl48sur_4b42este.json"),
                     fixture(f"bogota/predio_variables_{lote}.json"),
                     fixture("bogota/predio_dominios.json"),
                     fixture(f"bogota/construccion_pisos_{lote}.json"))


def test_consultar_exacta(falso_get, fixture):
    _consultar(falso_get, fixture, "001328010005")
    ficha = bogota.consultar("Calle 48 Sur # 4B-42 Este")
    uso = "Habitacional menor o igual a 3 pisos en NPH"
    estructura = "Armazón: ladrillo, bloque; muros: bloque, ladrillo"
    assert ficha == {
        "direccion_oficial": "CL 48 S 4B 42 E", "aproximada": False, "codigo": "001328010005",
        "lat": 4.541102868, "lon": -74.094116527, "destino": "Residencial", "pisos": 3,
        "construcciones": [
            {"anio": 1984, "area": 204.6, "uso": uso, "estructura": estructura},
            {"anio": 2012, "area": 51.6, "uso": uso, "estructura": estructura},
        ]}


def test_consultar_varios_usos(falso_get, fixture):
    _consultar(falso_get, fixture, "004304093003")
    ficha = bogota.consultar("Avenida Carrera 68 # 1A-56")
    assert ficha["destino"] == "Comercio en corredor comercial"
    assert {c["uso"] for c in ficha["construcciones"]} == {
        "Habitacional menor o igual a 3 pisos en NPH", "Corredor Comercial en NPH",
        "Bodega Economica", "Oficinas y Consultorios en NPH",
        "Depositos de Almacenamiento en NPH"}


def test_consultar_no_encontrada(falso_get, fixture):
    falso_get(fixture("bogota/geocodificar_fallo.json"))
    assert bogota.consultar("xyz") is None


def test_consultar_api_key_invalida(falso_get):
    falso_get({"message": "API Key no valida", "status": False})
    with pytest.raises(requests.RequestException):
        bogota.consultar("Calle 72 # 10-34")
