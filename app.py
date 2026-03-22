import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de página
st.set_page_config(page_title="SEMITRANSPARENCIAS STRATEGIA INK", layout="wide")

# CSS Look Novage y Visor Pro
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }
    .status-box {
        padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 15px; border: 1px solid;
        display: flex; align-items: center; justify-content: center;
    }
    .status-warning { background-color: #1f1906; color: #ffd33d; border-color: #ffd33d; }
    .status-success { background-color: #061f10; color: #3df18d; border-color: #3df18d; }
    
    /* Contenedor del Visor */
    #canvas-container {
        width: 100%; height: 650px; border: 1px solid #30363d; border-radius: 10px;
        overflow: hidden; background-color: #1a1a1a; cursor: grab;
        background-image: linear-gradient(45deg, #2b2b2b 25%, transparent 25%), linear-gradient(-45deg, #2b2b2b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2b2b2b 75%), linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);
        background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    }
    #canvas-container:active { cursor: grabbing; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# SIDEBAR
st.sidebar.title("CORRECTOR STRATEGIA INK")
archivo = st.sidebar.file_uploader("Cargar PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # MENSAJE DE ESTADO (Debajo del cargador)
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.markdown('<div class="status-box status-warning">⚠️ Tiene semitransparencias.</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-box status-success">✅ Limpio (sin semitransparencias).</div>', unsafe_allow_html=True)

    st.sidebar.markdown("### Paso 2: Ajusta la corrección")
    dpi_val = st.sidebar.number_input("DPI Original", value=300)
    umbral = st.sidebar.slider("Sensibilidad", 1, 254, 45)
    
    if st.sidebar.button("APLICAR CORRECCIÓN"):
        st.session_state.procesado = True

    if not st.session_state.procesado:
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Descarga
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("❌ PROBAR OTRO VALOR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR INTERACTIVO JS (Sin Folium, sin errores)
    st.subheader("Visor de Precisión")
    st.caption("Ruedita: Zoom | Clic Izquierdo: Mover")
    
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html_visor = f"""
    <div id="canvas-container">
        <img id="zoom-img" src="data:image/png;base64,{img_str}" style="transform-origin: 0 0; cursor: grab; width: 100%;">
    </div>
    <script>
        const container = document.getElementById('canvas-container');
        const img = document.getElementById('zoom-img');
        let scale = 1, panning = false, pointX = 0, pointY = 0, start = {{ x: 0, y: 0 }};

        container.onwheel = (e) => {{
            e.preventDefault();
            var xs = (e.clientX - pointX) / scale, ys = (e.clientY - pointY) / scale, delta = -e.deltaY;
            (delta > 0) ? (scale *= 1.2) : (scale /= 1.2);
            if (scale < 1) scale = 1; if (scale > 20) scale = 20;
            pointX = e.clientX - xs * scale; pointY = e.clientY - ys * scale;
            img.style.transform = `translate(${{pointX}}px, ${{pointY}}px) scale(${{scale}})`;
        }}
        container.onmousedown = (e) => {{ e.preventDefault(); start = {{ x: e.clientX - pointX, y: e.clientY - pointY }}; panning = true; }};
        container.onmouseup = () => {{ panning = false; }};
        container.onmousemove = (e) => {{
            if (!panning) return;
            pointX = (e.clientX - start.x); pointY = (e.clientY - start.y);
            img.style.transform = `translate(${{pointX}}px, ${{pointY}}px) scale(${{scale}})`;
        }};
    </script>
    """
    st.components.v1.html(html_visor, height=660)

else:
    st.session_state.procesado = False
    st.info("SubI una imagen para comenzar.")
