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

st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS Minimalista para carga rápida
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 320px !important; }
    .step-label { color: white; font-weight: bold; margin-top: 10px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; }
    .status-box { padding: 10px; border-radius: 8px; font-weight: bold; margin-bottom: 10px; text-align: center; border: 1px solid; }
    .status-clean { background-color: rgba(36, 161, 72, 0.1); border-color: #24a148; color: #24a148; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.1); border-color: orange; color: orange; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# Función de procesamiento ultra rápida
@st.cache_data(show_spinner=False)
def procesar_limpieza(img_np, umbral):
    alpha = img_np[:, :, 3]
    nuevo_alpha = np.where(alpha < umbral, 0, 255).astype(np.uint8)
    return np.stack([img_np[:,:,0], img_np[:,:,1], img_np[:,:,2], nuevo_alpha], axis=-1)

with st.sidebar:
    st.title("STRATEGIA")
    archivo = st.file_uploader("Subir", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        # Carga inicial única
        img_input = Image.open(archivo).convert("RGBA")
        pix_orig = np.array(img_input)
        
        # 1. ANALIZADOR
        if np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255)):
            st.markdown('<div class="status-box status-dirty">⚠️ SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO</div>', unsafe_allow_html=True)

        # 2. VISOR CONFIG
        st.markdown('<span class="step-label">Visor</span>', unsafe_allow_html=True)
        fnd = st.selectbox("Fondo", ["Negro", "Blanco", "Transparente"])
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[fnd]

        # 3. TAMAÑO
        st.markdown('<span class="step-label">1. Medidas</span>', unsafe_allow_html=True)
        dpi_target = st.number_input("DPI", value=300)
        w_px, h_px = img_input.size
        
        # 4. UMBRAL REAL-TIME
        st.markdown('<span class="step-label">2. Umbral</span>', unsafe_allow_html=True)
        umbral = st.slider("Ajuste", 1, 254, 128)
        
        # Procesar solo lo necesario para el visor (usamos la imagen cargada)
        res_np = procesar_limpieza(pix_orig, umbral)
        img_fin = Image.fromarray(res_np)

        # 5. DESCARGAS (Solo se ejecutan al clickear)
        st.markdown("---")
        nom = archivo.name.rsplit('.', 1)[0].upper()
        
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        b_png = io.BytesIO()
        img_fin.save(b_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.download_button("📥 PNG", b_png.getvalue(), f"P000 | {nom}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            b_pdf = io.BytesIO()
            # Cálculo rápido de puntos PDF
            pw, ph = (w_px * 72 / dpi_target), (h_px * 72 / dpi_target)
            c_pdf = pdf_canvas.Canvas(b_pdf, pagesize=(pw, ph))
            t_img = io.BytesIO(); img_fin.save(t_img, format="PNG")
            c_pdf.drawImage(ImageReader(t_img), 0, 0, width=pw, height=ph, mask='auto')
            c_pdf.save()
            st.download_button("📄 PDF (DTF)", b_pdf.getvalue(), f"P000 | {nom}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR ULTRA RÁPIDO ---
if archivo:
    v_buf = io.BytesIO()
    # Bajamos un poco la calidad SOLO para el visor para que cargue instantáneo
    img_fin.resize((1000, int(1000*h_px/w_px))).save(v_buf, format="PNG", optimize=True)
    v_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative;">
        <canvas id="v"></canvas>
        <button onclick="rc()" style="position:fixed; bottom:20px; right:20px; padding:10px; background:#d4ff00; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">RE-CENTRAR</button>
    </div>
    <script>
        const v = document.getElementById('v'), x = v.getContext('2d'), i = new Image();
        i.src = "data:image/png;base64,{v_b64}";
        let s=1, vx=0, vy=0, d=false, lx, ly;
        function rc() {{
            s = Math.min(window.innerWidth/i.width, window.innerHeight/i.height)*0.9;
            vx = (window.innerWidth - i.width*s)/2; vy = (window.innerHeight - i.height*s)/2;
            w();
        }}
        i.onload = () => {{ v.width = window.innerWidth; v.height = window.innerHeight; rc(); }};
        function w() {{
            x.clearRect(0, 0, v.width, v.height);
            x.imageSmoothingEnabled = false;
            x.drawImage(i, vx, vy, i.width*s, i.height*s);
        }}
        v.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vx = e.offsetX - (e.offsetX - vx)*z; vy = e.offsetY - (e.offsetY - vy)*z;
            s *= z; w();
        }};
        v.onmousedown = (e) => {{ d=true; lx=e.offsetX-vx; ly=e.offsetY-vy; }};
        window.onmouseup = () => d=false;
        v.onmousemove = (e) => {{ if(d) {{ vx=e.offsetX-lx; vy=e.offsetY-ly; w(); }} }};
    </script>
    """, height=1000)
