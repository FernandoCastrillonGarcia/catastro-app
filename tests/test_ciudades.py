"""Medellín, Cali, Barranquilla, Bucaramanga y Manizales sin red, con respuestas reales (fixtures)."""
import pytest
import requests

from municipios import barranquilla, bucaramanga, cali, manizales, medellin


def _sin(ficha, *claves):
    return {k: v for k, v in ficha.items() if k not in claves}


# --- Medellín ---

def test_medellin_con_ladm(falso_get, fixture):
    llamadas = falso_get(fixture("medellin/geocod_calle_80_47_14.json"),
                         fixture("medellin/capa6_04100190003.json"),
                         fixture("medellin/capa19_04100190003.json"),
                         fixture("medellin/capa18_04100190003.json"),
                         fixture("medellin/capa18_dominio_uso.json"))
    ficha = medellin.consultar("Calle 80 # 47-14")
    assert _sin(ficha, "construcciones") == {
        "direccion_oficial": "CL08004701400000", "aproximada": False, "codigo": "04100190003",
        "lat": 6.27321196, "lon": -75.55610903, "destino": "Residencial", "pisos": 4, "notas": []}
    assert {c["uso"] for c in ficha["construcciones"]} == {"(Residencial) Apartamentos mas de 4 Pisos"}
    assert [c["area"] for c in ficha["construcciones"]] == [179.0, 191.6, 111.4, 179.5]
    assert all(c["anio"] is None and c["estructura"] is None for c in ficha["construcciones"])
    assert llamadas[1][1]["where"] == "cbml='04100190003'"


def test_medellin_sin_ladm_usa_destino(falso_get, fixture):
    falso_get(fixture("medellin/geocod_calle_44_52_165.json"),
              fixture("medellin/capa6_10100030004.json"),
              fixture("medellin/capa19_10100030004.json"),
              fixture("medellin/capa18_10100030004.json"))
    ficha = medellin.consultar("Calle 44 # 52-165")
    assert (ficha["destino"], ficha["pisos"]) == ("Comercial y Servicios", 13)
    assert all(c["uso"] is None for c in ficha["construcciones"])
    assert ficha["notas"]


def test_medellin_malla_vial_es_aproximada(falso_get, fixture):
    falso_get(fixture("medellin/geocod_malla_vial_calle_10_sur_50_20.json"))
    assert medellin.geocodificar("Calle 10 Sur # 50-20")["aproximada"] is True


def test_medellin_no_encontrada(falso_get, fixture):
    falso_get(fixture("medellin/geocod_no_encontrada.json"))
    assert medellin.consultar("xyz 123") is None


def test_medellin_fuerza_ipv4():
    adaptador = medellin.SESION.get_adapter("https://www.medellin.gov.co/servidormapas")
    assert isinstance(adaptador, medellin._SoloIPv4)


# --- Cali ---

def test_cali_un_predio(falso_get, fixture):
    llamadas = falso_get(fixture("cali/wfs_variables_kr100_11a_25.json"))
    ficha = cali.consultar("Carrera 100 # 11A-25")
    assert ficha == {
        "direccion_oficial": "KR 100 # 11 A - 25", "aproximada": False,
        "codigo": "760010100229800140156000000000", "lat": 3.3718329, "lon": -76.5405319,
        "destino": "Comercial", "pisos": 1,
        "construcciones": [{"anio": None, "area": 21, "uso": "Comercial", "estructura": None},
                           {"anio": None, "area": 8, "uso": "Comercial", "estructura": None}]}
    assert "direpred = 'KR 100 # 11 A - 25'" in llamadas[0][1]["CQL_FILTER"]
    assert llamadas[0][1]["srsName"] == "EPSG:4326"


def test_cali_ph_reune_todas_las_unidades(falso_get, fixture):
    falso_get(fixture("cali/wfs_variables_ph_cl44_47c_04.json"))
    ficha = cali.consultar("Calle 44 # 47C-04")
    assert ficha["codigo"] == "760010100160100660001… (5 predios)"
    assert ficha["pisos"] == 2
    assert len(ficha["construcciones"]) >= 5


def test_cali_no_encontrada(falso_get, fixture):
    falso_get(fixture("cali/wfs_variables_no_encontrada.json"))
    assert cali.consultar("Calle 999 # 1-1") is None


def test_cali_direccion_ilegible_no_consulta(falso_get):
    assert cali.consultar("Barrio El Peñón") is None and falso_get() == []


# --- Barranquilla ---

