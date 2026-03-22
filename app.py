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

# CSS: ESTILOS
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; height: 3em; margin-top: 10px; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    
    .status-box { padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-align: center; border: 1px solid; }
    .status-clean { background-color: rgba(36, 161, 72, 0.1); border-color: #24a148; color: #24a148; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.1); border-color: orange; color: orange; }
    
    header, footer { visibility: hidden; }
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
        
        # 1. ANALIZADOR (ARRIBA DE TODO)
        pixeles_orig = np.array(img_input)
        alpha_orig = pixeles_orig[:, :, 3]
        if np.any((alpha_orig > 0) & (alpha_orig < 255)):
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO (SIN SEMITRANSPARENCIAS)</div>', unsafe_allow_html=True)

        # 2. SECCIÓN VISOR (ESTADO ANTERIOR)
        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fnd = st.selectbox("Fondo del área de trabajo", ["Negro", "Blanco", "Transparente"])
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[fnd]

        # 3. TAMAÑO Y RESOLUCIÓN
        st.markdown('<span class="step-label">1. Tamaño y Resolución</span>', unsafe_allow_html=True)
        preset = st.selectbox("Formato predefinido:", list(PRESETS.keys()))
        unidad = st.selectbox("Unidad", ["Centímetros", "Píxeles"])
        dpi_target = st.number_input("DPI de salida", value=300)
        
        ancho_orig, alto_orig = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        
        if preset != "Personalizado":
            w_cm, h_cm = PRESETS[preset]
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if unidad == "Centímetros":
                    w_cm = st.number_input("Ancho (cm)", value=float(ancho_orig * 2.54 / dpi_orig))
                else:
                    px_w = st.number_input("Ancho (px)", value=int(ancho_orig))
                    w_cm = (px_w * 2.54) / dpi_target
            with col2:
                mantener = st.checkbox("🔗", value=True)
            
            if unidad == "Centímetros":
                h_cm = st.number_input("Alto (cm)", value=float(alto_orig * 2.54 / dpi_orig) if mantener else 0.0)
            else:
                px_h = st.number_input("Alto (px)", value=int(alto_orig) if mantener else 0)
                h_cm = (px_h * 2.54) / dpi_target

        f_w, f_h = int((w_cm / 2.54) * dpi_target), int((h_cm / 2.54) * dpi_target)
        img_resized = img_input.resize((f_w, f_h), resample=Image.LANCZOS)
        
        # 4. LIMPIEZA AUTOMÁTICA (SIN BOTÓN)
        st.markdown('<span class="step-label">2. Corrección de Bordes</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte", 1, 254, 128)
        
        # PROCESADO EN TIEMPO REAL
        datos = np.array(img_resized)
        nuevo_a = np.where(datos[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([datos[:,:,0], datos[:,:,1], datos[:,:,2], nuevo_a], axis=-1))

        # 5. DESCARGAS
        st.markdown("---")
        nombre = archivo.name.rsplit('.', 1)[0].upper()
        
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        b_png = io.BytesIO()
        img_final.save(b_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.download_button("📥 DESCARGAR PNG", b_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            b_pdf = io.BytesIO()
            pts_w, pts_h = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
            c = pdf_canvas.Canvas(b_pdf, pagesize=(pts_w, pts_h))
            t = io.BytesIO(); img_final.save(t, format="PNG")
            c.drawImage(ImageReader(t), 0, 0, width=pts_w, height=pts_h, mask='auto'); c.save()
            st.download_button("📄 DESCARGAR PDF", b_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR CON ZOOM FOCALIZADO Y ACTUALIZACIÓN DINÁMICA ---
if archivo:
    buf = io.BytesIO()
    img_final.save(buf, format="PNG")
    img_64 = base64.b64encode(buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative;">
        <canvas id="c" style="cursor: move;"></canvas>
        <button onclick="rv()" style="position:fixed; bottom:20px; right:20px; padding:12px; background:#d4ff00; border:none; border-radius:8px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">RE-CENTRAR IMAGEN</button>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d'), i = new Image();
        i.src = "data:image/png;base64,{img_64}";
        let s = 1, vX = 0, vY = 0, d = false, pX, pY;
        function rv() {{
            s = Math.min(window.innerWidth/i.width, window.innerHeight/i.height) * 0.8;
            vX = (window.innerWidth - i.width*s)/2; vY = (window.innerHeight - i.height*s)/2;
            w();
        }}
        i.onload = () => {{ c.width = window.innerWidth; c.height = window.innerHeight; rv(); }};
        function w() {{
            x.clearRect(0, 0, c.width, c.height);
            x.imageSmoothingEnabled = false;
            x.drawImage(i, vX, vY, i.width*s, i.height*s);
        }}
        c.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vX = e.offsetX - (e.offsetX - vX) * z; vY = e.offsetY - (e.offsetY - vY) * z;
            s *= z; w();
        }};
        c.onmousedown = (e) => {{ d = true; pX = e.offsetX - vX; pY = e.offsetY - vY; }};
        window.onmouseup = () => d = false;
        c.onmousemove = (e) => {{ if(d) {{ vX = e.offsetX - pX; vY = e.offsetY - pY; w(); }} }};
        window.onresize = () => {{ c.width = window.innerWidth; c.height = window.innerHeight; w(); }};
    </script>
    """, height=1000)
