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

st.set_page_config(page_title="CORRECTOR STRATEGIA INK v20.0", layout="wide", initial_sidebar_state="expanded")

# CSS - MANTIENE DISEÑO
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    .status-box { padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 15px; text-align: center; border: 1px solid; }
    .status-dirty { background-color: rgba(255, 165, 0, 0.1); border-color: orange; color: orange; }
    .status-clean { background-color: rgba(36, 161, 72, 0.1); border-color: #24a148; color: #24a148; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; width: 100%; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; width: 100%; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

if 'rst' not in st.session_state: st.session_state['rst'] = 0

with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR STRATEGIA</div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        img_input = Image.open(archivo).convert("RGBA")
        pix_orig = np.array(img_input)
        
        # 1. ESTADO
        tiene_semi = np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255))
        if tiene_semi:
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO</div>', unsafe_allow_html=True)

        # 2. INFO ORIGINAL
        w_px, h_px = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        st.markdown('<span class="step-label">Información Original</span>', unsafe_allow_html=True)
        st.write(f"📏 {w_px}x{h_px}px | {dpi_orig}DPI")

        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fondo_opcion = st.selectbox("Fondo", ["Cuadriculado", "Negro", "Blanco"])
        
        # 3. UMBRAL BINARIO DURO (LIMPIEZA REAL)
        st.markdown('<span class="step-label">Umbral de Limpieza (Alpha Binario)</span>', unsafe_allow_html=True)
        umbral = st.slider("Corte de transparencia", 0, 254, 128)
        
        if st.button("CENTRAR IMAGEN", use_container_width=True):
            st.session_state['rst'] += 1

        st.markdown("---")
        nombre = archivo.name.rsplit('.', 1)[0].upper()
        
        # PROCESAMIENTO BINARIO PARA DESCARGA
        pix_f = np.array(img_input)
        # Forzado de Alpha: o es 0 o es 255. Sin grises.
        new_a = np.where(pix_f[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([pix_f[:,:,0], pix_f[:,:,1], pix_f[:,:,2], new_a], axis=-1))

        b_png = io.BytesIO()
        img_final.save(b_png, format="PNG", dpi=(dpi_orig, dpi_orig))
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        st.download_button("📥 DESCARGAR PNG", b_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            b_pdf = io.BytesIO()
            pw, ph = (img_final.size[0] * 72 / dpi_orig), (img_final.size[1] * 72 / dpi_orig)
            c = pdf_canvas.Canvas(b_pdf, pagesize=(pw, ph)); tmp = io.BytesIO(); img_final.save(tmp, format="PNG")
            c.drawImage(ImageReader(tmp), 0, 0, width=pw, height=ph, mask='auto'); c.save()
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄 DESCARGAR PDF (DTF)", b_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR DE PÍXEL REAL (SIN SUAVIZADO) ---
if archivo:
    v_buf = io.BytesIO()
    img_input.save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    bg_style = "background-image: linear-gradient(45deg, #222 25%, transparent 25%), linear-gradient(-45deg, #222 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #222 75%), linear-gradient(-45deg, transparent 75%, #222 75%); background-size: 20px 20px; background-color: #111;"
    if fondo_opcion == "Negro": bg_style = "background-color: #000;"
    if fondo_opcion == "Blanco": bg_style = "background-color: #fff;"

    st.components.v1.html(f"""
    <div style="{bg_style} width: 100vw; height: 100vh; overflow: hidden; position: relative;">
        <canvas id="c" style="cursor: move; image-rendering: pixelated;"></canvas>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d', {{alpha: true}}), im = new Image();
        im.src = "data:image/png;base64,{img_b64}";
        let s, vx, vy, drag = false, lx, ly, rst_in = {st.session_state['rst']};
        let offC = document.createElement('canvas'), offX;

        im.onload = () => {{
            c.width = window.innerWidth; c.height = window.innerHeight;
            offC.width = im.width; offC.height = im.height; offX = offC.getContext('2d');
            let st_s = parseFloat(sessionStorage.getItem('vs')), st_r = parseInt(sessionStorage.getItem('vr')) || 0;
            if(!st_s || rst_in > st_r) rc(); else {{ s=st_s; vx=parseFloat(sessionStorage.getItem('vx')); vy=parseFloat(sessionStorage.getItem('vy')); render(); }}
        }};

        function render() {{
            offX.clearRect(0, 0, offC.width, offC.height);
            offX.drawImage(im, 0, 0);
            let id = offX.getImageData(0, 0, offC.width, offC.height), d = id.data, t = {umbral};
            // LIMPIEZA BINARIA PURA EN EL VISOR
            for (let i = 3; i < d.length; i += 4) d[i] = d[i] < t ? 0 : 255;
            createImageBitmap(id).then(bmp => {{
                x.clearRect(0, 0, c.width, c.height);
                x.imageSmoothingEnabled = false; // DESACTIVA EL SUAVIZADO DEL NAVEGADOR
                x.drawImage(bmp, vx, vy, im.width * s, im.height * s);
            }});
        }}
        function rc() {{
            s = Math.min(window.innerWidth/im.width, window.innerHeight/im.height)*0.8;
            vx = (window.innerWidth - im.width*s)/2; vy = (window.innerHeight - im.height*s)/2;
            sessionStorage.setItem('vs', s); sessionStorage.setItem('vx', vx); sessionStorage.setItem('vr', rst_in); render();
        }}
        c.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vx = e.offsetX - (e.offsetX - vx)*z; vy = e.offsetY - (e.offsetY - vy)*z;
            s *= z; sessionStorage.setItem('vs', s); sessionStorage.setItem('vx', vx); sessionStorage.setItem('vy', vy); render();
        }};
        c.onmousedown = (e) => {{ drag = true; lx = e.offsetX - vx; ly = e.offsetY - vy; }};
        window.onmouseup = () => drag = false;
        c.onmousemove = (e) => {{ if(drag) {{ vx = e.offsetX - lx; vy = e.offsetY - ly; render(); }} }};
    </script>
    """, height=1000)
