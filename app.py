import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide")

# CSS para branding y eliminar el suavizado del contenedor
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
        display: flex; align-items: center; justify-content: center; text-align: center;
    }
    .status-warning { background-color: #1f1906; color: #ffd33d; border-color: #ffd33d; }
    .status-success { background-color: #061f10; color: #3df18d; border-color: #3df18d; }
    
    /* Fondo ajedrezado para el visor */
    #visor-externo {
        width: 100%; height: 750px; border: 1px solid #30363d; border-radius: 10px;
        background-color: #1a1a1a;
        background-image: linear-gradient(45deg, #2b2b2b 25%, transparent 25%), linear-gradient(-45deg, #2b2b2b 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #2b2b2b 75%), linear-gradient(-45deg, transparent 75%, #2b2b2b 75%);
        background-size: 20px 20px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state:
    st.session_state.procesado = False

st.sidebar.title("CORRECTOR STRATEGIA INK")
st.sidebar.markdown("---")

archivo = st.sidebar.file_uploader("Subir imagen PNG", type=["png"], label_visibility="collapsed")

if archivo:
    img_orig = Image.open(archivo).convert("RGBA")
    datos = np.array(img_orig)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    hay_semi = np.any((a > 0) & (a < 255))
    if hay_semi:
        st.sidebar.markdown('<div class="status-box status-warning">⚠️ ATENCIÓN: Esta imagen tiene semitransparencias (Ghost Pixels).</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="status-box status-success">✅ IMAGEN LIMPIA: Sin halos ni semitransparencias.</div>', unsafe_allow_html=True)

    st.sidebar.markdown("### Configuración de Salida")
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

    # VISOR MOTOR CANVAS (FUERZA PÍXEL REAL)
    st.subheader("Control de Calidad (Píxel Crudo)")
    st.caption("Ruedita: Zoom | Click Izquierdo: Mover")
    
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

        img.onload = () => {{
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
            draw();
        }};

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            // ESTO ELIMINA EL SUAVIZADO EN EL CANVAS
            ctx.imageSmoothingEnabled = false;
            ctx.mozImageSmoothingEnabled = false;
            ctx.webkitImageSmoothingEnabled = false;
            ctx.msImageSmoothingEnabled = false;

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
            if (scale < 0.1) scale = 0.1; if (scale > 100) scale = 100;
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
    """
    st.components.v1.html(html_visor, height=770)

else:
    st.session_state.procesado = False
    st.info("Sube un archivo PNG para iniciar el análisis.")
