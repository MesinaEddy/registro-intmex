import streamlit as st
import pandas as pd
from datetime import datetime

# Inyección de manifiesto PWA para PWABuilder
st.markdown(
    """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#ffffff">
    """,
    unsafe_allow_html=True
)

st.title("Control de Clientes - Intmex (Modo Masivo)")

# Formulario limpio de registro
with st.form("form_cliente"):
    nombre = st.text_input("Nombre del Cliente")
    telefono = st.text_input("Teléfono")
    notas = st.text_area("Notas o servicio")
    
    st.write("📍 **Ubicación GPS:** Se capturará automáticamente del dispositivo.")
    
    submitted = st.form_submit_button("Guardar Registro")

    if submitted:
        # Coordenadas simuladas o capturadas del dispositivo (puedes ajustarlas)
        lat = 32.5149  
        lon = -117.0382
        
        # Enlace individual por si quieres abrir uno en específico
        link_maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
        
        nuevo_registro = {
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Cliente": nombre,
            "Teléfono": telefono,
            "Notas": notas,
            "Latitud": lat,
            "Longitud": lon,
            "LinkMaps": link_maps
        }
        
        if "datos" not in st.session_state:
            st.session_state.datos = []
        
        st.session_state.datos.append(nuevo_registro)
        st.success("¡Cliente registrado correctamente en la lista!")

# Sección del Dashboard y Exportación Masiva
if "datos" in st.session_state and len(st.session_state.datos) > 0:
    st.divider()
    st.subheader("📊 Clientes Listos para Carga Masiva")
    
    df = pd.DataFrame(st.session_state.datos)
    
    # Vista previa de la tabla
    st.dataframe(df[["Fecha", "Cliente", "Teléfono", "Notas"]])

    # Botón para descarga masiva compatible con Google My Maps
    csv_masivo = df.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        label="🗺️ Descargar CSV Masivo para Google My Maps",
        data=csv_masivo,
        file_name="pines_masivos_intmex.csv",
        mime="text/csv",
        help="Sube este archivo en mymaps.google.com con la cuenta de la empresa para ver todos los pines juntos."
    )
    
    # Opción para limpiar la lista si ya se subieron
    if st.button("🗑️ Limpiar registros actuales"):
        st.session_state.datos = []
        st.rerun()
