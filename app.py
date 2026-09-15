import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation
from streamlit_drawable_canvas import st_canvas
import io

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

# Inicializar estados de sesión y valores persistentes
if "modo_firma" not in st.session_state:
    st.session_state.modo_firma = False
if "modo_camara" not in st.session_state:
    st.session_state.modo_camara = False
if "datos_foto_buffer" not in st.session_state:
    st.session_state.datos_foto_buffer = None
if "tipo_evidencia" not in st.session_state:
    st.session_state.tipo_evidencia = "Seleccione"

# Lista completa de rutas solicitadas
LISTA_RUTAS = ["Seleccione Ruta"] + [f"R{i}" for i in range(1, 17)] + ["C301", "C302"]

defaults = {
    "num_ruta": "Seleccione Ruta",
    "nombre_asesor": "",
    "nombre_cliente": "",
    "telefono": "",
    "quien_recibe": "",
    "notas": "",
    "tipo_cte": "Seleccione",
    "visibilidad": "Seleccione",
    "accesibilidad": "Seleccione",
    "comprador": "Seleccione",
    "promo_seleccion": "Seleccione",
    "desc_promo": "",
    "codigos_sin_impactar": ""
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ---------------------------------------------------------
# FUNCIÓN CENTRALIZADA PARA GUARDAR EL REGISTRO AUTOMÁTICO
# ---------------------------------------------------------
def ejecutar_registro_automatico(lat_real, lon_real, desc_evidencia):
    # Validaciones obligatorias antes de guardar
    if st.session_state.num_ruta == "Seleccione Ruta" or not st.session_state.nombre_asesor:
        st.error("⚠️ Seleccione una Ruta válida y complete el Nombre del Asesor.")
        return False
    if not st.session_state.nombre_cliente or not st.session_state.quien_recibe:
        st.error("⚠️ Complete el Nombre del Cliente y el Nombre de quien recibe.")
        return False
    if st.session_state.tipo_cte == "Seleccione" or st.session_state.visibilidad == "Seleccione" or st.session_state.accesibilidad == "Seleccione" or st.session_state.comprador == "Seleccione":
        st.error("⚠️ Debe completar todos los campos del Tabulador de Supervisión.")
        return False
    if st.session_state.promo_seleccion == "Seleccione":
        st.error("⚠️ Indique si hubo Promo o no en la sección de Detalle de Promoción.")
        return False
    if st.session_state.promo_seleccion == "✓ (Sí)" and not st.session_state.desc_promo:
        st.error("⚠️ Indique la descripción de la promo impactada.")
        return False
    if not st.session_state.codigos_sin_impactar:
        st.error("⚠️ El campo de Códigos sin Impactar es obligatorio (indique SKU o escriba 'Ninguno').")
        return False
    if lat_real == 0.0 or lon_real == 0.0:
        st.error("⚠️ No se ha podido capturar la ubicación GPS. Autorice el acceso a la ubicación en el navegador.")
        return False

    link_maps = f"https://www.google.com/maps/search/?api=1&query={lat_real},{lon_real}"
    texto_promo_final = f"Sí - {st.session_state.desc_promo}" if st.session_state.promo_seleccion == "✓ (Sí)" else "No"

    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Ruta": st.session_state.num_ruta,
        "Asesor": st.session_state.nombre_asesor,
        "Cliente": st.session_state.nombre_cliente,
        "Teléfono": st.session_state.telefono,
        "Quien Recibe": st.session_state.quien_recibe,
        "Tipo Cte": st.session_state.tipo_cte,
        "Visibilidad": st.session_state.visibilidad,
        "Accesibilidad": st.session_state.accesibilidad,
        "Comprador": st.session_state.comprador,
        "Promo": texto_promo_final,
        "Codigos sin Impactar": st.session_state.codigos_sin_impactar,
        "Evidencia": desc_evidencia,
        "Notas": st.session_state.notas,
        "Latitud": lat_real,
        "Longitud": lon_real,
        "LinkMaps": link_maps
    }
    
    if "datos" not in st.session_state:
        st.session_state.datos = []
    
    st.session_state.datos.append(nuevo_registro)
    
    # Limpiar formulario tras el éxito
    st.session_state.tipo_evidencia = "Seleccione"
    for k in defaults:
        st.session_state[k] = defaults[k]
        
    st.success("✅ ¡Cliente registrado con éxito de forma automática!")
    return True

