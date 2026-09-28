"""Común: coordenadas del inmueble -> mapa folium con un solo marcador (sin texto).

Fondo de calles estilo Google Maps: "World Street Map" de Esri (solo visual, no es fuente de
datos). No se usan las teselas de Google (sus términos no lo permiten) ni OpenStreetMap.
"""
import folium

TESELAS = ("https://server.arcgisonline.com/ArcGIS/rest/services/"
           "World_Street_Map/MapServer/tile/{z}/{y}/{x}")


def crear_mapa(lat: float, lon: float) -> folium.Map:
    """Mapa centrado en (lat, lon) con un marcador."""
    m = folium.Map(location=[lat, lon], zoom_start=17, max_zoom=19, tiles=None)
    folium.TileLayer(tiles=TESELAS, attr="Esri", name="Calles", max_zoom=19).add_to(m)
    folium.Marker([lat, lon]).add_to(m)
    return m
