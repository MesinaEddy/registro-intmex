import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation

# Inyección de manifiesto PWA para PWABuilder
st.markdown(
    """
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#ffffff">
    """,
    unsafe_allow_html=True
)

st.title("Control de Clientes - Intmex")

# ---------------------------------------------------------
# 1. CONTROL DE ACCESO AL DASHBOARD (Solo Administrador)
# ---------------------------------------------------------
with st.sidebar:
    st.subheader("Panel de Administración")
    admin_pass = st.text_input("Contraseña de Admin", type="password")
    
    # Contraseña de administrador
    ACCESS_GRANTED = (admin_pass == "AdminIntmex2026*") 

# ---------------------------------------------------------
# 2. CAPTURA DE UBICACIÓN GPS REAL (Forzar Permisos)
# ---------------------------------------------------------
st.subheader("📍 Geolocalización del Dispositivo")
st.info("Haz clic en el botón de abajo para permitir y obtener la ubicación GPS actual.")

loc = streamlit_geolocation()

lat_real = 0.0
lon_real = 0.0

if loc.get('latitude') and loc.get('longitude'):
    lat_real = loc['latitude']
    lon_real = loc['longitude']
    st.success(f"✅ Ubicación GPS obtenida: Lat: {lat_real}, Lon: {lon_real}")
else:
    st.warning("⚠️ Esperando permisos de ubicación o clic en el botón de geolocalización...")

# ---------------------------------------------------------
# 3. FORMULARIO DE REGISTRO CON TABULADOR Y EVIDENCIA OBLIGATORIA
# ---------------------------------------------------------
st.subheader("📝 Registro de Nuevo Cliente y Tabulador")

with st.form("form_registro_cliente"):
    st.markdown("### 📌 Datos Generales")
    nombre_cliente = st.text_input("Nombre del Cliente")
    telefono = st.text_input("Teléfono")
    quien_recibe = st.text_input("Nombre de quien recibe")
    notas = st.text_area("Notas o servicio realizado")
    
    st.divider()
    st.markdown("### 📊 Tabulador de Supervisión (Obligatorio)")
    
    col1, col2 = st.columns(2)
    with col1:
        tipo_cte = st.selectbox("Tipo Cte", ["Seleccione", "A", "B", "C"])
        visibilidad = st.selectbox("Visibilidad", ["Seleccione", "✓ (Sí)", "X (No)"])
        accesibilidad = st.selectbox("Accesibilidad", ["Seleccione", "✓ (Sí)", "X (No)"])
    
    with col2:
        comprador = st.selectbox("Comprador", ["Seleccione", "✓ (Sí)", "X (No)"])
        promo = st.selectbox("Promo", ["Seleccione", "✓ (Sí)", "X (No)"])
    
    agotados = st.text_input("Agotados (Indicar SKU o Escribir 'Ninguno')")

    st.divider()
    st.markdown("### 📸 Evidencia Obligatoria")
    tipo_evidencia = st.radio(
        "Seleccione el tipo de evidencia obligatoria:",
        ["Seleccione", "Firma del Cliente", "Foto de la Fachada (Cámara trasera)"]
    )
    
    evidencia_cargada = None
    if tipo_evidencia == "Firma del Cliente":
        st.info("✍️ Solicite al cliente que firme en el dispositivo.")
        archivo_firma = st.file_uploader("Subir imagen de la firma", type=["png", "jpg", "jpeg"])
        if archivo_firma is not None:
            evidencia_cargada = "Firma cargada"
    elif tipo_evidencia == "Foto de la Fachada (Cámara trasera)":
        st.info("📷 Capture la foto de la fachada utilizando la cámara trasera.")
        foto_fachada = st.camera_input("Tomar foto de la fachada")
        if foto_fachada is not None:
            evidencia_cargada = "Foto de fachada cargada"

    st.write("📍 **Ubicación GPS:** Se validará automáticamente.")
    
    # Botón final de registro
    submitted = st.form_submit_button("Registrar Cliente")

    if submitted:
        # Validaciones de campos obligatorios
        if not nombre_cliente or not quien_recibe:
            st.error("⚠️ Complete el Nombre del Cliente y el Nombre de quien recibe.")
        elif tipo_cte == "Seleccione" or visibilidad == "Seleccione" or accesibilidad == "Seleccione" or comprador == "Seleccione" or promo == "Seleccione":
            st.error("⚠️ Debe completar todos los campos del Tabulador de Supervisión.")
        elif not agotados:
            st.error("⚠️ El campo de Agotados es obligatorio (indique SKU o escriba 'Ninguno').")
        elif tipo_evidencia == "Seleccione":
            st.error("⚠️ Debe seleccionar un tipo de evidencia obligatoria (Firma o Foto).")
        elif evidencia_cargada is None:
            st.error("⚠️ La evidencia seleccionada es obligatoria para completar el registro.")
        elif lat_real == 0.0 or lon_real == 0.0:
            st.error("⚠️ No se ha podido capturar la ubicación GPS. Autorice el acceso en el botón superior.")
        else:
            link_maps = f"https://www.google.com/maps/search/?api=1&query={lat_real},{lon_real}"
            
            nuevo_registro = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cliente": nombre_cliente,
                "Teléfono": telefono,
                "Quien Recibe": quien_recibe,
                "Tipo Cte": tipo_cte,
                "Visibilidad": visibilidad,
                "Accesibilidad": accesibilidad,
                "Comprador": comprador,
                "Promo": promo,
                "Agotados": agotados,
                "Evidencia": evidencia_cargada,
                "Notas": notas,
                "Latitud": lat_real,
                "Longitud": lon_real,
                "LinkMaps": link_maps
            }
            
            if "datos" not in st.session_state:
                st.session_state.datos = []
            
            st.session_state.datos.append(nuevo_registro)
            
            st.success("✅ ¡Cliente registrado con éxito y tabulador completado!")

# ---------------------------------------------------------
# 4. DASHBOARD EXCLUSIVO PARA ADMINISTRADORES
# ---------------------------------------------------------
if ACCESS_GRANTED:
    st.divider()
    st.header("🔒 Dashboard de Administración (Acceso Autorizado)")
    
    if "datos" in st.session_state and len(st.session_state.datos) > 0:
        df = pd.DataFrame(st.session_state.datos)
        
        st.subheader("📊 Registros de Clientes y Tabulador")
        st.dataframe(df)

        # Botón de descarga masiva compatible con Google My Maps
        csv_masivo = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="🗺️ Descargar CSV Masivo para Google My Maps",
            data=csv_masivo,
            file_name="pines_masivos_intmex.csv",
            mime="text/csv",
            help="Sube este archivo en mymaps.google.com con la cuenta de la empresa."
        )
        
        if st.button("🗑️ Limpiar Base de Datos de Registros"):
            st.session_state.datos = []
            st.rerun()
    else:
        st.info("No hay registros guardados todavía.")
else:
    if admin_pass != "":
        st.sidebar.error("Contraseña incorrecta. El dashboard permanece oculto.")
