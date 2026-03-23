import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# ReportLab para PDF DTF
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# Estilos corregidos
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 330px !important; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .status-box { padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-align: center; border: 1px solid; }
    .status-clean { background-color: rgba(36, 161, 72, 0.1); border-color: #24a148; color: #24a148; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.1); border-color: orange; color: orange; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<h2 style="color:white; margin-bottom:20px;">STRATEGIA</h2>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        # Carga rápida y caché de análisis
        img_input = Image.open(archivo).convert("RGBA")
        pix_orig = np.array(img_input)
        
        # 1. ANALIZADOR ARRIBA
        if np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255)):
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO (SIN SEMITRANSPARENCIAS)</div>', unsafe_allow_html=True)

        # 2. CONFIGURACIÓN VISOR
        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fnd = st.selectbox("Fondo", ["Negro", "Blanco", "Transparente"])
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[fnd]

        # 3. TAMAÑO Y RES
        st.markdown('<span class="step-label">1. Tamaño y Resolución</span>', unsafe_allow_html=True)
        dpi_target = st.number_input("DPI de salida", value=300)
        w_px, h_px = img_input.size
        
        # 4. UMBRAL (REAL-TIME)
        st.markdown('<span class="step-label">2. Corrección de Bordes</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte", 1, 254, 128)
        
        # Procesamiento ultra-veloz para el visor
        new_a = np.where(pix_orig[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_fin = Image.fromarray(np.stack([pix_orig[:,:,0], pix_orig[:,:,1], pix_orig[:,:,2], new_a], axis=-1))

        # 5. DESCARGAS
        st.markdown("---")
        nom = archivo.name.rsplit('.', 1)[0].upper()
        
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        b_png = io.BytesIO()
        img_fin.save(b_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.download_button("📥 DESCARGAR PNG", b_png.getvalue(), f"P000 | {nom}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            b_pdf = io.BytesIO()
            pw, ph = (w_px * 72 / dpi_target), (h_px * 72 / dpi_target)
            c_pdf = pdf_canvas.Canvas(b_pdf, pagesize=(pw, ph))
            t_img = io.BytesIO(); img_fin.save(t_img, format="PNG")
            c_pdf.drawImage(ImageReader(t_img), 0, 0, width=pw, height=ph, mask='auto')
            c_pdf.save()
            st.download_button("📄 DESCARGAR PDF (DTF)", b_pdf.getvalue(), f"P000 | {nom}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR BLINDADO ---
if archivo:
    # Versión optimizada para que el visor "vuele"
    v_buf = io.BytesIO()
    ratio = 1200 / float(w_px)
    img_fin.resize((1200, int(h_px * ratio)), resample=Image.NEAREST).save(v_buf, format="PNG", optimize=True)
    v_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <canvas id="canvas" style="cursor: move;"></canvas>
        <button onclick="rc()" style="position:fixed; bottom:20px; right:20px; padding:12px; background:#d4ff00; border:none; border-radius:8px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">RE-CENTRAR</button>
    </div>
    <script>
        const canvas = document.getElementById('canvas'), ctx = canvas.getContext('2d'), img = new Image();
        img.src = "data:image/png;base64,{v_b64}";
        let s = 1, vx = 0, vy = 0, drag = false, lx, ly;
        function rc() {{
            s = Math.min(window.innerWidth/img.width, window.innerHeight/img.height)*0.85;
            vx = (window.innerWidth - img.width*s)/2; vy = (window.innerHeight - img.height*s)/2;
            draw();
        }}
        img.onload = () => {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; rc(); }};
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, vx, vy, img.width*s, img.height*s);
        }}
        canvas.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vx = e.offsetX - (e.offsetX - vx)*z; vy = e.offsetY - (e.offsetY - vy)*z;
            s *= z; draw();
        }};
        canvas.onmousedown = (e) => {{ drag = true; lx = e.offsetX - vx; ly = e.offsetY - vy; }};
        window.onmouseup = () => drag = false;
        canvas.onmousemove = (e) => {{ if(drag) {{ vx = e.offsetX - lx; vy = e.offsetY - ly; draw(); }} }};
        window.onresize = () => {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; draw(); }};
    </script>
    """, height=1200)
