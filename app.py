import streamlit as st

st.markdown(
    """
    <script>
    const link = document.createElement('link');
    link.rel = 'manifest';
    link.href = '/app/static/manifest.json';
    document.head.appendChild(link);
    </script>
    """,
    unsafe_allow_html=True,
)
from datetime import datetime
from io import BytesIO
import folium
from folium.plugins import HeatMap
import numpy as np
import pandas as pd
import streamlit as st
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from streamlit_drawable_canvas import st_canvas
from streamlit_folium import st_folium

# --- CONFIGURACIÓN DE PÁGINA Y PWA ---
st.set_page_config(
    page_title="Supervisión de Repartos y Clientes",
    page_icon="📍",
    layout="wide",  # Layout ancho ideal para dashboards gerenciales
    initial_sidebar_state="collapsed",
)

pwa_code = """
<link rel="manifest" href="data:application/manifest+json;charset=utf-8,{
  'name': 'Supervisión de Repartos',
  'short_name': 'RepartosPro',
  'start_url': '/',
  'display': 'standalone',
  'background_color': '#f8f9fa',
  'theme_color': '#0066cc',
  'icons': [
    {
      'src': 'https://cdn-icons-png.flaticon.com/512/854/854878.png',
      'sizes': '512x512',
      'type': 'image/png'
    }
  ]
}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
"""
st.markdown(pwa_code, unsafe_allow_html=True)


# --- BASE DE DATOS (Preparada para SQLite local o en la nube tipo PostgreSQL/MySQL) ---
DATABASE_URL = "sqlite:///repartos.db"

Engine = create_engine(DATABASE_URL)
Base = declarative_base()


class Parada(Base):
  __tablename__ = "paradas"
  id = Column(Integer, primary_key=True, autoincrement=True)
  dia_semana = Column(String(20), nullable=False)
  nombre_ruta = Column(String(50), nullable=False)
  nombre_pdv = Column(String(100), nullable=False)
  telefono = Column(String(20), nullable=False)
  encargado = Column(String(100))
  lat = Column(Float, nullable=False)
  lon = Column(Float, nullable=False)
  comentarios = Column(Text)
  tiene_firma = Column(String(5))
  foto_fachada = Column(LargeBinary, nullable=True)
  fecha_hora = Column(DateTime, default=datetime.now)


Base.metadata.create_all(Engine)
SessionLocal = sessionmaker(bind=Engine)


# --- CÁLCULO DE DISTANCIA (GEOCERCAS) ---
def calcular_distancia_metros(lat1, lon1, lat2, lon2):
  """Calcula la distancia en metros entre dos puntos geográficos (Fórmula Haversine)."""
  R = 6371000  # Radio de la tierra en metros
  phi1, phi2 = np.radians(lat1), np.radians(lat2)
  d_phi = np.radians(lat2 - lat1)
  d_lambda = np.radians(lon2 - lon1)

  a = (
      np.sin(d_phi / 2) ** 2
      + np.cos(phi1) * np.cos(phi2) * np.sin(d_lambda / 2) ** 2
  )
  c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
  return R * c


# --- INTERFAZ PRINCIPAL ---
st.title("📍 Sistema Integral de Control y Supervisión de Rutas")

# Pestañas principales
pestana_registro, pestana_dashboard = st.tabs(
    ["➕ Registrar Visita (App Repartidores)", "📊 Dashboard & Panel Gerencial"]
)

