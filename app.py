import streamlit as st
import numpy as np
from PIL import Image
import io
import folium
from streamlit_folium import folium_static

# Configuración Novage
st.set_page_config(page_title="Corrector de Imágenes Novage", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }
    .stAlert { background-color: #1f1906; border: 1px solid #ffd33d; color: #ffd33d; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# SIDEBAR
st.sidebar.title("Corrector Novage")
archivo = st.sidebar.file_uploader("Cargar PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    
    dpi_val = st.sidebar.number_input("DPI Original", value=300)
    umbral = st.sidebar.slider("Sensibilidad", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    # Lógica de procesamiento
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    if not st.session_state.procesado:
        # Modo detección (Magenta)
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        # Modo resultado limpio
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Botón de Descarga
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button("📥 DESCARGAR", buf.getvalue(), f"CORREGIDO_{archivo.name.upper()}", "image/png")
        
        if st.sidebar.button("❌ PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR INTERACTIVO (Misma página)
    st.subheader("Visor de Precisión")
    st.caption("Usa la RUEDITA para Zoom y ARRASTRA con el mouse para moverte.")
    
    # Convertir imagen para el visor de alta precisión
    width, height = img_visor.size
    img_byte_arr = io.BytesIO()
    img_visor.save(img_byte_arr, format='PNG')
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode()
    img_url = f"data:image/png;base64,{img_base64}"

    # Crear mapa Folium como visor de imágenes
    m = folium.Map(location=[height/2, width/2], zoom_start=1, crs=folium.CRS.Simple, tiles=None)
    folium.RasterLayer(
        image=img_url,
        bounds=[[0, 0], [height, width]],
        opacity=1,
        name="Imagen"
    ).add_to(m)
    m.fit_bounds([[0, 0], [height, width]])
    
    # Renderizar visor en la página
    folium_static(m, width=900, height=600)

else:
    st.info("Subí una imagen para empezar.")
