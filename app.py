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

# CSS - DISEÑO LATERAL Y BOTONES
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

PRESETS = {
    "Personalizado": None,
    "A2 (42 x 59.4 cm)": (42.0, 59.4),
    "A3 (29.7 x 42 cm)": (29.7, 42.0),
    "A4 (21 x 29.7 cm)": (21.0, 29.7)
}

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
        w_cm_o, h_cm_o = round(w_px * 2.54 / dpi_orig, 2), round(h_px * 2.54 / dpi_orig, 2)
        st.markdown('<span class="step-label">Información Original</span>', unsafe_allow_html=True)
        st.write(f"📏 {w_px}x{h_px}px | {dpi_orig}DPI | {w_cm_o}x{h_cm_o}cm")

        # 3. CONFIGURACIÓN VISOR
        st.markdown('<span class="step-label">Configuración del Visor</span>', unsafe_allow_html=True)
        fondo_opcion = st.selectbox("Fondo", ["Cuadriculado", "Negro", "Blanco"])
        
        # 4. MEDIDAS (ESTO SOLO AFECTA A LA DESCARGA)
        st.markdown('<span class="step-label">1. Medidas de Salida</span>', unsafe_allow_html=True)
        preset = st.selectbox("Presets:", list(PRESETS.keys()))
        unidad = st.radio("Unidad:", ["Centímetros", "Píxeles"], horizontal=True)
        dpi_target = st.number_input("DPI de salida", value=int(dpi_orig))
        
        if preset != "Personalizado":
            ancho_cm, alto_cm = PRESETS[preset]
        else:
            if unidad == "Centímetros":
                ancho_cm, alto_cm = st.number_input("Ancho (cm)", value=w_cm_o), st.number_input("Alto (cm)", value=h_cm_o)
            else:
                ancho_px, alto_px = st.number_input("Ancho (px)", value=w_px), st.number_input("Alto (px)", value=h_px)
                ancho_cm, alto_cm = (ancho_px * 2.54) / dpi_target, (alto_px * 2.54) / dpi_target

        # 5. UMBRAL
        st.markdown('<span class="step-label">2. Umbral de Limpieza</span>', unsafe_allow_html=True)
        umbral = st.slider("Intensidad (0 = Desactivado)", 0, 254, 0)
        
        if st.button("CENTRAR IMAGEN", use_container_width=True):
            st.session_state['rst'] += 1

        st.markdown("---")
        nombre = archivo.name.rsplit('.', 1)[0].upper()
        
        # --- LÓGICA DE PROCESAMIENTO PESADO SÓLO AL TOCAR BOTONES ---
        def preparar_imagen():
            fw, fh = int((ancho_cm / 2.54) * dpi_target), int((alto_cm / 2.54) * dpi_target)
            img_res = img_input.resize((fw, fh), resample=Image.LANCZOS)
            if umbral > 0:
                pix_f = np.array(img_res)
                new_a = np.where(pix_f[:,:,3] < umbral, 0, 255).astype(np.uint8)
                return Image.fromarray(np.stack([pix_f[:,:,0], pix_f[:,:,1], pix_f[:,:,2], new_a], axis=-1))
            return img_res

        # BOTONES DE DESCARGA
        st.markdown('<div class="btn-png">', unsafe_allow_html=True)
        if st.button("📥 DESCARGAR PNG"):
            img_final = preparar_imagen()
            b_png = io.BytesIO()
            img_final.save(b_png, format="PNG", dpi=(dpi_target, dpi_target))
            st.download_button("Click para guardar PNG", b_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if pdf_disponible:
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            if st.button("📄 GENERAR PDF (DTF)"):
                img_final = preparar_imagen()
                b_pdf = io.BytesIO()
                pw, ph = (img_final.size[0] * 72 / dpi_target), (img_final.size[1] * 72 / dpi_target)
                c = pdf_canvas.Canvas(b_pdf, pagesize=(pw, ph)); tmp = io.BytesIO(); img_final.save(tmp, format="PNG")
                c.drawImage(ImageReader(tmp), 0, 0, width=pw, height=ph, mask='auto'); c.save()
                st.download_button("Click para guardar PDF", b_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR LIVIANO (96 DPI / MAX 1200PX) ---
if archivo:
    v_buf = io.BytesIO()
    # Generamos miniatura liviana solo para el visor
    max_v = 1200
    if w_px > max_v or h_px > max_v:
        r = max_v / max(w_px, h_px)
        img_v = img_input.resize((int(w_px*r), int(h_px*r)), resample=Image.NEAREST)
    else: img_v = img_input
    
    img_v.save(v_buf, format="PNG")
    img_b64 = base64.b64encode(v_buf.getvalue()).decode()
    
    colores = {"Negro": "#000", "Blanco": "#fff"}
    bg_style = f"background-color: {colores.get(fondo_opcion, '#000')};"
    if fondo_opcion == "Cuadriculado":
        bg_style = "background-image: linear-gradient(45deg, #222 25%, transparent 25%), linear-gradient(-45deg, #222 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #222 75%), linear-gradient(-45deg, transparent 75%, #222 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0px; background-color: #111;"

    st.components.v1.html(f"""
    <div style="{bg_style} width: 100vw; height: 100vh; overflow: hidden; position: relative;">
        <canvas id="c" style="cursor: move;"></canvas>
    </div>
    <script>
        const c = document.getElementById('c'), x = c.getContext('2d'), im = new Image();
        im.src = "data:image/png;base64,{img_b64}";
        let s = parseFloat(sessionStorage.getItem('vs')) || 0, vx = parseFloat(sessionStorage.getItem('vx')) || 0, vy = parseFloat(sessionStorage.getItem('vy')) || 0;
        let rst_in = {st.session_state['rst']}, rst_st = parseInt(sessionStorage.getItem('vr')) || 0;
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
            if (t > 0) {{ for (let i = 3; i < d.length; i += 4) d[i] = d[i] < t ? 0 : 255; }}
            createImageBitmap(id).then(bmp => {{
                x.clearRect(0, 0, c.width, c.height);
                x.imageSmoothingEnabled = false; // PIXEL REAL
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