# ==========================================
# 1. PESTAÑA: REGISTRO DE VISITAS (MÓVIL / CAMPO)
# ==========================================
with pestana_registro:
  st.subheader("📱 Registro de Visita en Ruta")
  st.info(
      "Modo operativo activo. El teléfono y una validación (firma o foto) son"
      " obligatorios."
  )

  with st.form("form_parada"):
    col1, col2 = st.columns(2)
    with col1:
      dia_semana = st.selectbox(
          "Día de la Semana",
          [
              "Lunes",
              "Martes",
              "Miércoles",
              "Jueves",
              "Viernes",
              "Sábado",
              "Domingo",
          ],
      )
    with col2:
      nombre_ruta = st.text_input(
          "Nombre de la Ruta", placeholder="Ej. Ruta Norte"
      )

    st.markdown("---")
    nombre_pdv = st.text_input("Nombre del Negocio / Cliente *")
    telefono = st.text_input(
        "Número de Teléfono del Cliente *",
        placeholder="Ej. 6641234567",
        max_chars=15,
    )
    encargado = st.text_input("Nombre del Encargado (Opcional)")

    st.write("📍 **Coordenadas de ubicación (GPS):**")
    lat = st.number_input(
        "Latitud", value=32.5149, format="%.6f"
    )  # Coordenada base Tijuana/México por defecto
    lon = st.number_input("Longitud", value=-117.0382, format="%.6f")

    comentarios = st.text_area("Notas / Comentarios de la visita")
    submit_button = st.form_submit_button(
        label="Guardar Registro 📌", use_container_width=True
    )

  st.markdown("---")
  st.subheader("✍️ Validación de Visita (Firma o Foto obligatoria)")

  st.write("**Firma Digital del Cliente:**")
  canvas_result = st_canvas(
      fill_color="rgba(255, 165, 0, 0.3)",
      stroke_width=2,
      stroke_color="#000000",
      background_color="#FFFFFF",
      height=140,
      width=330,
      drawing_mode="freedraw",
      key="canvas_firma",
  )

  st.write("---")
  st.write("**O tomar Foto de la Fachada:**")
  foto_fachada_file = st.camera_input("Toma una foto del negocio")

  if submit_button:
    tiene_firma = (
        False
        if canvas_result.json_data is None
        or len(canvas_result.json_data["objects"]) == 0
        else True
    )
    tiene_foto = True if foto_fachada_file is not None else False

    if nombre_pdv.strip() == "" or nombre_ruta.strip() == "":
      st.error("⚠️ El nombre del cliente y la ruta son obligatorios.")
    elif telefono.strip() == "" or not telefono.isdigit():
      st.error(
          "⚠️ El **Número de Teléfono** es obligatorio y debe contener solo"
          " dígitos."
      )
    elif not tiene_firma and not tiene_foto:
      st.error(
          "❌ Falta validación: Debes capturar la **Firma del Cliente** o la"
          " **Foto de la Fachada**."
      )
    else:
      foto_bytes = foto_fachada_file.getvalue() if tiene_foto else None

      try:
        db = SessionLocal()
        nueva_parada = Parada(
            dia_semana=dia_semana,
            nombre_ruta=nombre_ruta,
            nombre_pdv=nombre_pdv,
            telefono=telefono,
            encargado=encargado,
            lat=lat,
            lon=lon,
            comentarios=comentarios,
            tiene_firma="Sí" if tiene_firma else "No",
            foto_fachada=foto_bytes,
        )
        db.add(nueva_parada)
        db.commit()
        db.close()
        st.success(f"✅ ¡Visita de '{nombre_pdv}' registrada correctamente!")
      except Exception as e:
        st.error(f"Error al guardar: {e}")