# ---------------------------------------------------------
# OBTENER GPS (GLOBAL)
# ---------------------------------------------------------
st.subheader("📍 Geolocalización del Dispositivo")
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
# 2. PANTALLA EXCLUSIVA DE LIENZO PARA LA FIRMA
# ---------------------------------------------------------
if st.session_state.modo_firma:
    st.markdown("### ✍️ Lienzo de Firma del Cliente")
    st.info("Pida al cliente que firme dentro del recuadro utilizando su dedo o un lápiz táctil.")
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=350,
        width=400,
        drawing_mode="freedraw",
        return_image_data=True,
        key="canvas_firma",
    )
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        if st.button("✅ Aceptar Firma y Registrar"):
            if canvas_result.image_data is not None:
                exito = ejecutar_registro_automatico(lat_real, lon_real, "Firma capturada en lienzo")
                if exito:
                    st.session_state.modo_firma = False
                    st.rerun()
            else:
                st.warning("Por favor, realice una firma antes de aceptar.")
    with col_f2:
        if st.button("❌ Cancelar"):
            st.session_state.modo_firma = False
            st.rerun()

# ---------------------------------------------------------
# 3. PANTALLA EXCLUSIVA DE CÁMARA PARA LA FACHADA
# ---------------------------------------------------------
elif st.session_state.modo_camara:
    st.markdown("### 📷 Capturar Foto de la Fachada")
    st.info("Apunte con la cámara hacia la fachada del establecimiento y tome la foto.")
    
    foto_capturada = st.camera_input("Tomar foto")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if foto_capturada is not None:
            if st.button("✅ Usar esta Foto y Registrar"):
                exito = ejecutar_registro_automatico(lat_real, lon_real, "Foto de fachada capturada")
                if exito:
                    st.session_state.modo_camara = False
                    st.rerun()
    with col_c2:
        if st.button("❌ Cancelar"):
            st.session_state.modo_camara = False
            st.rerun()

