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
    .info-text { color: #aaaaaa; font-size: 0.85rem; margin-bottom: 5px; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-center > div > button { background-color: #d4ff00 !important; color: black !important; font-weight: bold !important; margin-top: 10px; }
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
        
        # --- LECTURA DE METADATOS ORIGINALES ---
        w_orig_px, h_orig_px = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        w_orig_cm = round((w_orig_px * 2.54) / dpi_orig, 2)
        h_orig_cm = round((h_orig_px * 2.54) / dpi_orig, 2)

        st.markdown('<span class="step-label">Información Original</span>', unsafe_allow_html=True)
        st.markdown(f'<p class="info-text">Resolución: {w_orig_px} x {h_orig_px} px</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="info-text">Densidad: {dpi_orig} DPI</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="info-text">Tamaño: {w_orig_cm} x {h_orig_cm} cm</p>', unsafe_allow_html=True)

        # --- SECCIÓN DE EDICIÓN ---
        st.markdown('<span class="step-label">1. Ajustar Medidas</span>', unsafe_allow_html=True)
        preset = st.selectbox("Formato de salida:", list(PRESETS.keys()))
        unidad = st.selectbox("Unidad de edición", ["Centímetros", "Píxeles"])
        dpi_target = st.number_input("DPI de salida", value=int(dpi_orig) if dpi_orig > 71 else 300)
        
        if preset != "Personalizado":
            w_cm, h_cm = PRESETS[preset]
        else:
            col1, col2 = st.columns([3, 1])
            with col1:
                if unidad == "Centímetros":
                    w_cm = st.number_input("Ancho (cm)", value=w_orig_cm)
                else:
                    px_w = st.number_input("Ancho (px)", value=w_orig_px)
                    w_cm = (px_w * 2.54) / dpi_target
            
            mantener = col2.checkbox("🔗", value=True)
            
            if unidad == "Centímetros":
                h_cm = st.number_input("Alto (cm)", value=h_orig_cm if mantener else 0.0)
            else:
                px_h = st.number_input("Alto (px)", value=h_orig_px if mantener else 0)
                h_cm = (px_h * 2.54) / dpi_target

        # --- CORRECCIÓN ---
        st.markdown('<span class="step-label">2. Corrección de Bordes</span>', unsafe_allow_html=True)
        umbral_final = st.slider("Umbral para descarga", 1, 254, 128)
        
        if st.button("CENTRAR VISOR"):
            st.session_state['reset_visor'] = st.session_state.get('reset_visor', 0) + 1

        # PROCESO FINAL
        f_w, f_h = int((w_cm / 2.54) * dpi_target), int((h_cm / 2.54) * dpi_target)
        pix_np = np.array(img_input)
        new_a = np.where(pix_np[:,:,3] < umbral_final, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([pix_np[:,:,0], pix_np[:,:,1], pix_np[:,:,2], new_a], axis=-1)).resize((f_w, f_h), resample=Image.LANCZOS)

        # --- DESCARGAS ---
        st.markdown("---")
        nombre_base = archivo.name.rsplit('.', 1)[0].upper()
        
        buf_png = io.BytesIO()
        img_final.save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre_base}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            buf_pdf = io.BytesIO()
            p_w, p_h = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
            c_pdf = pdf_canvas.Canvas(buf_pdf, pagesize=(p_w, p_h))
            img_tmp = io.BytesIO(); img_final.save(img_tmp, format="PNG")
            c_pdf.drawImage(ImageReader(img_tmp), 0, 0, width=p_w, height=p_h, mask='auto')
            c_pdf.save()
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄 DESCARGAR PDF (DTF)", buf_pdf.getvalue(), f"P000 | {nombre_base}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR HÍBRIDO RÁPIDO ---
if archivo:
    v_buf = io.BytesIO()
    img_input.resize((1000, int(1000 * h_orig_px / w_orig_px))).save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    reset_val = st.session_state.get('reset_visor', 0)
    
    st.components.v1.html(f"""
    <div style="background-color: #000; width: 100vw; height: 100vh; overflow: hidden; position: relative; font-family: sans-serif;">
        <div style="position: absolute; top: 15px; left: 15px; z-index: 10; background: rgba(0,0,0,0.85); padding: 15px; border-radius: 10px; border: 1px solid #d4ff00; color: white; min-width: 180px;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #d4ff00; font-size: 12px;">VISOR EN VIVO</p>
            <label style="font-size: 11px;">Umbral:</label>
            <input type="range" id="u" min="1" max="254" value="128" style="width: 100%; cursor: pointer; accent-color: #d4ff00;">
            <div id="uv" style="text-align: center; font-weight: bold; margin-top: 5px;">128</div>
        </div>
        <canvas id="c" style="cursor: move;"></canvas>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d'), im = new Image();
        const sl = document.getElementById('u'), sv = document.getElementById('uv');
        im.src = "data:image/png;base64,{img_b64}";
        
        let s = parseFloat(sessionStorage.getItem('v_s')) || 0;
        let vx = parseFloat(sessionStorage.getItem('v_vx')) || 0;
        let vy = parseFloat(sessionStorage.getItem('v_vy')) || 0;
        let lastR = {reset_val}, storR = parseInt(sessionStorage.getItem('v_r')) || 0;
        let offC = document.createElement('canvas'), offX, drag = false, lx, ly;

        im.onload = () => {{
            c.width = window.innerWidth; c.height = window.innerHeight;
            offC.width = im.width; offC.height = im.height;
            offX = offC.getContext('2d');
            if(s === 0 || lastR > storR) rc(); else render();
        }};

        sl.oninput = () => {{ sv.innerText = sl.value; render(); }};

        function render() {{
            offX.drawImage(im, 0, 0);
            let id = offX.getImageData(0, 0, offC.width, offC.height);
            let d = id.data, t = parseInt(sl.value);
            for (let i = 3; i < d.length; i += 4) d[i] = d[i] < t ? 0 : 255;
            createImageBitmap(id).then(bmp => {{
                x.clearRect(0, 0, c.width, c.height);
                x.imageSmoothingEnabled = false;
                x.drawImage(bmp, vx, vy, im.width * s, im.height * s);
            }});
        }}

        function rc() {{
            s = Math.min(window.innerWidth/im.width, window.innerHeight/im.height)*0.85;
            vx = (window.innerWidth - im.width*s)/2; vy = (window.innerHeight - img.height*s)/2;
            sessionStorage.setItem('v_r', lastR);
            render();
        }}

        c.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vx = e.offsetX - (e.offsetX - vx)*z; vy = e.offsetY - (e.offsetY - vy)*z;
            s *= z; sessionStorage.setItem('v_s', s); sessionStorage.setItem('v_vx', vx); sessionStorage.setItem('v_vy', vy);
            render();
        }};
        c.onmousedown = (e) => {{ drag = true; lx = e.offsetX - vx; ly = e.offsetY - vy; }};
        window.onmouseup = () => drag = false;
        c.onmousemove = (e) => {{ if(drag) {{ vx = e.offsetX - lx; vy = e.offsetY - ly; render(); }} }};
    </script>
    """, height=1000)
