import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# 1. CONFIGURACIÓN DE PÁGINA PARA MÁXIMO ANCHO
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# 2. CSS AVANZADO PARA ELIMINAR LÍMITES DE STREAMLIT
st.markdown("""
    <style>
    /* Eliminar el padding superior y lateral de Streamlit para ganar espacio */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Estilo del Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        min-width: 380px !important;
    }

    /* Botones personalizados */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important;
        height: 3.5em; text-transform: uppercase;
    }

    /* Contenedor del Visor que usará el 90% del alto de la pantalla */
    .canvas-container {
        width: 100%;
        height: 85vh; 
        border: 2px solid #30363d;
        border-radius: 12px;
        overflow: hidden;
        background-color: #1a1a1a;
        background-image: radial-gradient(#333 1px, transparent 1px);
        background-size: 20px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

# BARRA LATERAL
st.sidebar.title("CORRECTOR STRATEGIA INK")
st.sidebar.markdown("---")

archivo = st.sidebar.file_uploader("Subir imagen PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # Detección de Ghost Pixels
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.error("⚠️ ATENCIÓN: Ghost Pixels detectados.")
    else:
        st.sidebar.success("✅ IMAGEN LIMPIA.")

    st.sidebar.markdown("### CONFIGURACIÓN")
    dpi_val = st.sidebar.number_input("RESOLUCIÓN (DPI)", value=300)
    umbral = st.sidebar.slider("UMBRAL DE CORTE ALPHA", 1, 254, 128)
    
    if st.sidebar.button("EJECUTAR CORRECCIÓN v4.0"):
        st.session_state.procesado = True

    # Definir imagen para el visor
    if not st.session_state.procesado:
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255] # Resaltar en Magenta
        img_visor = Image.fromarray(vis)
    else:
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        # Formato de nombre pedido: MAYÚSCULAS
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("🔄 REINICIAR"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR PROFESIONAL (USA EL ÁREA BLANCA DE LA DERECHA)
    st.subheader(f"VISOR DE PRECISIÓN: {archivo.name.upper()}")
    
    # Convertir imagen a Base64 para el Canvas
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # HTML + JS PARA EL VISOR DE PANTALLA COMPLETA
    html_visor = f"""
    <div class="canvas-container" id="container">
        <canvas id="canvas" style="cursor: grab;"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const container = document.getElementById('container');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";

        let scale = 1, viewX = 0, viewY = 0, isPanning = false, startX, startY;

        function initCanvas() {{
            canvas.width = container.clientWidth;
            canvas.height = container.clientHeight;
            
            // Ajuste inicial para que la imagen quepa en el visor
            scale = Math.min(canvas.width / img.width, canvas.height / img.height) * 0.8;
            viewX = (canvas.width - img.width * scale) / 2;
            viewY = (canvas.height - img.height * scale) / 2;
            draw();
        }}

        img.onload = initCanvas;
        window.onresize = initCanvas;

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false; // CRUCIAL: ELIMINA EL SUAVIZADO
            ctx.save();
            ctx.translate(viewX, viewY);
            ctx.scale(scale, scale);
            ctx.drawImage(img, 0, 0);
            ctx.restore();
        }}

        canvas.onwheel = (e) => {{
            e.preventDefault();
            const zoom = e.deltaY > 0 ? 0.8 : 1.2;
            const mouseX = e.offsetX, mouseY = e.offsetY;
            viewX = mouseX - (mouseX - viewX) * zoom;
            viewY = mouseY - (mouseY - viewY) * zoom;
            scale *= zoom;
            draw();
        }};

        canvas.onmousedown = (e) => {{ isPanning = true; startX = e.offsetX - viewX; startY = e.offsetY - viewY; canvas.style.cursor = 'grabbing'; }};
        window.onmouseup = () => {{ isPanning = false; canvas.style.cursor = 'grab'; }};
        canvas.onmousemove = (e) => {{
            if (!isPanning) return;
            viewX = e.offsetX - startX;
            viewY = e.offsetY - startY;
            draw();
        }};
    </script>
    <style>
        body {{ margin: 0; padding: 0; overflow: hidden; }}
        .canvas-container {{ width: 100%; height: 100%; }}
    </style>
    """
    # Aumentamos el height de st.components para que no corte el contenedor
    st.components.v1.html(html_visor, height=850)

else:
    st.session_state.procesado = False
    st.info("Sube un archivo PNG para iniciar el análisis de bordes.")
