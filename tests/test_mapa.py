"""Mapa del inmueble (sin red: folium solo arma el HTML; las teselas las pide el navegador)."""
from mapa import TESELAS_IGAC, crear_mapa


def test_mapa_centrado_con_marcador_y_fondo_igac():
    m = crear_mapa(4.541102868, -74.094116527, "CL 48 S 4B 42 E")
    html = m.get_root().render()
    assert m.location == [4.541102868, -74.094116527]
    assert TESELAS_IGAC in html
    assert "openstreetmap" not in html.lower()
    assert "CL 48 S 4B 42 E" in html
