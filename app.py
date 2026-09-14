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
st.info("Por favor, haz clic en el botón de abajo para permitir y obtener la ubicación GPS actual del dispositivo.")

# Este componente lanza la ventana emergente nativa del celular/navegador pidiendo permisos de ubicación
loc = streamlit_geolocation()

# Extraemos las coordenadas reales si el usuario ya autorizó
lat_real = 0.0
lon_real = 0.0

if loc.get('latitude') and loc.get('longitude'):
    lat_real = loc['latitude']
    lon_real = loc['longitude']
    st.success(f"✅ Ubicación GPS obtenida con éxito: Lat: {lat_real}, Lon: {lon_real}")
else:
    st.warning("⚠️ Esperando permisos de ubicación o clic en el botón de geolocalización...")

# ---------------------------------------------------------
# 3. FORMULARIO DE REGISTRO PARA OPERADORES Y CAMPO
# ---------------------------------------------------------
st.subheader("📝 Registro de Nuevo Cliente")

with st.form("form_registro_cliente"):
    nombre_cliente = st.text_input("Nombre del Cliente")
    telefono = st.text_input("Teléfono")
    
    # Campo: Nombre de quien recibe
    quien_recibe = st.text_input("Nombre de quien recibe")
    
    notas = st.text_area("Notas o servicio realizado")
    
    st.divider()
    st.write("📸 **Apartado de Evidencia (Opcional)**")
    tipo_evidencia = st.radio(
        "¿Desea agregar evidencia en este registro?",
        ["No agregar evidencia", "Firma del Cliente", "Foto de la Fachada (Cámara trasera)"]
    )
    
    evidencia_cargada = "Sin evidencia"
    if tipo_evidencia == "Firma del Cliente":
        st.info("✍️ Solicite al cliente que firme en el dispositivo (Opcional).")
        archivo_firma = st.file_uploader("Subir imagen de la firma", type=["png", "jpg", "jpeg"])
        if archivo_firma is not None:
            evidencia_cargada = "Firma cargada"
    elif tipo_evidencia == "Foto de la Fachada (Cámara trasera)":
        st.info("📷 Capture la foto de la fachada utilizando la cámara trasera (Opcional).")
        foto_fachada = st.camera_input("Tomar foto de la fachada")
        if foto_fachada is not None:
            evidencia_cargada = "Foto de fachada cargada"

    # Botón final de registro
    submitted = st.form_submit_button("Registrar Cliente")

    if submitted:
        # Validaciones obligatorias
        if not nombre_cliente or not quien_recibe:
            st.error("⚠️ Por favor complete el Nombre del Cliente y el Nombre de quien recibe.")
        elif lat_real == 0.0 or lon_real == 0.0:
            st.error("⚠️ No se ha podido capturar la ubicación GPS. Asegúrate de presionar el botón de geolocalización arriba y permitir el acceso.")
        else:
            link_maps = f"https://www.google.com/maps/search/?api=1&query={lat_real},{lon_real}"
            
            nuevo_registro = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Cliente": nombre_cliente,
                "Teléfono": telefono,
                "Quien Recibe": quien_recibe,
                "Notas": notas,
                "Evidencia": evidencia_cargada,
                "Latitud": lat_real,
                "Longitud": lon_real,
                "LinkMaps": link_maps
            }
            
            if "datos" not in st.session_state:
                st.session_state.datos = []
            
            st.session_state.datos.append(nuevo_registro)
            
            # Leyenda flotante temporal de éxito
            st.success("✅ ¡Cliente registrado con éxito y geolocalizado!")

# ---------------------------------------------------------
# 4. DASHBOARD EXCLUSIVO PARA ADMINISTRADORES
# ---------------------------------------------------------
if ACCESS_GRANTED:
    st.divider()
    st.header("🔒 Dashboard de Administración (Acceso Autorizado)")
    
    if "datos" in st.session_state and len(st.session_state.datos) > 0:
        df = pd.DataFrame(st.session_state.datos)
        
        st.subheader("📊 Registros de Clientes Actuales")
        st.dataframe(df[["Fecha", "Cliente", "Teléfono", "Quien Recibe", "Evidencia", "Latitud", "Longitud", "Notas"]])

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
