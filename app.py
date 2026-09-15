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

# Inicializar todos los estados de sesión necesarios para evitar que se borren los datos
if "modo_firma" not in st.session_state:
    st.session_state.modo_firma = False
if "firma_guardada" not in st.session_state:
    st.session_state.firma_guardada = False

if "modo_camara" not in st.session_state:
    st.session_state.modo_camara = False
if "foto_guardada" not in st.session_state:
    st.session_state.foto_guardada = False
if "datos_foto_buffer" not in st.session_state:
    st.session_state.datos_foto_buffer = None

if "tipo_evidencia" not in st.session_state:
    st.session_state.tipo_evidencia = "Seleccione"

# Inicializar valores del formulario en session_state
defaults = {
    "num_ruta": "",
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
    "agotados": ""
}

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

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
        if st.button("✅ Aceptar Firma"):
            if canvas_result.image_data is not None:
                st.session_state.firma_guardada = True
                st.session_state.modo_firma = False
                st.success("¡Firma capturada correctamente!")
                st.rerun()
            else:
                st.warning("Por favor, realice una firma antes de aceptar.")
    with col_f2:
        if st.button("❌ Cancelar Firma"):
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
            if st.button("✅ Usar esta Foto"):
                st.session_state.datos_foto_buffer = foto_capturada
                st.session_state.foto_guardada = True
                st.session_state.modo_camara = False
                st.success("¡Foto de fachada guardada correctamente!")
                st.rerun()
    with col_c2:
        if st.button("❌ Cancelar Cámara"):
            st.session_state.modo_camara = False
            st.rerun()

