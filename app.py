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
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide")

# CSS: ESTILO INTERFAZ
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 22px; font-weight: bold; text-transform: uppercase; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; }
    .stButton > button { width: 100%; background-color: #d4ff00 !important; color: black !important; font-weight: bold !important; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR STRATEGIA</div>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir Imagen", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
    
    img_final_objeto = None # Variable local para evitar el AttributeError

    if archivo:
        img_input = Image.open(archivo).convert("RGBA")
        ancho_orig, alto_orig = img_input.size
        dpi_orig = img_input.info.get('dpi', (72, 72))[0]
        
        st.markdown('<span class="step-label">Tamaño de Imagen</span>', unsafe_allow_html=True)
        unidad = st.selectbox("Unidad", ["Píxeles", "Centímetros"], index=1)
        
        col1, col2 = st.columns(2)
        with col1:
            if unidad == "Centímetros":
                val_ancho = st.number_input("Anchura", value=float(ancho_orig * 2.54 / dpi_orig))
            else:
                val_ancho = st.number_input("Anchura", value=int(ancho_orig))
        with col2:
            mantener = st.checkbox("🔗", value=True)
            
        if unidad == "Centímetros":
            val_alto = st.number_input("Altura", value=float(alto_orig * 2.54 / dpi_orig) if mantener else 0.0)
            dpi_target = st.number_input("Resolución (DPI)", value=300)
            new_w, new_h = int((val_ancho / 2.54) * dpi_target), int((val_alto / 2.54) * dpi_target)
        else:
            val_alto = st.number_input("Altura", value=int(alto_orig))
            dpi_target = st.number_input("DPI", value=int(dpi_orig))
            new_w, new_h = int(val_ancho), int(val_alto)

        umbral = st.slider("Umbral Alpha", 1, 254, 128)
        opcion_fondo = st.selectbox("Fondo Visor", ["Negro", "Blanco", "Transparente"])
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

        if st.button("CORREGIR Y REDIMENSIONAR"):
            # Procesamiento
            img_resampled = img_input.resize((new_w, new_h), resample=Image.LANCZOS)
            datos = np.array(img_resampled)
            nuevo_a = np.where(datos[:,:,3] < umbral, 0, 255).astype(np.uint8)
            img_final_objeto = Image.fromarray(np.stack([datos[:,:,0], datos[:,:,1], datos[:,:,2], nuevo_a], axis=-1))
            st.session_state['temp_img'] = img_final_objeto # Guardado seguro
            st.success("✅ ¡Procesado!")

        if 'temp_img' in st.session_state:
            img_final_objeto = st.session_state['temp_img']
            nombre = archivo.name.rsplit('.', 1)[0].upper()
            
            # Botón PNG
            buf_png = io.BytesIO()
            img_final_objeto.save(buf_png, format="PNG", dpi=(dpi_target, dpi_target))
            st.markdown('<div class="btn-png">', unsafe_allow_html=True)
            st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Botón PDF
            if pdf_disponible:
                buf_pdf = io.BytesIO()
                w_pts, h_pts = (img_final_objeto.size[0] * 72 / dpi_target), (img_final_objeto.size[1] * 72 / dpi_target)
                p = pdf_canvas.Canvas(buf_pdf, pagesize=(w_pts, h_pts))
                tmp = io.BytesIO()
                img_final_objeto.save(tmp, format="PNG")
                p.drawImage(ImageReader(tmp), 0, 0, width=w_pts, height=h_pts, mask='auto')
                p.save()
                st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
                st.download_button("📄 DESCARGAR PDF", buf_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
                st.markdown('</div>', unsafe_allow_html=True)

# --- VISOR ---
if archivo:
    if 'temp_img' in st.session_state:
        img_visor = st.session_state['temp_img']
    else:
        # Previsualización Ghost Pixels
        vis = np.array(img_input)
        vis[(vis[:,:,3] > 0) & (vis[:,:,3] < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)

    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.components.v1.html(f"""
    <div style="background-color: {bg_css}; width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px;">
        <canvas id="canvas" style="cursor: move;"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";
        let scale = 1, vX = 0, vY = 0, pX, pY, down = false;
        img.onload = () => {{
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            scale = Math.min(canvas.width/img.width, canvas.height/img.height) * 0.8;
            vX = (canvas.width - img.width*scale)/2; vY = (canvas.height - img.height*scale)/2;
            draw();
        }};
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, vX, vY, img.width*scale, img.height*scale);
        }}
        canvas.onwheel = (e) => {{ e.preventDefault(); scale *= e.deltaY > 0 ? 0.9 : 1.1; draw(); }};
        canvas.onmousedown = (e) => {{ down = true; pX = e.offsetX - vX; pY = e.offsetY - vY; }};
        window.onmouseup = () => down = false;
        canvas.onmousemove = (e) => {{ if(down) {{ vX = e.offsetX - pX; vY = e.offsetY - pY; draw(); }} }};
    </script>
    """, height=1200)
