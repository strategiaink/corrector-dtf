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

# CSS ESTABLE
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 330px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; }
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
        pix_orig = np.array(img_input)
        
        # 1. ANALIZADOR
        if np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255)):
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO (SIN SEMITRANSPARENCIAS)</div>', unsafe_allow_html=True)

        # 2. CONFIGURACIÓN VISOR
        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fnd = st.selectbox("Fondo", ["Negro", "Blanco", "Transparente"])
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[fnd]

        # 3. TAMAÑO Y RESOLUCIÓN (RESTAURADO)
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

        # 4. CORRECCIÓN (UMBRAL)
        st.markdown('<span class="step-label">2. Corrección de Bordes</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte", 1, 254, 128)
        
        # Redimensionar y aplicar umbral
        f_w, f_h = int((w_cm / 2.54) * dpi_target), int((h_cm / 2.54) * dpi_target)
        img_res = img_input.resize((f_w, f_h), resample=Image.LANCZOS)
        dat_np = np.array(img_res)
        new_a = np.where(dat_np[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([dat_np[:,:,0], dat_np[:,:,1], dat_np[:,:,2], new_a], axis=-1))

        # 5. BOTONES DE DESCARGA
        st.markdown("---")
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        buf_png = io.BytesIO()
        img_final.save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre_base}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            buf_pdf = io.BytesIO()
            p_w, p_h = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
            canvas_pdf = pdf_canvas.Canvas(buf_pdf, pagesize=(p_w, p_h))
            img_tmp = io.BytesIO(); img_final.save(img_tmp, format="PNG")
            canvas_pdf.drawImage(ImageReader(img_tmp), 0, 0, width=p_w, height=p_h, mask='auto')
            canvas_pdf.save()
            st.download_button("📄 DESCARGAR PDF (DTF)", buf_pdf.getvalue(), f"P000 | {nombre_base}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR ESTABLE ---
if archivo:
    v_buf = io.BytesIO()
    # Proxy para que el visor sea rápido
    img_final.resize((1000, int(1000 * f_h / f_w)), resample=Image.NEAREST).save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <canvas id="canvas" style="cursor: move;"></canvas>
        <button onclick="rc()" style="position:fixed; bottom:20px; right:20px; padding:12px; background:#d4ff00; border:none; border-radius:8px; font-weight:bold; cursor:pointer;">RE-CENTRAR</button>
    </div>
    <script>
        const canvas = document.getElementById('canvas'), ctx = canvas.getContext('2d'), img = new Image();
        img.src = "data:image/png;base64,{img_b64}";
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
    """, height=1000)
