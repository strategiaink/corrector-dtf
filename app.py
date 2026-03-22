import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de página
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide")

# CSS para branding Strategia Ink y limpieza visual
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    
    /* Botones Strategia Ink */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }

    /* Ocultar textos de límite de Streamlit */
    [data-testid="stFileUploadDropzone"] div div { display: none; }
    [data-testid="stFileUploadDropzone"]::before { content: "Arrastra tu archivo aquí o haz clic"; color: #888; }

    .status-box {
        padding: 12px; border-radius: 10px; font-weight: bold; margin-bottom: 15px; border: 1px solid;
        display: flex; align-items: center; justify-content: center; text-align: center;
    }
    .status-warning { background-color: #1f1906; color: #ffd33d; border-color: #ffd33d; }
    .status-success { background-color: #061f10; color: #3df18d; border-color: #3df18d; }
    
    #canvas-container {
        width: 100%; height: 750px; border: 1px solid #30363d; border-radius: 10px;
        overflow: hidden; background-color: #1a1a1a; position: relative;
    }
    #zoom-img { image-rendering: pixelated; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# BARRA LATERAL (SIDEBAR)
st.sidebar.title("CORRECTOR STRATEGIA INK")
st.sidebar.markdown("---")

# Cargador de archivos (Traducción completa)
archivo = st.sidebar.file_uploader("Subir imagen PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # Detección de Semitransparencias (Ghost Pixels)
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.markdown('<div class="status-box status-warning">⚠️ ATENCIÓN: Esta imagen tiene semitransparencias (Ghost Pixels).</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-box status-success">✅ IMAGEN LIMPIA: Sin halos ni semitransparencias.</div>', unsafe_allow_html=True)

    st.sidebar.markdown("### Configuración de Salida")
    dpi_val = st.sidebar.number_input("Resolución (DPI)", value=300)
    umbral = st.sidebar.slider("Umbral de Corte Alpha", 1, 254, 128, help="Define qué tan agresivo es el recorte de bordes.")
    
    if st.sidebar.button("EJECUTAR CORRECCIÓN v4.0"):
        st.session_state.procesado = True

    if not st.session_state.procesado:
        # Previsualización: Magenta resalta los problemas
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        # Aplicación de mejoras v4.0
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Nombre de archivo en MAYÚSCULAS según tus reglas
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("🔄 CORREGIR OTRA VEZ"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR DE ALTA PRECISIÓN
    st.subheader("Control de Calidad (Píxel Real)")
    st.caption("Usa la RUEDITA para Zoom y ARRASTRA para moverte por la imagen.")
    
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html_visor = f"""
    <div id="canvas-container">
        <img id="zoom-img" src="data:image/png;base64,{img_str}" style="transform-origin: 0 0; cursor: grab; position: absolute; width: 100%;">
    </div>
    <script>
        const container = document.getElementById('canvas-container');
        const img = document.getElementById('zoom-img');
        let scale = 1, panning = false, pointX = 0, pointY = 0, start = {{ x: 0, y: 0 }};

        container.onwheel = (e) => {{
            e.preventDefault();
            var xs = (e.clientX - pointX) / scale, ys = (e.clientY - pointY) / scale, delta = -e.deltaY;
            (delta > 0) ? (scale *= 1.4) : (scale /= 1.4);
            if (scale < 1) scale = 1; if (scale > 80) scale = 80;
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
    st.components.v1.html(html_visor, height=770)

else:
    st.session_state.procesado = False
    st.info("Sube un archivo PNG para iniciar el análisis de Strategia Ink.")
