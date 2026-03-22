import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS PARA COPIAR LA ESTRUCTURA DE LA WEB
st.markdown("""
    <style>
    /* Reset total de márgenes */
    .main { overflow: hidden; }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
        max-width: 100% !important;
    }
    
    /* Sidebar Estilo Novage */
    [data-testid="stSidebar"] {
        background-color: #111418;
        min-width: 400px !important;
    }

    /* Botones de Función */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; border-radius: 6px !important; font-weight: bold !important;
        height: 3em; text-transform: uppercase; margin-bottom: 5px;
    }
    
    /* Botón Aplicar (Amarillo) */
    div.stButton > button:first-child { background-color: #d4ff00 !important; color: black !important; }
    
    /* Botón Descarga (Verde) */
    div.stDownloadButton > button { background-color: #24a148 !important; color: white !important; }
    
    /* Botones Secundarios */
    [data-testid="stSidebar"] button { border: 1px solid #30363d !important; }

    /* EL CONTENEDOR MAESTRO (Ajustado a medida Novage) */
    .mesa-trabajo {
        width: 100%;
        height: 94vh; /* Casi todo el alto del monitor */
        background-color: #0d1117;
        background-image: 
            linear-gradient(45deg, #161b22 25%, transparent 25%), 
            linear-gradient(-45deg, #161b22 25%, transparent 25%), 
            linear-gradient(45deg, transparent 75%, #161b22 75%), 
            linear-gradient(-45deg, transparent 75%, #161b22 75%);
        background-size: 20px 20px;
        background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
        border: 1px solid #30363d;
        border-radius: 4px;
        overflow: hidden;
    }
    
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False
if 'mostrar_original' not in st.session_state:
    st.session_state.mostrar_original = False

# BARRA LATERAL (Panel de Control Unificado)
st.sidebar.title("CORRECTOR STRATEGIA INK")
st.sidebar.markdown("---")

archivo = st.sidebar.file_uploader("Subir PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # Estado de la imagen
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.warning("⚠️ GHOST PIXELS DETECTADOS")
    else:
        st.sidebar.success("✅ IMAGEN LIMPIA")

    st.sidebar.markdown("### CONFIGURACIÓN")
    umbral = st.sidebar.slider("SENSIBILIDAD / UMBRAL", 1, 254, 128)
    dpi_val = st.sidebar.number_input("DPI SALIDA", value=300)
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("APLICAR"):
            st.session_state.procesado = True
    with col2:
        if st.button("RESETEAR"):
            st.session_state.procesado = False
            st.session_state.mostrar_original = False
            st.rerun()

    # NUEVAS FUNCIONES DE LA WEB EN EL SIDEBAR
    st.sidebar.markdown("---")
    st.sidebar.markdown("### HERRAMIENTAS")
    
    if st.sidebar.button("COMPARAR (ANTES/DESPUÉS)"):
        st.session_state.mostrar_original = not st.session_state.mostrar_original

    if st.session_state.procesado:
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        
        # Lógica de qué mostrar en el visor
        img_visor = img_orig if st.session_state.mostrar_original else img_final
        
        # Botón de Descarga PNG
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR PNG CORREGIDO", buf.getvalue(), nombre_descarga, "image/png")
    else:
        # Modo Visor de Ghost Pixels (Magenta)
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)

    # VISOR DE ALTA PRECISIÓN (OCUPA TODA LA DERECHA)
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html_visor = f"""
    <div class="mesa-trabajo" id="box">
        <canvas id="canvas"></canvas>
    </div>
    <script>
        const box = document.getElementById('box');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";

        let scale = 1, viewX = 0, viewY = 0, isPanning = false, startX, startY;

        function fit() {{
            canvas.width = box.clientWidth;
            canvas.height = box.clientHeight;
            if (img.width > 0) {{
                scale = Math.min(canvas.width / img.width, canvas.height / img.height) * 0.9;
                viewX = (canvas.width - img.width * scale) / 2;
                viewY = (canvas.height - img.height * scale) / 2;
                draw();
            }}
        }}

        img.onload = fit;
        window.onresize = fit;

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.save();
            ctx.translate(viewX, viewY);
            ctx.scale(scale, scale);
            ctx.drawImage(img, 0, 0);
            ctx.restore();
        }}

        canvas.onwheel = (e) => {{
            e.preventDefault();
            const zoom = e.deltaY > 0 ? 0.8 : 1.2;
            const mX = e.offsetX, mY = e.offsetY;
            viewX = mX - (mX - viewX) * zoom;
            viewY = mY - (mY - viewY) * zoom;
            scale *= zoom;
            draw();
        }};

        canvas.onmousedown = (e) => {{ isPanning = true; startX = e.offsetX - viewX; startY = e.offsetY - viewY; }};
        window.onmouseup = () => isPanning = false;
        canvas.onmousemove = (e) => {{
            if (!isPanning) return;
            viewX = e.offsetX - startX;
            viewY = e.offsetY - startY;
            draw();
        }};
    </script>
    """
    st.components.v1.html(html_visor, height=900, scrolling=False)

else:
    st.info("Sube una imagen para activar el panel de control.")
