"""Común: coordenadas del inmueble -> mapa folium sobre el mapa base oficial del IGAC.

No se usa OpenStreetMap (el mapa por defecto de folium): el fondo es el "Mapa híbrido" que el IGAC
publica en su organización de ArcGIS Online (verificado el 2026-09-27: teselas en las 6 ciudades
hasta el zoom 15; más cerca, Leaflet amplía la última tesela).
"""
import folium

TESELAS_IGAC = ("https://tiles.arcgis.com/tiles/RVvWzU3lgJISqdke/arcgis/rest/services/"
                "Mapa_Hibrido/MapServer/tile/{z}/{y}/{x}")
ZOOM_MAX_IGAC = 15


def crear_mapa(lat: float, lon: float, etiqueta: str) -> folium.Map:
    """Mapa centrado en (lat, lon) con un marcador cuyo texto emergente es `etiqueta`."""
    m = folium.Map(location=[lat, lon], zoom_start=ZOOM_MAX_IGAC, max_zoom=18, tiles=None)
    folium.TileLayer(tiles=TESELAS_IGAC, attr="Mapa base: IGAC", name="IGAC",
                     max_native_zoom=ZOOM_MAX_IGAC, max_zoom=18).add_to(m)
    folium.Marker([lat, lon], popup=etiqueta, tooltip=etiqueta).add_to(m)
    return m
