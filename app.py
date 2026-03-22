import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
import folium
from streamlit_folium import folium_static

# Configuración Novage
st.set_page_config(page_title="CORRECTOR DE IMÁGENES NOVAGE", layout="wide")

# CSS Estilo Novage y Visor
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    
    /* Botones Amarillos */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }

    /* Mensajes de estado debajo del cargador */
    .status-box {
        padding: 10px;
        border-radius: 10px;
        font-weight: bold;
        margin-top: 10px;
        border: 1px solid;
        display: flex;
        align-items: center;
    }
    .status-warning { background-color: #1f1906; color: #ffd33d; border-color: #ffd33d; }
    .status-success { background-color: #061f10; color: #3df18d; border-color: #3df18d; }

    /* Visor con fondo de transparencia */
    .leaflet-container {
        background-image: linear-gradient(45deg, #2b2b2b 25%, transparent 25%), 
                          linear-gradient(-45deg, #2b2b2b 25%, transparent 25%), 
                          linear-gradient(45deg, transparent 75%, #2b2b2b 75%), 
                          linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        background-color: #1a1a1a !important;
        border: 1px solid #30363d !important;
        border-radius: 10px;
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
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # DETECCIÓN DE SEMITRANSPARENCIAS (Justo debajo del archivo)
    hay_semitransparencia = np.any((a > 0) & (a < 255))
    
    if hay_semitransparencia:
        st.sidebar.markdown('<div class="status-box status-warning">⚠️ Tiene semitransparencias.</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-box status-success">✅ Limpio (sin semitransparencias).</div>', unsafe_allow_html=True)

    st.sidebar.markdown("---")
    dpi_val = st.sidebar.number_input("DPI Original", value=300)
    umbral = st.sidebar.slider("Sensibilidad", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    if not st.session_state.procesado:
        # Muestra en Magenta para revisión
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        # Resultado final limpio
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Nombre en MAYÚSCULAS
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("❌ PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR DE PRECISIÓN (CORREGIDO)
    st.subheader("Visor de Precisión")
    st.caption("🖱️ RUEDITA: Zoom | 👆 CLIC IZQ: Mover imagen")
    
    w, h = img_visor.size
    img_byte_arr = io.BytesIO()
    img_visor.save(img_byte_arr, format='PNG')
    img_b64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    img_url = f"data:image/png;base64,{img_b64}"

    # Uso de ImageOverlay para evitar error de RasterLayer
    m = folium.Map(location=[h/2, w/2], zoom_start=1, crs="Simple", tiles=None)
    
    folium.raster_layers.ImageOverlay(
        url=img_url,
        bounds=[[0, 0], [h, w]],
        origin='upper'
    ).add_to(m)
    
    m.fit_bounds([[0, 0], [h, w]])
    folium_static(m, width=1100, height=650)

else:
    st.session_state.procesado = False
    st.info("Sube una imagen para comenzar.")
