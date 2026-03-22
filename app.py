import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Configuración de ReportLab para el PDF DTF
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS: ESTILOS FIJOS
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; display: block; }
    
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; font-weight: bold !important; height: 3em; margin-top: 10px; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; font-weight: bold !important; height: 3em; margin-top: 10px; }
    
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
        
        # 1. ANALIZADOR DE SEMITRANSPARENCIAS
        pixeles_orig = np.array(img_input)
        alpha_orig = pixeles_orig[:, :, 3]
        if np.any((alpha_orig > 0) & (alpha_orig < 255)):
            st.markdown('<div class="status-box status-dirty">⚠️ TIENE SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-box status-clean">✅ LIMPIO (SIN SEMITRANSPARENCIAS)</div>', unsafe_allow_html=True)

        # 2. CONFIGURACIÓN DEL VISOR (ARRIBA)
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
        
        # 4. CORRECCIÓN AUTOMÁTICA EN TIEMPO REAL
        st.markdown('<span class="step-label">2. Corrección de Bordes</span>', unsafe_allow_html=True)
        umbral = st.slider("Umbral de corte", 1, 254, 128)
        
        # Procesado instantáneo para el visor y descarga
        datos_np = np.array(img_resized)
        nuevo_alpha = np.where(datos_np[:,:,3] < umbral, 0, 255).astype(np.uint8)
        img_final = Image.fromarray(np.stack([datos_np[:,:,0], datos_np[:,:,1], datos_np[:,:,2], nuevo_alpha], axis=-1))

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

# --- VISOR ESTABLE (CORREGIDO) ---
if archivo:
    # Generar string de imagen para el JS
    visor_buf = io.BytesIO()
    img_final.save(visor_buf, format="PNG")
    img_b64 = base64.b64encode(visor_buf.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; position: relative; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <canvas id="canvas" style="cursor: move;"></canvas>
        <button onclick="recenter()" style="position:fixed; bottom:20px; right:20px; padding:12px 20px; background:#d4ff00; border:none; border-radius:8px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 15px rgba(0,0,0,0.5); font-family: sans-serif;">RE-CENTRAR IMAGEN</button>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_b64}";
        
        let scale = 1, viewX = 0, viewY = 0, isDragging = false, lastX, lastY;

        function recenter() {{
            scale = Math.min(window.innerWidth / img.width, window.innerHeight / img.height) * 0.8;
            viewX = (window.innerWidth - img.width * scale) / 2;
            viewY = (window.innerHeight - img.height * scale) / 2;
            render();
        }}

        img.onload = () => {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            recenter();
        }};

        function render() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, viewX, viewY, img.width * scale, img.height * scale);
        }}

        canvas.onwheel = (e) => {{
            e.preventDefault();
            const zoom = e.deltaY > 0 ? 0.9 : 1.1;
            viewX = e.offsetX - (e.offsetX - viewX) * zoom;
            viewY = e.offsetY - (e.offsetY - viewY) * zoom;
            scale *= zoom;
            render();
        }};

        canvas.onmousedown = (e) => {{ isDragging = true; lastX = e.offsetX - viewX; lastY = e.offsetY - viewY; }};
        window.onmouseup = () => isDragging = false;
        canvas.onmousemove = (e) => {{
            if (isDragging) {{
                viewX = e.offsetX - lastX;
                viewY = e.offsetY - lastY;
                render();
            }}
        }};
        window.onresize = () => {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; render(); }};
    </script>
    """, height=1000)
