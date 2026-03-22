import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
import folium
from streamlit_folium import folium_static

# Configuración Novage
st.set_page_config(page_title="CORRECTOR DE IMÁGENES NOVAGE", layout="wide")

# CSS Look Novage con fondo de transparencia
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }
    .stAlert { background-color: #1f1906; border: 1px solid #ffd33d; color: #ffd33d; border-radius: 10px; }
    
    /* Cuadrícula de transparencia para el visor */
    .leaflet-container {
        background-image: linear-gradient(45deg, #2b2b2b 25%, transparent 25%), linear-gradient(-45deg, #2b2b2b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2b2b2b 75%), linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        background-color: #1a1a1a !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# SIDEBAR
st.sidebar.title("CORRECTOR NOVAGE")
archivo = st.sidebar.file_uploader("Cargar PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    
    st.sidebar.markdown("### Paso 2: Ajusta la corrección")
    dpi_val = st.sidebar.number_input("DPI Original", value=300)
    umbral = st.sidebar.slider("Sensibilidad", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    # Lógica de procesamiento
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    if not st.session_state.procesado:
        # Modo detección (Magenta)
        if np.any((a > 0) & (a < 255)):
            st.sidebar.warning("⚠️ Tiene semitransparencias.")
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        # Modo resultado limpio
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Botón de Descarga con formato de nombre solicitado
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("❌ PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR INTERACTIVO
    st.subheader("Visor de Precisión")
    st.caption("🖱️ RUEDITA: Zoom | 👆 CLIC: Arrastrar imagen")
    
    width, height = img_visor.size
    img_byte_arr = io.BytesIO()
    img_visor.save(img_byte_arr, format='PNG')
    # Aquí está la corrección del error base64
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    img_url = f"data:image/png;base64,{img_b64}"

    # Crear el visor tipo mapa para zoom infinito
    m = folium.Map(location=[height/2, width/2], zoom_start=1, crs=folium.CRS.Simple, tiles=None)
    folium.RasterLayer(
        image=img_url,
        bounds=[[0, 0], [height, width]],
        opacity=1
    ).add_to(m)
    m.fit_bounds([[0, 0], [height, width]])
    
    folium_static(m, width=1000, height=600)

else:
    st.session_state.procesado = False
    st.info("Sube una imagen para comenzar.")
