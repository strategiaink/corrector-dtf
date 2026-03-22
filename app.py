import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de página - Forzamos el uso de todo el ancho
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide")

# CSS para maximizar el área de trabajo
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; padding-top: 0rem; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; min-width: 350px !important; }
    
    /* Botones Strategia Ink */
    .stButton > button, .stDownloadButton > button { 
        width: 100%; background-color: #d4ff00 !important; color: black !important; 
        font-weight: bold !important; border-radius: 8px !important; border: none !important; height: 3em;
    }

    /* Contenedor Full Screen para el Visor */
    #visor-externo {
        width: 100%; 
        height: 85vh; /* Ocupa casi todo el alto de la pantalla */
        border: 1px solid #30363d; 
        border-radius: 10px;
        background-color: #1a1a1a;
        background-image: linear-gradient(45deg, #2b2b2b 25%, transparent 25%), linear-gradient(-45deg, #2b2b2b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2b2b2b 75%), linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);
        background-size: 20px 20px;
        overflow: hidden;
    }
    
    /* Eliminar espacios innecesarios de Streamlit */
    .block-container { padding-top: 1rem; padding-bottom: 0rem; }
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
    
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.markdown('<div class="status-box" style="background-color: #1f1906; color: #ffd33d; padding:10px; border-radius:10px; border: 1px solid #ffd33d; text-align:center;">⚠️ ATENCIÓN: Ghost Pixels detectados.</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-box" style="background-color: #061f10; color: #3df18d; padding:10px; border-radius:10px; border: 1px solid #3df18d; text-align:center;">✅ IMAGEN LIMPIA.</div>', unsafe_allow_html=True)

    st.sidebar.markdown("### Configuración")
    dpi_val = st.sidebar.number_input("Resolución (DPI)", value=300)
    umbral = st.sidebar.slider("Umbral de Corte Alpha", 1, 254, 128)
    
    if st.sidebar.button("EJECUTAR CORRECCIÓN v4.0"):
        st.session_state.procesado = True

    if not st.session_state.procesado:
        vis = datos.copy()
        vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
        img_visor = img_final
        
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        nombre_descarga = f"P000 | {nombre_base}.PNG"
        buf = io.BytesIO()
        img_final.save(buf, format="PNG", dpi=(dpi_val, dpi_val))
        st.sidebar.download_button(f"📥 DESCARGAR: {nombre_descarga}", buf.getvalue(), nombre_descarga, "image/png")
        
        if st.sidebar.button("🔄 CORREGIR OTRA VEZ"):
            st.session_state.procesado = False
            st.rerun()

    # VISOR GIGANTE (MÁXIMA PRECISIÓN)
    st.subheader(f"Visor de Precisión: {archivo.name}")
    
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html_visor = f"""
    <div id="visor-externo">
        <canvas id="canvas" style="width: 100%; height: 100%; cursor: grab;"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";

        let scale = 1, viewX = 0, viewY = 0, isPanning = false, startX, startY;

        function resizeCanvas() {{
            canvas.width = canvas.parentElement.clientWidth;
            canvas.height = canvas.parentElement.clientHeight;
            draw();
        }}

        img.onload = () => {{
            // Centrar imagen al cargar
            scale = Math.min(canvas.width / img.width, canvas.height / img.height) * 0.9;
            viewX = (canvas.width - img.width * scale) / 2;
            viewY = (canvas.height - img.height * scale) / 2;
            resizeCanvas();
        }};

        window.addEventListener('resize', resizeCanvas);

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false; // FUERZA EL PÍXEL CRUDO
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
        
        resizeCanvas();
    </script>
    """
    st.components.v1.html(html_visor, height=800) # El alto del iframe ahora es grande

else:
    st.session_state.procesado = False
    st.info("Sube un archivo PNG para analizar los bordes en tamaño completo.")