# ==========================================
# 2. PESTAÑA: DASHBOARD & PANEL GERENCIAL
# ==========================================
with pestana_dashboard:
  st.subheader("🔐 Panel de Control y Supervisión Gerencial")

  PASSWORD_ADMIN = "Admin123"

  if "auth_admin" not in st.session_state:
    st.session_state.auth_admin = False

  if not st.session_state.auth_admin:
    with st.form("form_login"):
      st.info(
          "Introduce la contraseña de supervisor/administrador para acceder al"
          " dashboard."
      )
      password_ingresada = st.text_input("Contraseña", type="password")
      btn_login = st.form_submit_button("Ingresar al Dashboard")

      if btn_login:
        if password_ingresada == PASSWORD_ADMIN:
          st.session_state.auth_admin = True
          st.rerun()
        else:
          st.error("❌ Contraseña incorrecta.")
  else:
    col_logout, col_space = st.columns([1, 4])
    with col_logout:
      if st.button("Cerrar Sesión"):
        st.session_state.auth_admin = False
        st.rerun()

    st.success("🔓 Sesión de Supervisor Activa")
    st.markdown("---")

    db = SessionLocal()
    paradas_db = db.query(Parada).all()
    db.close()

    if not paradas_db:
      st.warning(
          "Aún no hay registros de visitas guardados en la base de datos."
      )
    else:
      # Convertir a DataFrame de Pandas para analíticas y descargas
      data_rows = []
      for p in paradas_db:
        data_rows.append({
            "ID": p.id,
            "Fecha/Hora": p.fecha_hora,
            "Día": p.dia_semana,
            "Ruta": p.nombre_ruta,
            "Cliente": p.nombre_pdv,
            "Teléfono": p.telefono,
            "Encargado": p.encargado or "N/D",
            "Latitud": p.lat,
            "Longitud": p.lon,
            "Firma": p.tiene_firma,
            "Tiene Foto": "Sí" if p.foto_fachada else "No",
            "Comentarios": p.comentarios or "",
        })
      df_all = pd.DataFrame(data_rows)

      # --- TARJETAS DE MÉTRICAS (KPIs) ---
      kpi1, kpi2, kpi3, kpi4 = st.columns(4)
      with kpi1:
        st.metric(
            label="Total Visitas Registradas", value=len(df_all)
        )
      with kpi2:
        st.metric(
            label="Rutas Activas", value=df_all["Ruta"].nunique()
        )
      with kpi3:
        st.metric(
            label="Clientes Únicos", value=df_all["Cliente"].nunique()
        )
      with kpi4:
        validadas_firma = len(df_all[df_all["Firma"] == "Sí"])
        st.metric(label="Visitas con Firma Digital", value=validadas_firma)

      st.markdown("---")

      # --- SECCIÓN DE DESCARGA DE ARCHIVOS (EXCEL / CSV) ---
      st.subheader("📥 Exportación de Base de Datos y Reportes")
      col_dl1, col_dl2 = st.columns(2)

      with col_dl1:
        # Exportar a Excel profesional
        output_excel = BytesIO()
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
          df_all.to_excel(writer, index=False, sheet_name="Visitas_Repartos")
        excel_data = output_excel.getvalue()

        st.download_button(
            label="📊 Descargar Base de Datos Completa (.XLSX)",
            data=excel_data,
            file_name=f"Reporte_Repartos_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

      with col_dl2:
        csv_data = df_all.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Descargar Reporte en Formato CSV",
            data=csv_data,
            file_name=f"Reporte_Repartos_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

      st.markdown("---")

      # --- FILTROS Y CONFIGURACIÓN DE GEOCERCAS ---
      st.subheader("🗺️ Monitoreo de Ubicaciones y Geocercas")

      col_f1, col_f2, col_f3 = st.columns(3)
      with col_f1:
        filtro_dia = st.selectbox(
            "Filtrar por Día", ["Todos"] + list(df_all["Día"].unique())
        )
      with col_f2:
        filtro_ruta = st.selectbox(
            "Filtrar por Ruta", ["Todos"] + list(df_all["Ruta"].unique())
        )
      with col_f3:
        # Módulo de Geocerca: Definir punto central de referencia de bodega o almacén
        st.write("**Configurar Geocerca de Referencia**")
        activar_geocerca = st.checkbox("Validar radio autorizado (Geocerca)")

      df_filtrado = df_all.copy()
      if filtro_dia != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Día"] == filtro_dia]
      if filtro_ruta != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Ruta"] == filtro_ruta]

      # Si se activa geocerca, evaluamos distancia máxima (ej. 15 km desde centro de operaciones)
      if activar_geocerca:
        c_lat = st.number_input(
            "Latitud del Centro de Operaciones / Bodega", value=32.5149
        )
        c_lon = st.number_input(
            "Longitud del Centro de Operaciones / Bodega", value=-117.0382
        )
        radio_km = st.slider("Radio autorizado (Kilómetros)", 1, 50, 15)

        # Calcular distancias
        df_filtrado["Distancia_Km"] = df_filtrado.apply(
            lambda row: calcular_distancia_metros(
                c_lat, c_lon, row["Latitud"], row["Longitud"]
            )
            / 1000.0,
            axis=1,
        )
        # Filtrar los que están fuera de rango
        fuera_rango = df_filtrado[df_filtrado["Distancia_Km"] > radio_km]
        if not fuera_rango.empty:
          st.warning(
              f"⚠️ Hay {len(df_filtrado[df_filtrado['Distancia_Km'] > radio_km])}"
              f" visitas registradas **fuera de la geocerca** configurada."
          )

      # --- MAPA INTERACTIVO DE SUPERVISIÓN ---
      if df_filtrado.empty:
        st.info("No hay datos para mostrar con los filtros seleccionados.")
      else:
        mapa_centro = [
            df_filtrado["Latitud"].mean(),
            df_filtrado["Longitud"].mean(),
        ]
        mapa = folium.Map(location=mapa_centro, zoom_start=12)

        # Si hay geocerca, dibujar círculo de referencia en el mapa
        if activar_geocerca:
          folium.Circle(
              location=[c_lat, c_lon],
              radius=radio_km * 1000,
              color="blue",
              fill=True,
              fill_opacity=0.1,
              popup="Zona Geocerca Autorizada",
          ).add_to(mapa)

        for _, row in df_filtrado.iterrows():
          popup_text = f"""
                    <b>Cliente:</b> {row['Cliente']}<br>
                    <b>Tel:</b> {row['Teléfono']}<br>
                    <b>Ruta:</b> {row['Ruta']}<br>
                    <b>Día:</b> {row['Día']}<br>
                    <b>Hora:</b> {row['Fecha/Hora']}
                    """
          folium.Marker(
              [row["Latitud"], row["Longitud"]],
              popup=folium.Popup(popup_text, max_width=300),
              tooltip=row["Cliente"],
              icon=folium.Icon(color="green", icon="store", prefix="fa"),
          ).add_to(mapa)

        st_folium(mapa, width=1100, height=500)

      st.markdown("---")

      # --- TABLA Y EVIDENCIAS DETALLADAS ---
      st.subheader("📋 Detalle de Visitas y Fotografías de Fachada")
      st.dataframe(
          df_filtrado[
              [
                  "Fecha/Hora",
                  "Día",
                  "Ruta",
                  "Cliente",
                  "Teléfono",
                  "Encargado",
                  "Firma",
                  "Tiene Foto",
                  "Comentarios",
              ]
          ],
          use_container_width=True,
      )

      # Visualizador individual de fotos y evidencias
      st.write("### 🔍 Inspección de Evidencias por Cliente")
      cliente_seleccionado = st.selectbox(
          "Selecciona un cliente para ver su evidencia fotográfica:",
          df_filtrado["Cliente"].unique(),
      )

      if cliente_seleccionado:
        visita_sel = (
            db.query(Parada)
            .filter(Parada.nombre_pdv == cliente_seleccionado)
            .first()
        )
        if visita_sel:
          col_ev1, col_ev2 = st.columns(2)
          with col_ev1:
            st.write(f"**Negocio:** {visita_sel.nombre_pdv}")
            st.write(f"**Teléfono:** {visita_sel.telefono}")
            st.write(f"**Ruta:** {visita_sel.nombre_ruta}")
            st.write(f"**Encargado:** {visita_sel.encargado or 'No especificado'}")
            st.write(f"**Fecha y Hora:** {visita_sel.fecha_hora}")
            st.write(f"**Notas:** {visita_sel.comentarios or 'Sin notas'}")
          with col_ev2:
            if visita_sel.foto_fachada:
              st.write("**📸 Fotografía de Fachada Registrada:**")
              st.image(visita_sel.foto_fachada, width=300)
            else:
              st.info(
                  "ℹ️ Esta visita fue validada por medio de **Firma Digital** del"
                  " cliente."
              )
