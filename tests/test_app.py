"""Mensajes y ficha de la UI (AppTest, sin red)."""
from pathlib import Path

import requests
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def consultar(direccion, municipio=None):
    at = AppTest.from_file(APP, default_timeout=10).run()
    if municipio:
        at.selectbox[0].select(municipio).run()
    at.text_input[0].set_value(direccion).run()
    assert not at.exception
    return at


def ficha_ui(at) -> dict:
    tabla = at.table[0].value
    return {fila: str(tabla.loc[fila].iloc[0]) for fila in tabla.index}


def _bogota(falso_get, fixture, geo=None):
    falso_get(geo or fixture("bogota/geocodificar_cl48sur_4b42este.json"),
              fixture("bogota/predio_variables_001328010005.json"),
              fixture("bogota/predio_dominios.json"),
              fixture("bogota/construccion_pisos_001328010005.json"))


def test_bogota_ficha_completa(falso_get, fixture):
    _bogota(falso_get, fixture)
    at = consultar("Calle 48 Sur # 4B-42 Este")
    assert not at.error and not at.warning and not at.info
    ficha = ficha_ui(at)
    assert ficha["Año de construcción"] == "1984"
    assert ficha["Tipo de construcción (material)"] == \
        "Armazón: ladrillo, bloque; muros: bloque, ladrillo"
    assert ficha["Uso"] == \
        "Habitacional menor o igual a 3 pisos en NPH (destino económico: Residencial)"
    assert ficha["CIIU"].startswith("Sin dato. Ninguna fuente oficial pública")
    assert ficha["Número de pisos"] == "3"
    assert ficha["Coordenadas (lat, lon)"] == "4.541103, -74.094117"
    assert ficha["Tipología"] == "Casa (derivada del uso y los pisos)"
    assert [c.value for c in at.caption] == [
        "Fuente: Catastro Bogotá (UAECD)",
        "Dirección catastral: CL 48 S 4B 42 E · Lote: 001328010005"]
    assert [m.value for m in at.markdown] == [
        "Construcciones en el lote por año:", "- 1984: 204.6 m²", "- 2012: 51.6 m²"]


def test_aproximada(falso_get, fixture):
    geo = fixture("bogota/geocodificar_cl48sur_4b42este.json")
    geo["response"]["data"]["tipo_direccion"] = "Dirección por aproximación"
    _bogota(falso_get, fixture, geo)
    at = consultar("Calle 48 Sur 4B 42 Este")
    assert [w.value for w in at.warning] == [
        "Dirección aproximada: se usó CL 48 S 4B 42 E. El predio podría no ser el que buscas."]


def test_ciudad_sin_anio_explica_motivo(falso_get, fixture):
    falso_get(*[fixture(f"manizales/ric_calle_63_12a_31_{n}.json") for n in (1, 2)])
    at = consultar("Calle 63 # 12A-31", "Manizales")
    assert not at.error
    ficha = ficha_ui(at)
    assert ficha["Año de construcción"].startswith("Sin dato. El reporte nacional del IGAC")
    assert ficha["Tipo de construcción (material)"] == \
        "Sin dato. El gestor no publica el material de la estructura (revisado 2026-09-27)."
    assert ficha["Uso"] == "Habitacional"
    assert ficha["Número de pisos"] == "1"
    assert ficha["Tipología"] == "Casa (derivada del uso y los pisos)"


def test_nota_de_la_ciudad(falso_get, fixture):
    falso_get(*[fixture(f"bucaramanga/r1r2_ph_calle_36_17_37_{n}.json") for n in (1, 2)])
    at = consultar("Calle 36 # 17-37", "Bucaramanga")
    assert [i.value for i in at.info][0].startswith("Propiedad horizontal:")
    ficha = ficha_ui(at)
    assert ficha["Número de pisos"] == "Sin dato. El predio no tiene este dato en la fuente."
    assert ficha["Coordenadas (lat, lon)"].startswith("Sin dato.")


def test_no_encontrada(falso_get, fixture):
    falso_get(fixture("bogota/geocodificar_fallo.json"))
    at = consultar("xyz")
    assert [e.value for e in at.error] == ["Dirección no encontrada."]
    assert not at.table


def test_servicio_no_disponible(falso_get):
    falso_get(requests.Timeout())
    at = consultar("Calle 72 # 10-34")
    assert [e.value for e in at.error] == ["Servicio no disponible. Intenta de nuevo más tarde."]
    assert not at.table
