import streamlit as st
import numpy as np
from PIL import Image
import io
from streamlit_drawable_canvas import st_canvas

# Configuración de página
st.set_page_config(page_title="Corrector de Imágenes Novage", layout="wide")

# CSS Look Novage
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    .stButton > button { 
        width: 100%; background-color: #d4ff00; color: black; 
        font-weight: bold; border-radius: 8px; border: none; height: 3em;
    }
    .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00; color: black; 
        font-weight: bold; border-radius: 8px; border: none;
    }
    .stAlert { background-color: #1f1906; border: 1px solid #ffd33d; color: #ffd33d; border-radius: 10px; }
    p, label { color: #8b949e !important; }
    h1, h2, h3 { color: white !important; font-family: 'sans-serif'; }
    </style>
    """, unsafe_allow_html=True)

# Inicializar estados
if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# SIDEBAR
st.sidebar.title("Corrector de Imágenes Novage")
st.sidebar.caption("Elimina semitransparencias para impresión DTF")

st.sidebar.markdown("### Paso 1: Carga tu imagen (PNG)")
archivo = st.sidebar.file_uploader("Seleccionar archivo", type=["png"], key="subidor", label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    
    if np.any((datos[:,:,3] > 0) & (datos[:,:,3] < 255)):
        st.sidebar.warning("⚠️ Tiene semitransparencias.")

    st.sidebar.markdown("### Paso 2: Ajusta la corrección")
    dpi = st.sidebar.number_input("DPI Original del Archivo", value=300)
    umbral = st.sidebar.slider("Sensibilidad de corrección", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    if st.session_state.procesado:
        # Procesamiento
        r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_limpia = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        
        # Preparar Descarga
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        buf = io.BytesIO()
        img_limpia.save(buf, format="PNG", dpi=(dpi, dpi))
        
        st.sidebar.download_button(
            label="📥 DESCARGAR RESULTADO LIMPIO",
            data=buf.getvalue(),
            file_name=f"P000 | {nombre_base}.PNG",
            mime="image/png"
        )
        
        if st.sidebar.button("❌ BORRAR Y PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR INTERACTIVO
    st.subheader("Visor Interactivo")
    st.caption("🖱️ RUEDITA: Zoom | 👆 CLIC IZQ: Mover imagen (Manito)")
    
    # Imagen para mostrar (Magenta si no está procesado, Limpia si lo está)
    if not st.session_state.procesado:
        vis = datos.copy()
        vis[(datos[:,:,3] > 0) & (datos[:,:,3] < 255)] = [255, 0, 255, 255]
        img_display = Image.fromarray(vis)
    else:
        img_display = img_limpia

    # Canvas corregido para evitar el AttributeError
    st_canvas(
        background_image=img_display,
        height=600,
        width=800,
        drawing_mode="transform",
        display_toolbar=True,
        key="canvas_visor",
    )
else:
    st.session_state.procesado = False
    st.info("Subí un archivo PNG para empezar.")
