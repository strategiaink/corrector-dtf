import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS para mantener el estilo limpio y profesional
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 330px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .status-box { padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-align: center; border: 1px solid; }
    .status-clean { background-color: rgba(36, 161, 72, 0.1); border-color: #24a148; color: #24a148; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.1); border-color: orange; color: orange; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; }
    .btn-center > div > button { background-color: #d4ff00 !important; color: black !important; font-weight: bold !important; margin-top: 10px; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR STRATEGIA</div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        img_input = Image.open(archivo).convert("RGBA")
        pix_orig = np.array(img_input)
        
        # --- CARTEL DE AVISO (REQUISITO FUNDAMENTAL) ---
        tiene_semi = np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255))
        if tiene_semi:
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO</div>', unsafe_allow_html=True)

        # INFO DE ARCHIVO (ESTILO PHOTOSHOP)
        w_px, h_px = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        st.markdown(f'<p style="color:#888; font-size:12px; margin:0;">{w_px}x{h_px} px | {dpi_orig} DPI</p>', unsafe_allow_html=True)

        st.markdown('<span class="step-label">1. Medidas de Salida</span>', unsafe_allow_html=True)
        dpi_target = st.number_input("DPI", value=300)
        ancho_cm = st.number_input("Ancho (cm)", value=float(round(w_px * 2.54 / dpi_orig, 2)))
        alto_cm = st.number_input("Alto (cm)", value=float(round(h_px * 2.54 / dpi_orig, 2)))

        st.markdown('<span class="step-label">2. Umbral de Limpieza</span>', unsafe_allow_html=True)
        # El valor de este slider es el que MANDARÁ en la descarga
        umbral = st.slider("Intensidad (Photoshop)", 1, 254, 128)
        
        st.markdown('<div class="btn-center">', unsafe_allow_html=True)
        if st.button("CENTRAR IMAGEN"):
            st.session_state['reset_v'] = st.session_state.get('reset_v', 0) + 1
        st.markdown('</div>', unsafe_allow_html=True)

        # --- PROCESO DE LIMPIEZA REAL PARA DESCARGA ---
        # 1. Aplicamos umbral drástico: < umbral -> transparente (0), >= umbral -> sólido (255)
        mascara = np.where(pix_orig[:,:,3] < umbral, 0, 255).astype(np.uint8)
        # 2. Creamos la imagen limpia combinando colores originales y la máscara nueva
        img_limpia = Image.fromarray(np.stack([pix_orig[:,:,0], pix_orig[:,:,1], pix_orig[:,:,2], mascara], axis=-1))
        # 3. Redimensionamos el resultado YA LIMPIO
        f_w, f_h = int((ancho_cm / 2.54) * dpi_target), int((alto_cm / 2.54) * dpi_target)
        img_final = img_limpia.resize((f_w, f_h), resample=Image.LANCZOS)

        st.markdown("---")
        nombre = archivo.name.rsplit('.', 1)[0].upper()
        
        # Generación de archivos
        buf_png = io.BytesIO()
        img_final.save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
        
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            buf_pdf = io.BytesIO()
            pw, ph = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
            c = pdf_canvas.Canvas(buf_pdf, pagesize=(pw, ph))
            it = io.BytesIO(); img_final.save(it, format="PNG")
            c.drawImage(ImageReader(it), 0, 0, width=pw, height=ph, mask='auto')
            c.save()
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄 DESCARGAR PDF (DTF)", buf_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR SINCRONIZADO ---
if archivo:
    # Imagen optimizada para el visor (1000px)
    v_buf = io.BytesIO()
    img_input.resize((1000, int(1000 * h_px / w_px))).save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: #000; width: 100vw; height: 100vh; overflow: hidden; position: relative;">
        <canvas id="c" style="cursor: move;"></canvas>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d'), im = new Image();
        im.src = "data:image/png;base64,{img_b64}";
        let s = parseFloat(sessionStorage.getItem('v_s')) || 0, vx = parseFloat(sessionStorage.getItem('v_vx')) || 0, vy = parseFloat(sessionStorage.getItem('v_vy')) || 0;
        let rst = {st.session_state.get('reset_v', 0)}, sR = parseInt(sessionStorage.getItem('v_r')) || 0;
        let offC = document.createElement('canvas'), offX, drag = false, lx, ly;

        im.onload = () => {{
            c.width = window.innerWidth; c.height = window.innerHeight;
            offC.width = im.width; offC.height = im.height; offX = offC.getContext('2d');
            if(s === 0 || rst > sR) rc(); else render();
        }};

        function render() {{
            offX.clearRect(0, 0, offC.width, offC.height);
            offX.drawImage(im, 0, 0);
            let id = offX.getImageData(0, 0, offC.width, offC.height), d = id.data, t = {umbral};
            for (let i = 3; i < d.length; i += 4) d[i] = d[i] < t ? 0 : 255;
            createImageBitmap(id).then(bmp => {{
                x.clearRect(0, 0, c.width, c.height);
                x.imageSmoothingEnabled = false;
                x.drawImage(bmp, vx, vy, im.width * s, im.height * s);
            }});
        }}

        function rc() {{
            s = Math.min(window.innerWidth/im.width, window.innerHeight/im.height)*0.85;
            vx = (window.innerWidth - im.width*s)/2; vy = (window.innerHeight - im.height*s)/2;
            sessionStorage.setItem('v_r', rst); render();
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