else:
    # ---------------------------------------------------------
    # 4. CAPTURA DE UBICACIÓN GPS REAL
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
    # 5. FORMULARIO DE REGISTRO CON RETENCIÓN DE DATOS
    # ---------------------------------------------------------
    st.subheader("📝 Registro de Nuevo Cliente y Tabulador")

    with st.form("form_registro_cliente"):
        st.markdown("### 📌 Datos de Ruta y Asesor")
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            num_ruta = st.text_input("Número de Ruta", value=st.session_state.num_ruta)
        with col_r2:
            nombre_asesor = st.text_input("Nombre del Asesor", value=st.session_state.nombre_asesor)

        st.markdown("### 📌 Datos Generales del Cliente")
        nombre_cliente = st.text_input("Nombre del Cliente", value=st.session_state.nombre_cliente)
        telefono = st.text_input("Teléfono", value=st.session_state.telefono)
        quien_recibe = st.text_input("Nombre de quien recibe", value=st.session_state.quien_recibe)
        notas = st.text_area("Notas o servicio realizado", value=st.session_state.notas)
        
        st.divider()
        st.markdown("### 📊 Tabulador de Supervisión (Obligatorio)")
        
        col1, col2 = st.columns(2)
        with col1:
            opts_tipo = ["Seleccione", "A", "B", "C"]
            idx_tipo = opts_tipo.index(st.session_state.tipo_cte) if st.session_state.tipo_cte in opts_tipo else 0
            tipo_cte = st.selectbox("Tipo Cte", opts_tipo, index=idx_tipo)

            opts_visi = ["Seleccione", "✓ (Sí)", "X (No)"]
            idx_visi = opts_visi.index(st.session_state.visibilidad) if st.session_state.visibilidad in opts_visi else 0
            visibilidad = st.selectbox("Visibilidad", opts_visi, index=idx_visi)

            opts_acce = ["Seleccione", "✓ (Sí)", "X (No)"]
            idx_acce = opts_acce.index(st.session_state.accesibilidad) if st.session_state.accesibilidad in opts_acce else 0
            accesibilidad = st.selectbox("Accesibilidad", opts_acce, index=idx_acce)
        
        with col2:
            opts_comp = ["Seleccione", "✓ (Sí)", "X (No)"]
            idx_comp = opts_comp.index(st.session_state.comprador) if st.session_state.comprador in opts_comp else 0
            comprador = st.selectbox("Comprador", opts_comp, index=idx_comp)

            opts_promo = ["Seleccione", "✓ (Sí)", "X (No)"]
            idx_promo = opts_promo.index(st.session_state.promo_seleccion) if st.session_state.promo_seleccion in opts_promo else 0
            promo_seleccion = st.selectbox("Promo", opts_promo, index=idx_promo)

        agotados = st.text_input("Agotados (Indicar SKU o Escribir 'Ninguno')", value=st.session_state.agotados)

        submitted = st.form_submit_button("Registrar Cliente")

    st.divider()

    # ---------------------------------------------------------
    # 6. CAMPO DINÁMICO DE PROMO FUERA DEL FORMULARIO
    # ---------------------------------------------------------
    st.markdown("### 🎯 Detalle de Promoción")
    opciones_promo = ["Seleccione", "✓ (Sí)", "X (No)"]
    
    # Sincronizamos el selector dinámico con el state global
    idx_sel_dinamico = opciones_promo.index(st.session_state.promo_seleccion) if st.session_state.promo_seleccion in opciones_promo else 0
    promo_seleccion_dinamica = st.selectbox(
        "¿Se aplicó o impactó alguna Promo?",
        opciones_promo,
        index=idx_sel_dinamico,
        key="selector_promo_dinamico"
    )
    # Actualizamos el estado general de la promo
    st.session_state.promo_seleccion = promo_seleccion_dinamica

    desc_promo = ""
    if st.session_state.promo_seleccion == "✓ (Sí)":
        desc_promo = st.text_area("📝 Escriba la descripción de la promo impactada (Obligatorio)", value=st.session_state.desc_promo)
        st.session_state.desc_promo = desc_promo

    st.divider()
    
    # ---------------------------------------------------------
    # 7. SELECCIÓN DE EVIDENCIA OBLIGATORIA
    # ---------------------------------------------------------
    st.markdown("### 📸 Evidencia Obligatoria")
    
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
        if not st.session_state.firma_guardada:
            if st.button("✍️ Abrir Lienzo para Firmar"):
                # Capturamos todos los textos actuales en session_state antes de salir al lienzo
                st.session_state.num_ruta = num_ruta
                st.session_state.nombre_asesor = nombre_asesor
                st.session_state.nombre_cliente = nombre_cliente
                st.session_state.telefono = telefono
                st.session_state.quien_recibe = quien_recibe
                st.session_state.notas = notas
                st.session_state.tipo_cte = tipo_cte
                st.session_state.visibilidad = visibilidad
                st.session_state.accesibilidad = accesibilidad
                st.session_state.comprador = comprador
                st.session_state.agotados = agotados
                
                st.session_state.modo_firma = True
                st.rerun()
        else:
            st.success("✅ Firma registrada y lista para el envío.")
            if st.button("🔄 Cambiar / Volver a firmar"):
                st.session_state.firma_guardada = False
                st.session_state.modo_firma = True
                st.rerun()

    elif st.session_state.tipo_evidencia == "Foto de la Fachada (Cámara trasera)":
        st.markdown("---")
        if not st.session_state.foto_guardada:
            if st.button("📷 Abrir Cámara para Fachada"):
                # Capturamos todos los textos actuales en session_state antes de salir a la cámara
                st.session_state.num_ruta = num_ruta
                st.session_state.nombre_asesor = nombre_asesor
                st.session_state.nombre_cliente = nombre_cliente
                st.session_state.telefono = telefono
                st.session_state.quien_recibe = quien_recibe
                st.session_state.notas = notas
                st.session_state.tipo_cte = tipo_cte
                st.session_state.visibilidad = visibilidad
                st.session_state.accesibilidad = accesibilidad
                st.session_state.comprador = comprador
                st.session_state.agotados = agotados

                st.session_state.modo_camara = True
                st.rerun()
        else:
            st.success("✅ Foto de fachada capturada y lista.")
            if st.button("🔄 Tomar otra foto"):
                st.session_state.foto_guardada = False
                st.session_state.modo_camara = True
                st.rerun()

    # ---------------------------------------------------------
    # 8. PROCESO DE VALIDACIÓN AL ENVIAR EL FORMULARIO
    # ---------------------------------------------------------
    if submitted:
        evidencia_valida = False
        desc_evidencia = "Sin evidencia"

        if st.session_state.tipo_evidencia == "Seleccione":
            st.error("⚠️ Debe seleccionar un tipo de evidencia obligatoria (Firma o Foto).")
        elif st.session_state.tipo_evidencia == "Firma del Cliente" and not st.session_state.firma_guardada:
            st.error("⚠️ Debe capturar la firma del cliente usando el botón de lienzo.")
        elif st.session_state.tipo_evidencia == "Foto de la Fachada (Cámara trasera)" and not st.session_state.foto_guardada:
            st.error("⚠️ Debe tomar la foto de la fachada para completar el registro.")
        else:
            evidencia_valida = True
            if st.session_state.tipo_evidencia == "Firma del Cliente":
                desc_evidencia = "Firma capturada en lienzo"
            else:
                desc_evidencia = "Foto de fachada capturada"

        if not num_ruta or not nombre_asesor:
            st.error("⚠️ Complete el Número de Ruta y el Nombre del Asesor.")
        elif not nombre_cliente or not quien_recibe:
            st.error("⚠️ Complete el Nombre del Cliente y el Nombre de quien recibe.")
        elif tipo_cte == "Seleccione" or visibilidad == "Seleccione" or accesibilidad == "Seleccione" or comprador == "Seleccione":
            st.error("⚠️ Debe completar los campos del Tabulador de Supervisión.")
        elif st.session_state.promo_seleccion == "Seleccione":
            st.error("⚠️ Indique si hubo Promo o no en la sección de Detalle de Promoción.")
        elif st.session_state.promo_seleccion == "✓ (Sí)" and not desc_promo:
            st.error("⚠️ Indique la descripción de la promo impactada.")
        elif not agotados:
            st.error("⚠️ El campo de Agotados es obligatorio (indique SKU o escriba 'Ninguno').")
        elif lat_real == 0.0 or lon_real == 0.0:
            st.error("⚠️ No se ha podido capturar la ubicación GPS. Autorice el acceso en el botón superior.")
        elif evidencia_valida:
            link_maps = f"https://www.google.com/maps/search/?api=1&query={lat_real},{lon_real}"
            
            # Texto formal para el reporte
            texto_promo_final = f"Sí - {desc_promo}" if st.session_state.promo_seleccion == "✓ (Sí)" else "No"

            nuevo_registro = {
                "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Ruta": num_ruta,
                "Asesor": nombre_asesor,
                "Cliente": nombre_cliente,
                "Teléfono": telefono,
                "Quien Recibe": quien_recibe,
                "Tipo Cte": tipo_cte,
                "Visibilidad": visibilidad,
                "Accesibilidad": accesibilidad,
                "Comprador": comprador,
                "Promo": texto_promo_final,
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
            
            # Limpiar estados generales y del formulario tras el éxito
            st.session_state.firma_guardada = False
            st.session_state.foto_guardada = False
            st.session_state.datos_foto_buffer = None
            st.session_state.tipo_evidencia = "Seleccione"
            for k in defaults:
                st.session_state[k] = defaults[k]
            
            st.success("✅ ¡Cliente registrado con éxito y tabulador completado!")
            st.rerun()

# ---------------------------------------------------------
# 9. DASHBOARD EXCLUSIVO PARA ADMINISTRADORES
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
