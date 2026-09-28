"""Mapa del inmueble (sin red: folium solo arma el HTML; las teselas las pide el navegador)."""
from mapa import TESELAS, crear_mapa


def test_mapa_centrado_con_marcador_sin_texto():
    m = crear_mapa(4.541102868, -74.094116527)
    html = m.get_root().render()
    assert m.location == [4.541102868, -74.094116527]
    assert TESELAS in html
    assert "openstreetmap" not in html.lower()
    assert "bindPopup" not in html and "bindTooltip" not in html
