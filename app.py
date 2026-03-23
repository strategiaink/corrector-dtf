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

# CSS COMPLETO (Soporta el selector de fondo y diseño lateral)
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

with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR STRATEGIA</div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    if archivo:
        img_input = Image.open(archivo).convert("RGBA")
        pix_orig = np.array(img_input)
        
        # 1. AVISO DE SEMITRANSPARENCIAS
        tiene_semi = np.any((pix_orig[:,:,3] > 0) & (pix_orig[:,:,3] < 255))
        if tiene_semi:
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO</div>', unsafe_allow_html=True)

        # 2. INFORMACIÓN ORIGINAL (REFERENCIA PHOTOSHOP)
        w_px, h_px = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        w_cm_orig = round(w_px * 2.54 / dpi_orig, 2)
        h_cm_orig = round(h_px * 2.54 / dpi_orig, 2)
        
        st.markdown('<span class="step-label">Información Original</span>', unsafe_allow_html=True)
        st.markdown(f"**Resolución:** {w_px} x {h_px} px")
        st.markdown(f"**Densidad:** {dpi_orig} DPI")
        st.markdown(f"**Tamaño:** {w_cm_orig} x {h_cm_orig} cm")

        # 3. CONFIGURACIÓN DEL VISOR (FONDO)
        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fondo_opcion = st.selectbox("Fondo del área de trabajo", ["Negro", "Blanco", "Cuadriculado"])
        colores_fondo = {"Negro": "#000000", "Blanco": "#ffffff", "Cuadriculado": "con-patron"}
        color_v = colores_fondo[fondo_opcion]

        # 4. MEDIDAS DE DESCARGA
        st.markdown('<span class="step-label">1. Medidas de Salida</span>', unsafe_allow_html=True)
        dpi_target = st.number_input("DPI", value=300)
        ancho_cm = st.number_input("Ancho (cm)", value=w_cm_orig)
        alto_cm = st.number_input("Alto (cm)", value=h_cm_orig)

        # 5. UMBRAL (LIMPIEZA AGRESIVA)
        st.markdown('<span class="step-label">2. Umbral de Limpieza</span>', unsafe_allow_html=True)
        umbral = st.slider("Intensidad (Photoshop)", 1, 254, 128)
        
        if st.button("CENTRAR IMAGEN", use_container_width=True):
            st.session_state['rst'] = st.session_state.get('rst', 0) + 1

        # --- PROCESO FINAL SINCRONIZADO ---
        mask = np.where(pix_orig[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_l = Image.fromarray(np.stack([pix_orig[:,:,0], pix_orig[:,:,1], pix_orig[:,:,2], mask], axis=-1))
        fw, fh = int((ancho_cm / 2.54) * dpi_target), int((alto_cm / 2.54) * dpi_target)
        img_final = img_l.resize((fw, fh), resample=Image.LANCZOS)

        st.markdown("---")
        nombre = archivo.name.rsplit('.', 1)[0].upper()
        
        # PNG
        b_png = io.BytesIO()
        img_final.save(b_png, format="PNG", dpi=(dpi_target, dpi_target))
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        st.download_button("📥 DESCARGAR PNG", b_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # PDF
        if pdf_disponible:
            b_pdf = io.BytesIO()
            pw, ph = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
            c = pdf_canvas.Canvas(b_pdf, pagesize=(pw, ph))
            tmp = io.BytesIO(); img_final.save(tmp, format="PNG")
            c.drawImage(ImageReader(tmp), 0, 0, width=pw, height=ph, mask='auto')
            c.save()
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄 DESCARGAR PDF (DTF)", b_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR CON TODAS LAS FUNCIONES ---
if archivo:
    v_buf = io.BytesIO()
    img_input.resize((1000, int(1000 * h_px / w_px))).save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    bg_style = f"background-color: {color_v};"
    if fondo_opcion == "Cuadriculado":
        bg_style = "background-image: linear-gradient(45deg, #222 25%, transparent 25%), linear-gradient(-45deg, #222 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #222 75%), linear-gradient(-45deg, transparent 75%, #222 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; background-color: #111;"

    st.components.v1.html(f"""
    <div id="wrapper" style="{bg_style} width: 100vw; height: 100vh; overflow: hidden; position: relative;">
        <canvas id="c" style="cursor: move;"></canvas>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d'), im = new Image();
        im.src = "data:image/png;base64,{img_b64}";
        let s = parseFloat(sessionStorage.getItem('vs')) || 0, vx = parseFloat(sessionStorage.getItem('vx')) || 0, vy = parseFloat(sessionStorage.getItem('vy')) || 0;
        let rst_in = {st.session_state.get('rst', 0)}, rst_st = parseInt(sessionStorage.getItem('vr')) || 0;
        let offC = document.createElement('canvas'), offX, drag = false, lx, ly;

        im.onload = () => {{
            c.width = window.innerWidth; c.height = window.innerHeight;
            offC.width = im.width; offC.height = im.height; offX = offC.getContext('2d');
            if(s === 0 || rst_in > rst_st) rc(); else render();
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
            s = Math.min(window.innerWidth/im.width, window.innerHeight/im.height)*0.8;
            vx = (window.innerWidth - im.width*s)/2; vy = (window.innerHeight - im.height*s)/2;
            sessionStorage.setItem('vr', rst_in); render();
        }}

        c.onwheel = (e) => {{
            e.preventDefault(); const z = e.deltaY > 0 ? 0.9 : 1.1;
            vx = e.offsetX - (e.offsetX - vx)*z; vy = e.offsetY - (e.offsetY - vy)*z;
            s *= z; sessionStorage.setItem('vs', s); sessionStorage.setItem('vx', vx); sessionStorage.setItem('vy', vy);
            render();
        }};
        c.onmousedown = (e) => {{ drag = true; lx = e.offsetX - vx; ly = e.offsetY - vy; }};
        window.onmouseup = () => drag = false;
        c.onmousemove = (e) => {{ if(drag) {{ vx = e.offsetX - lx; vy = e.offsetY - ly; render(); }} }};
    </script>
    """, height=1000)
