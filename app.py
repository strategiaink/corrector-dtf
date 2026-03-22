import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de ReportLab
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS: ESPACIO FULL Y BOTONES
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 380px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; height: 3.5em; margin-bottom: 10px; }
    div.stButton > button:first-child { background-color: #d4ff00 !important; color: black !important; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; margin-top: 10px; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    header, footer { visibility: hidden; }
    
    .viewer-container {
        width: 100%;
        height: 100vh;
        overflow: auto !important;
        background-image: radial-gradient(#333 1px, transparent 1px);
        background-size: 20px 20px;
        position: relative;
    }
    
    /* Estilos para los carteles de estado */
    .status-box { padding: 15px; border-radius: 10px; font-weight: bold; margin: 10px 0; text-align: center; }
    .status-clean { background-color: rgba(36, 161, 72, 0.2); border: 1px solid #24a148; color: #24a148; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.2); border: 1px solid orange; color: orange; }
    </style>
    """, unsafe_allow_html=True)

PRESETS = {
    "Personalizado": None,
    "A2 (42 x 59.4 cm)": (42.0, 59.4),
    "A3 (29.7 x 42 cm)": (29.7, 42.0),
    "A4 (21 x 29.7 cm)": (21.0, 29.7)
}

with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR STRATEGIA</div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        img_input = Image.open(archivo).convert("RGBA")
        ancho_orig, alto_orig = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]

        # --- ANALIZADOR DE SEMITRANSPARENCIAS (RESTAURADO) ---
        pixeles = np.array(img_input)
        alpha = pixeles[:, :, 3]
        tiene_semi = np.any((alpha > 0) & (alpha < 255))
        
        if tiene_semi:
            st.markdown('<div class="status-box status-dirty">⚠️ Tiene semitransparencias.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ Limpio (sin semitransparencias).</div>', unsafe_allow_html=True)

        st.markdown('<span class="step-label">1. Tamaño y Resolución</span>', unsafe_allow_html=True)
        preset = st.selectbox("Ajustar a tamaño:", list(PRESETS.keys()))
        unidad = st.selectbox("Unidad de medida", ["Centímetros", "Píxeles"])
        dpi_target = st.number_input("Resolución (DPI)", value=300)
        
        if preset != "Personalizado":
            w_cm, h_cm = PRESETS[preset]
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if unidad == "Centímetros":
                    w_cm = st.number_input("Ancho (cm)", value=float(ancho_orig * 2.54 / dpi_orig))
                else:
                    new_px_w = st.number_input("Ancho (px)", value=int(ancho_orig))
                    w_cm = (new_px_w * 2.54) / dpi_target
            with col2:
                mantener = st.checkbox("🔗", value=True)
            
            if unidad == "Centímetros":
                h_cm = st.number_input("Alto (cm)", value=float(alto_orig * 2.54 / dpi_orig) if mantener else 0.0)
            else:
                new_px_h = st.number_input("Alto (px)", value=int(alto_orig) if mantener else 0)
                h_cm = (new_px_h * 2.54) / dpi_target

        # Redimensionado en tiempo real
        final_w, final_h = int((w_cm / 2.54) * dpi_target), int((h_cm / 2.54) * dpi_target)
        img_resized = img_input.resize((final_w, final_h), resample=Image.LANCZOS)
        
        st.markdown('<span class="step-label">2. Limpieza (Alpha)</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte", 1, 254, 128)
        
        if st.button("APLICAR CORRECCIÓN"):
            datos = np.array(img_resized)
            nuevo_a = np.where(datos[:,:,3] < umbral, 0, 255).astype(np.uint8)
            st.session_state['img_final'] = Image.fromarray(np.stack([datos[:,:,0], datos[:,:,1], datos[:,:,2], nuevo_a], axis=-1))

        if 'img_final' in st.session_state:
            st.markdown("---")
            nombre = archivo.name.rsplit('.', 1)[0].upper()
            st.markdown('<div class="btn-png">', unsafe_allow_html=True)
            buf_png = io.BytesIO()
            st.session_state['img_final'].save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
            st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if pdf_disponible:
                st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
                buf_pdf = io.BytesIO()
                w_pts, h_pts = (st.session_state['img_final'].size[0] * 72 / dpi_target), (st.session_state['img_final'].size[1] * 72 / dpi_target)
                p = pdf_canvas.Canvas(buf_pdf, pagesize=(w_pts, h_pts))
                tmp = io.BytesIO()
                st.session_state['img_final'].save(tmp, format="PNG")
                p.drawImage(ImageReader(tmp), 0, 0, width=w_pts, height=h_pts, mask='auto')
                p.save()
                st.download_button("📄 DESCARGAR PDF", buf_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<span class="step-label">Visualización</span>', unsafe_allow_html=True)
        opcion_fondo = st.selectbox("Fondo Visor", ["Negro", "Blanco", "Transparente"], index=0)
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

# --- VISOR CON ZOOM FOCALIZADO EN CURSOR ---
if archivo:
    img_v = st.session_state['img_final'] if 'img_final' in st.session_state else img_resized
    if 'img_final' not in st.session_state:
        vis = np.array(img_v)
        vis[(vis[:,:,3] > 0) & (vis[:,:,3] < 255)] = [255, 0, 255, 255]
        img_v = Image.fromarray(vis)

    buffered = io.BytesIO()
    img_v.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div class="viewer-container" style="background-color: {bg_css};">
        <canvas id="canvas" style="cursor: move;"></canvas>
        <button onclick="resetView()" style="position:fixed; bottom:20px; right:20px; z-index:100; padding:10px; background:#d4ff00; border:none; border-radius:5px; cursor:pointer; font-weight:bold;">RE-CENTRAR</button>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";
        let scale = 1, vX = 0, vY = 0, pX, pY, down = false;

        function resetView() {{
            scale = Math.min(window.innerWidth/img.width, window.innerHeight/img.height) * 0.8;
            vX = (window.innerWidth - img.width*scale)/2; 
            vY = (window.innerHeight - img.height*scale)/2;
            draw();
        }}

        img.onload = () => {{
            canvas.width = Math.max(window.innerWidth, img.width * 5); 
            canvas.height = Math.max(window.innerHeight, img.height * 5);
            resetView();
        }};

        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, vX, vY, img.width*scale, img.height*scale);
        }}

        canvas.onwheel = (e) => {{ 
            e.preventDefault(); 
            const zoom = e.deltaY > 0 ? 0.9 : 1.1;
            const mouseX = e.offsetX;
            const mouseY = e.offsetY;
            vX = mouseX - (mouseX - vX) * zoom;
            vY = mouseY - (mouseY - vY) * zoom;
            scale *= zoom;
            draw();
        }};

        canvas.onmousedown = (e) => {{ down = true; pX = e.offsetX - vX; pY = e.offsetY - vY; }};
        window.onmouseup = () => down = false;
        canvas.onmousemove = (e) => {{ if(down) {{ vX = e.offsetX - pX; vY = e.offsetY - pY; draw(); }} }};
    </script>
    """, height=1200)