def test_barranquilla(falso_get, fixture):
    llamadas = falso_get(*[fixture(f"barranquilla/agol_carrera_55_48_26_{n}.json") for n in (1, 2, 3)])
    ficha = barranquilla.consultar("Carrera 55 # 48-26")
    assert _sin(ficha, "lat", "lon") == {
        "direccion_oficial": "Carrera 55 48 26", "aproximada": False,
        "codigo": "080010101000002110002000000000", "destino": "Habitacional", "pisos": 1,
        "construcciones": [{"anio": None, "area": 126, "uso": None, "estructura": None},
                           {"anio": None, "area": 2, "uso": None, "estructura": None}]}
    assert ficha["lat"] == pytest.approx(10.99397, abs=1e-5)
    assert ficha["lon"] == pytest.approx(-74.78574, abs=1e-5)
    assert llamadas[0][1]["outSR"] == "4326"
    assert llamadas[1][1]["where"] == "CODIGO LIKE '080010101000002110002%'"
    assert all("miciudad" not in url for url, _ in llamadas)  # nunca el servidor con Cloudflare


def test_barranquilla_ph(falso_get, fixture):
    falso_get(*[fixture(f"barranquilla/agol_ph_calle_101b_50_37_{n}.json") for n in (1, 2, 3)])
    ficha = barranquilla.consultar("Calle 101B # 50-37")
    assert ficha["codigo"] == "080010103000006660003… (3 predios)"
    assert (ficha["pisos"], ficha["destino"]) == (2, "Habitacional")


def test_barranquilla_no_encontrada(falso_get, fixture):
    falso_get(fixture("barranquilla/agol_no_encontrada_1.json"))
    assert barranquilla.consultar("Calle 999 # 1-1") is None


def test_barranquilla_error_arcgis(falso_get):
    falso_get({"error": {"code": 400, "message": "Invalid query"}})
    with pytest.raises(requests.RequestException):
        barranquilla.consultar("Carrera 55 # 48-26")


# --- Bucaramanga ---

def test_bucaramanga_no_ph(falso_get, fixture):
    llamadas = falso_get(*[fixture(f"bucaramanga/r1r2_carrera_15b_6_15_{n}.json") for n in (1, 2, 3)])
    ficha = bucaramanga.consultar("Carrera 15B # 6-15")
    assert _sin(ficha, "construcciones") == {
        "direccion_oficial": "K 15B 6 15 BR CHAPINERO", "aproximada": False,
        "codigo": "010601100023000", "lat": 7.1390547, "lon": -73.1313824,
        "destino": "Habitacional", "pisos": 2, "notas": []}
    assert [c["area"] for c in ficha["construcciones"]] == [117.0, 30.0]
    assert llamadas[2][1]["where"] == "local_id='68001010601100023000'"


def test_bucaramanga_ph_sin_pisos_ni_coordenadas(falso_get, fixture):
    llamadas = falso_get(*[fixture(f"bucaramanga/r1r2_ph_calle_36_17_37_{n}.json") for n in (1, 2)])
    ficha = bucaramanga.consultar("Calle 36 # 17-37")
    assert (ficha["pisos"], ficha["lat"], ficha["lon"]) == (None, None, None)
    assert ficha["destino"] == "Comercial" and ficha["notas"]
    assert len(llamadas) == 2  # no pide el terreno AMB


def test_bucaramanga_no_encontrada(falso_get, fixture):
    falso_get(fixture("bucaramanga/r1_no_encontrada_1.json"))
    assert bucaramanga.consultar("Calle 999 # 1-1") is None


# --- Manizales ---

def test_manizales(falso_get, fixture):
    llamadas = falso_get(*[fixture(f"manizales/ric_calle_63_12a_31_{n}.json") for n in (1, 2)])
    ficha = manizales.consultar("Calle 63 # 12A-31")
    assert _sin(ficha, "lat", "lon") == {
        "direccion_oficial": "C 63 12A 31", "aproximada": False,
        "codigo": "170010101000000730012000000000", "destino": "Habitacional", "pisos": 1,
        "construcciones": [{"anio": None, "area": 36.6, "uso": None, "estructura": None},
                           {"anio": None, "area": 79.9, "uso": None, "estructura": None}]}
    assert ficha["lat"] == pytest.approx(5.06220, abs=1e-5)
    assert llamadas[0][1]["where"].startswith("municipio='MANIZALES' AND (direccion = 'C 63 12A 31'")


def test_manizales_no_encontrada(falso_get, fixture):
    falso_get(fixture("manizales/ric_no_encontrada_1.json"))
    assert manizales.consultar("Calle 999 # 1-1") is None
