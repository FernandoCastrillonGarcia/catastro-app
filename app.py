"""Interfaz Streamlit: municipio + dirección -> ficha del inmueble (gestor catastral oficial)."""
import requests
import streamlit as st

from municipios import MUNICIPIOS
from resumen import resumir

st.title("Ficha del inmueble")
municipio = MUNICIPIOS[st.selectbox("Municipio", list(MUNICIPIOS))]
st.caption(f"Fuente: {municipio['gestor']}")
direccion = st.text_input("Dirección", placeholder="Calle 48 Sur # 4B-42 Este")

if st.button("Consultar") and not direccion.strip():
    st.warning("Escribe una dirección.")
elif direccion.strip():
    try:
        with st.spinner(f"Consultando {municipio['gestor']}..."):
            ficha = municipio["consultar"](direccion)
    except (requests.RequestException, ValueError):
        st.error("Servicio no disponible. Intenta de nuevo más tarde.")
        st.stop()

    if ficha is None:
        st.error("Dirección no encontrada.")
        st.stop()
    if ficha["aproximada"]:
        st.warning(f"Dirección aproximada: se usó {ficha['direccion_oficial']}. "
                   "El predio podría no ser el que buscas.")
    for nota in ficha.get("notas", []):
        st.info(nota)

    r = resumir(ficha)
    sin_dato = municipio["sin_dato"]

    def valor(variable, texto):
        if texto:
            return texto
        return "Sin dato. " + sin_dato.get(variable, "El predio no tiene este dato en la fuente.")

    uso = r["uso"]
    if uso and r["destino"] and r["destino"] != uso:
        uso = f"{uso} (destino económico: {r['destino']})"
    st.table(
        {
            "Año de construcción": valor("anio", r["anio"] and str(r["anio"]["anio"])),
            "Tipo de construcción (material)": valor("estructura", r["estructura"]),
            "Uso": valor("uso", uso),
            "CIIU": valor("ciiu", None),
            "Número de pisos": valor("pisos", r["pisos"] and str(r["pisos"])),
            "Coordenadas (lat, lon)": valor(
                "coordenadas", r["lat"] is not None and f"{r['lat']:.6f}, {r['lon']:.6f}"),
            "Tipología": valor("tipologia", r["tipologia"] and
                               f"{r['tipologia']} (derivada del uso y los pisos)"),
        },
        border="horizontal",
    )
    st.caption(f"Dirección catastral: {ficha['direccion_oficial']} · "
               f"{municipio['nombre_codigo']}: {ficha['codigo']}")
    if r["anio"] and len(r["anio"]["detalle"]) > 1:
        st.write("Construcciones en el lote por año:")
        for anio, area in r["anio"]["detalle"]:
            st.write(f"- {anio}: {area} m²")
    if len(r["usos"]) > 1:
        st.write("Usos en el lote:")
        for nombre, area in r["usos"]:
            st.write(f"- {nombre}: {area} m²")