else:
    # ---------------------------------------------------------
    # 4. FORMULARIO INTERACTIVO LIBRE (SIN st.form)
    # ---------------------------------------------------------
    st.subheader("📝 Registro de Nuevo Cliente y Tabulador")

    st.markdown("### 📌 Datos de Ruta y Asesor")
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        idx_ruta = LISTA_RUTAS.index(st.session_state.num_ruta) if st.session_state.num_ruta in LISTA_RUTAS else 0
        st.session_state.num_ruta = st.selectbox("Seleccione Ruta", LISTA_RUTAS, index=idx_ruta)
    with col_r2:
        st.session_state.nombre_asesor = st.text_input("Nombre del Asesor", value=st.session_state.nombre_asesor)

    st.markdown("### 📌 Datos Generales del Cliente")
    st.session_state.nombre_cliente = st.text_input("Nombre del Cliente", value=st.session_state.nombre_cliente)
    st.session_state.telefono = st.text_input("Teléfono", value=st.session_state.telefono)
    st.session_state.quien_recibe = st.text_input("Nombre de quien recibe", value=st.session_state.quien_recibe)
    st.session_state.notas = st.text_area("Notas o servicio realizado", value=st.session_state.notas)
    
    st.divider()
    st.markdown("### 📊 Tabulador de Supervisión (Obligatorio)")
    
    col1, col2 = st.columns(2)
    with col1:
        opts_tipo = ["Seleccione", "A", "B", "C"]
        st.session_state.tipo_cte = st.selectbox("Tipo Cte", opts_tipo, index=opts_tipo.index(st.session_state.tipo_cte) if st.session_state.tipo_cte in opts_tipo else 0)

        opts_visi = ["Seleccione", "✓ (Sí)", "X (No)"]
        st.session_state.visibilidad = st.selectbox("Visibilidad", opts_visi, index=opts_visi.index(st.session_state.visibilidad) if st.session_state.visibilidad in opts_visi else 0)

        opts_acce = ["Seleccione", "✓ (Sí)", "X (No)"]
        st.session_state.accesibilidad = st.selectbox("Accesibilidad", opts_acce, index=opts_acce.index(st.session_state.accesibilidad) if st.session_state.accesibilidad in opts_acce else 0)
    
    with col2:
        opts_comp = ["Seleccione", "✓ (Sí)", "X (No)"]
        st.session_state.comprador = st.selectbox("Comprador", opts_comp, index=opts_comp.index(st.session_state.comprador) if st.session_state.comprador in opts_comp else 0)

        opts_promo = ["Seleccione", "✓ (Sí)", "X (No)"]
        st.session_state.promo_seleccion = st.selectbox("Promo", opts_promo, index=opts_promo.index(st.session_state.promo_seleccion) if st.session_state.promo_seleccion in opts_promo else 0)

    st.session_state.codigos_sin_impactar = st.text_input("Códigos sin Impactar (Indicar SKU o Escribir 'Ninguno')", value=st.session_state.codigos_sin_impactar)

    st.divider()

    # ---------------------------------------------------------
    # 5. CAMPO DINÁMICO DE PROMO
    # ---------------------------------------------------------
    if st.session_state.promo_seleccion == "✓ (Sí)":
        st.markdown("### 🎯 Detalle de Promoción")
        st.session_state.desc_promo = st.text_area("📝 Escriba la descripción de la promo impactada (Obligatorio)", value=st.session_state.desc_promo)

    st.divider()
    
    # ---------------------------------------------------------
    # 6. SELECCIÓN DE EVIDENCIA OBLIGATORIA Y ACCIÓN DIRECTA
    # ---------------------------------------------------------
    st.markdown("### 📸 Evidencia Obligatoria y Finalización")
    st.info("Seleccione el tipo de evidencia que desea capturar. Al aceptar la firma o la foto, **el registro se guardará automáticamente**.")

    opciones_evidencia = ["Seleccione", "Firma del Cliente", "Foto de la Fachada (Cámara trasera)"]
    indice_actual = opciones_evidencia.index(st.session_state.tipo_evidencia) if st.session_state.tipo_evidencia in opciones_evidencia else 0

    tipo_evidencia = st.radio(
        "Seleccione el tipo de evidencia obligatoria:",
        opciones_evidencia,
        index=indice_actual,
        key="radio_evidencia_cambio",
        on_change=lambda: setattr(st.session_state, 'tipo_evidencia', st.session_state.radio_evidencia_cambio)
    )

    if st.session_state.tipo_evidencia == "Firma del Cliente":
        st.markdown("---")
        if st.button("✍️ Abrir Lienzo y Firmar"):
            st.session_state.modo_firma = True
            st.rerun()

    elif st.session_state.tipo_evidencia == "Foto de la Fachada (Cámara trasera)":
        st.markdown("---")
        if st.button("📷 Abrir Cámara para Fachada"):
            st.session_state.modo_camara = True
            st.rerun()

# ---------------------------------------------------------
# 7. DASHBOARD EXCLUSIVO PARA ADMINISTRADORES
# ---------------------------------------------------------
if ACCESS_GRANTED:
    st.divider()
    st.header("🔒 Dashboard de Administración (Acceso Autorizado)")
    
    if "datos" in st.session_state and len(st.session_state.datos) > 0:
        df = pd.DataFrame(st.session_state.datos)
        
        st.subheader("📊 Registros de Clientes y Tabulador")
        df_display = df.drop(columns=["LinkMaps"], errors="ignore")
        st.dataframe(df_display)

        st.markdown("### 📥 Opciones de Exportación")
        
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            csv_masivo = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="🗺️ Descargar CSV para My Maps",
                data=csv_masivo,
                file_name="pines_masivos_intmex.csv",
                mime="text/csv",
                help="Sube este archivo en mymaps.google.com con la cuenta de la empresa."
            )
            
        with col_exp2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte_Operativo')
            excel_data = output.getvalue()
            
            st.download_button(
                label="📊 Descargar Reporte en Excel",
                data=excel_data,
                file_name=f"reporte_ejecutivo_intmex_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Descarga un reporte ordenado con todos los detalles del tabulador y operaciones."
            )
        
        st.markdown("---")
        if st.button("🗑️ Limpiar Base de Datos de Registros"):
            st.session_state.datos = []
            st.rerun()
    else:
        st.info("No hay registros guardados todavía.")
else:
    if admin_pass != "":
        st.sidebar.error("Contraseña incorrecta. El dashboard permanece oculto.")
