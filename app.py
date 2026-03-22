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

# CONFIGURACIÓN DE PÁGINA (Layout Wide para recuperar espacio)
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS: RECUPERAR ESPACIO DE TRABAJO Y SEPARAR BOTONES
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 380px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    
    /* Separación de botones */
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; height: 3.5em; margin-bottom: 10px; }
    div.stButton > button:first-child { background-color: #d4ff00 !important; color: black !important; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; margin-top: 20px; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# Definición de tamaños estándar (Ancho, Alto en cm)
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

        st.markdown('<span class="step-label">1. Tamaño y Resolución (Real-Time)</span>', unsafe_allow_html=True)
        preset = st.selectbox("Ajustar a tamaño:", list(PRESETS.keys()))
        unidad = st.selectbox("Unidad de medida", ["Centímetros", "Píxeles"])
        dpi_target = st.number_input("Resolución (DPI)", value=300)
        
        # Lógica de Proporción y Medidas
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

        # Conversión final a píxeles para el motor
        final_w = int((w_cm / 2.54) * dpi_target)
        final_h = int((h_cm / 2.54) * dpi_target)

        # REDIMENSIONADO AUTOMÁTICO (Sin botón)
        img_resized = img_input.resize((final_w, final_h), resample=Image.LANCZOS)
        
        st.markdown('<span class="step-label">2. Limpieza de Semitransparencias</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte (Alpha)", 1, 254, 128)
        
        if st.button("APLICAR CORRECCIÓN DE BORDES"):
            datos = np.array(img_resized)
            nuevo_a = np.where(datos[:,:,3] < umbral, 0, 255).astype(np.uint8)
            st.session_state['img_final'] = Image.fromarray(np.stack([datos[:,:,0], datos[:,:,1], datos[:,:,2], nuevo_a], axis=-1))
            st.session_state['dpi_final'] = dpi_target

        # BOTONES DE DESCARGA SEPARADOS
        if 'img_final' in st.session_state:
            st.markdown("---")
            nombre = archivo.name.rsplit('.', 1)[0].upper()
            
            st.markdown('<div class="btn-png">', unsafe_allow_html=True)
            buf_png = io.BytesIO()
            st.session_state['img_final'].save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
            st.download_button("📥 DESCARGAR PNG CORREGIDO", buf_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
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
                st.download_button("📄 DESCARGAR PDF (DTF)", buf_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<span class="step-label">Visualización</span>', unsafe_allow_html=True)
        opcion_fondo = st.selectbox("Fondo Visor", ["Negro", "Blanco", "Transparente"], index=0)
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

# --- VISOR FULL SCREEN (RESTAURADO) ---
if archivo:
    # Si ya corregimos, mostrar la corregida. Si no, mostrar la redimensionada con Ghost Pixels.
    if 'img_final' in st.session_state:
        img_visor = st.session_state['img_final']
    else:
        vis = np.array(img_resized)
        vis[(vis[:,:,3] > 0) & (vis[:,:,3] < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)

    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <canvas id="canvas" style="cursor: move;"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";
        let scale = 1, vX = 0, vY = 0, pX, pY, down = false;
        img.onload = () => {{
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            scale = Math.min(canvas.width/img.width, canvas.height/img.height) * 0.9;
            vX = (canvas.width - img.width*scale)/2; vY = (canvas.height - img.height*scale)/2;
            draw();
        }};
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, vX, vY, img.width*scale, img.height*scale);
        }}
        canvas.onwheel = (e) => {{ e.preventDefault(); scale *= e.deltaY > 0 ? 0.85 : 1.15; draw(); }};
        canvas.onmousedown = (e) => {{ down = true; pX = e.offsetX - vX; pY = e.offsetY - vY; }};
        window.onmouseup = () => down = false;
        canvas.onmousemove = (e) => {{ if(down) {{ vX = e.offsetX - pX; vY = e.offsetY - pY; draw(); }} }};
        window.onresize = () => {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; draw(); }};
    </script>
    """, height=1200)
