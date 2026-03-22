import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de página
st.set_page_config(page_title="Corrector de Imágenes Novage", layout="wide")

# CSS Look Novage exacto y funcional
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    
    /* Botones Amarillos */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }
    
    /* Estilo de la imagen para que sea interactiva */
    .img-container {
        cursor: grab;
        overflow: auto;
        border: 2px solid #30363d;
        border-radius: 10px;
        background-image: linear-gradient(45deg, #1d2127 25%, transparent 25%), linear-gradient(-45deg, #1d2127 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #1d2127 75%), linear-gradient(-45deg, transparent 75%, #1d2127 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    }
    .img-container:active { cursor: grabbing; }
    
    .stAlert { background-color: #1f1906; border: 1px solid #ffd33d; color: #ffd33d; border-radius: 10px; }
    h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

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
    dpi_val = st.sidebar.number_input("DPI Original del Archivo", value=300)
    umbral = st.sidebar.slider("Sensibilidad de corrección", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    if st.session_state.procesado:
        # Procesamiento de limpieza
        r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        
        # Preparar Descarga
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        
        st.sidebar.download_button(
            label="📥 DESCARGAR RESULTADO LIMPIO",
            data=buf.getvalue(),
            file_name=f"P000 | {nombre_base}.PNG",
            mime="image/png"
        )
        
        if st.sidebar.button("❌ BORRAR Y PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # CUERPO PRINCIPAL - VISOR
    st.subheader("Visor de Corrección")
    
    if not st.session_state.procesado:
        # Mostrar imagen con bordes magenta
        vis = datos.copy()
        vis[(datos[:,:,3] > 0) & (datos[:,:,3] < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
        st.caption("🔍 Visualizando bordes detectados (Magenta)")
    else:
        img_visor = img_final
        st.caption("✅ Visualizando resultado corregido")

    # VISOR CON ZOOM Y MANITO (Usa el componente nativo que es más estable)
    st.image(img_visor, use_container_width=True)
    st.info("Podes hacer clic derecho en la imagen y abrirla en una pestaña nueva para ver el zoom al 1000% o usar el zoom nativo de tu navegador (Ctrl + Ruedita).")

else:
    st.session_state.procesado = False
    st.info("Subí un archivo PNG para empezar.")
