import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation
from streamlit_drawable_canvas import st_canvas

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
    ACCESS_GRANTED = (admin_pass == "AdminIntmex2026*") 

# Inicializar estados de sesión para el flujo de la firma
if "modo_firma" not in st.session_state:
    st.session_state.modo_firma = False
if "firma_guardada" not in st.session_state:
    st.session_state.firma_guardada = False

# ---------------------------------------------------------
# 2. PANTALLA EXCLUSIVA DE LIENZO PARA LA FIRMA
# ---------------------------------------------------------
if st.session_state.modo_firma:
    st.markdown("### ✍️ Lienzo de Firma del Cliente")
    st.info("Pida al cliente que firme dentro del recuadro utilizando su dedo o un lápiz táctil.")
    
    # Lienzo interactivo de dibujo
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=350,
        width=400,
        drawing_mode="freedraw",
        key="canvas_firma",
    )
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("✅ Aceptar Firma"):
            if canvas_result.image_data is not None:
                st.session_state.firma_guardada = True
                st.session_state.modo_firma = False
                st.success("¡Firma capturada correctamente!")
                st.rerun()
            else:
                st.warning("Por favor, realice una firma antes de aceptar.")
    with col_f2:
        if st.button("❌ Cancelar"):
            st.session_state.modo_firma = False
            st.rerun()

else:
    # ---------------------------------------------------------
    # 3. CAPTURA DE UBICACIÓN GPS REAL
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
    # 4. FORMULARIO DE REGISTRO
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
        
        # Manejo de la evidencia visual en el formulario
        foto_fachada = None
        if tipo_evidencia == "Foto de la Fachada (Cámara trasera)":
            st.info("📷 Capture la foto de la fachada utilizando la cámara trasera.")
            foto_fachada = st.camera_input("Tomar foto de la fachada")

        st.write("📍 **Ubicación GPS:** Se validará automáticamente.")
        
        submitted = st.form_submit_button("Registrar Cliente")

    # Botones fuera del form para activar el lienzo de firma si eligieron esa opción
    if tipo_evidencia == "Firma del Cliente":
        if not st.session_state.firma_guardada:
            if st.button("✍️ Abrir Lienzo para Firmar"):
                st.session_state.modo_firma = True
                st.rerun()
        else:
            st.success("✅ Firma registrada y lista para el envío.")
            if st.button("🔄 Cambiar / Volver a firmar"):
                st.session_state.firma_guardada = False
                st.session_state.modo_firma = True
                st.rerun()

    if submitted:
        # Validaciones
        evidencia_valida = False
        desc_evidencia = "Sin evidencia"

        if tipo_evidencia == "Seleccione":
            st.error("⚠️ Debe seleccionar un tipo de evidencia obligatoria (Firma o Foto).")
        elif tipo_evidencia == "Firma del Cliente" and not st.session_state.firma_guardada:
            st.error("⚠️ Debe capturar la firma del cliente usando el botón de lienzo.")
        elif tipo_evidencia == "Foto de la Fachada (Cámara trasera)" and foto_fachada is None:
            st.error("⚠️ Debe tomar la foto de la fachada para completar el registro.")
        else:
            evidencia_valida = True
            if tipo_evidencia == "Firma del Cliente":
                desc_evidencia = "Firma capturada en lienzo"
            else:
                desc_evidencia = "Foto de fachada capturada"

        if not nombre_cliente or not quien_recibe:
            st.error("⚠️ Complete el Nombre del Cliente y el Nombre de quien recibe.")
        elif tipo_cte == "Seleccione" or visibilidad == "Seleccione" or accesibilidad == "Seleccione" or comprador == "Seleccione" or promo == "Seleccione":
            st.error("⚠️ Debe completar todos los campos del Tabulador de Supervisión.")
        elif not agotados:
            st.error("⚠️ El campo de Agotados es obligatorio (indique SKU o escriba 'Ninguno').")
        elif lat_real == 0.0 or lon_real == 0.0:
            st.error("⚠️ No se ha podido capturar la ubicación GPS. Autorice el acceso en el botón superior.")
        elif evidencia_valida:
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
                "Evidencia": desc_evidencia,
                "Notas": notas,
                "Latitud": lat_real,
                "Longitud": lon_real,
                "LinkMaps": link_maps
            }
            
            if "datos" not in st.session_state:
                st.session_state.datos = []
            
            st.session_state.datos.append(nuevo_registro)
            
            # Resetear estado de firma para el siguiente cliente
            st.session_state.firma_guardada = False
            
            st.success("✅ ¡Cliente registrado con éxito y tabulador completado!")

# ---------------------------------------------------------
# 5. DASHBOARD EXCLUSIVO PARA ADMINISTRADORES
# ---------------------------------------------------------
if ACCESS_GRANTED:
    st.divider()
    st.header("🔒 Dashboard de Administración (Acceso Autorizado)")
    
    if "datos" in st.session_state and len(st.session_state.datos) > 0:
        df = pd.DataFrame(st.session_state.datos)
        
        st.subheader("📊 Registros de Clientes y Tabulador")
        df_display = df.drop(columns=["LinkMaps"], errors="ignore")
        st.dataframe(df_display)

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
