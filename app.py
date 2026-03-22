import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Intentar importar librerías críticas para PDF
try:
    from pdf2image import convert_from_bytes
    pdf_tools_ready = True
except ImportError:
    pdf_tools_ready = False

try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR SEMITRANSPARENCIAS", layout="wide", initial_sidebar_state="expanded")

# CSS: DISEÑO NOVAGE
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 20px; font-weight: bold; text-transform: uppercase; }
    .sidebar-subtitle { color: #8b949e; font-size: 13px; font-style: italic; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; margin-bottom: 8px; display: block; border-left: 3px solid #d4ff00; padding-left: 10px; }
    .warning-box { background-color: #2b2106; color: #e3b341; padding: 12px; border-radius: 8px; border: 1px solid #e3b341; font-weight: bold; text-align: center; margin: 10px; }
    .success-box { background-color: #061f10; color: #3df18d; padding: 12px; border-radius: 8px; border: 1px solid #3df18d; font-weight: bold; text-align: center; margin: 10px; }
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; text-transform: uppercase; height: 3.5em; }
    div.stButton > button:first-child { background-color: #d4ff00 !important; color: black !important; border: none !important; }
    .btn-descarga-png > div > button { background-color: #24a148 !important; color: white !important; }
    .btn-descarga-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state: st.session_state.procesado = False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">PNG, JPG, PDF - Strategia Ink</div>', unsafe_allow_html=True)
    
    st.markdown('<span class="step-label">Paso 1: Carga tu archivo</span>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")
    
    img_orig = None
    if archivo:
        try:
            if archivo.type == "application/pdf":
                if pdf_tools_ready:
                    # Convertir primera página a imagen
                    paginas = convert_from_bytes(archivo.read(), first_page=1, last_page=1)
                    if paginas:
                        img_orig = paginas[0].convert("RGBA")
                else:
                    st.error("Error: Dependencias de PDF no instaladas.")
            else:
                img_orig = Image.open(archivo).convert("RGBA")
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")

    if img_orig:
        datos = np.array(img_orig)
        r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
        
        # Detección
        hay_semi = np.any((a > 0) & (a < 255))
        if hay_semi:
            st.markdown('<div class="warning-box">⚠️ Semitransparencias detectadas.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ IMAGEN LIMPIA</div>', unsafe_allow_html=True)
        
        st.markdown('<span class="step-label">Visualización:</span>', unsafe_allow_html=True)
        opcion_fondo = st.selectbox("Fondo", ["Negro", "Blanco", "Transparente"], label_visibility="collapsed")
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

        st.markdown('<span class="step-label">Paso 2: Configuración</span>', unsafe_allow_html=True)
        dpi_val = st.number_input("DPI", value=300)
        umbral = st.slider("Umbral Alpha", 1, 254, 128)
        
        if st.button("Aplicar Corrección"):
            st.session_state.procesado = True
        
        if st.session_state.procesado:
            nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
            img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
            img_visor = img_final
            
            if st.button("Restaurar"):
                st.session_state.procesado = False
                st.rerun()
            
            st.markdown("---")
            nombre_limpio = archivo.name.rsplit('.', 1)[0].upper()
            
            # Bloque de descarga PNG
            buf_png = io.BytesIO()
            img_final.save(buf_png, format="PNG", dpi=(dpi_val, dpi_val))
            st.markdown('<div class="btn-descarga-png">', unsafe_allow_html=True)
            st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre_limpio}.PNG", "image/png")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Bloque de descarga PDF (Corregido sin fondo negro)
            if pdf_disponible:
                buf_pdf = io.BytesIO()
                p = pdf_canvas.Canvas(buf_pdf, pagesize=A4)
                w_a4, h_a4 = A4
                temp_png = io.BytesIO()
                img_final.save(temp_png, format="PNG")
                temp_png.seek(0)
                img_reader = ImageReader(temp_png)
                iw, ih = img_final.size
                sc = min(w_a4/iw, h_a4/ih) * 0.9
                p.drawImage(img_reader, (w_a4-iw*sc)/2, (h_a4-ih*sc)/2, width=iw*sc, height=ih*sc, mask='auto')
                p.save()
                st.markdown('<div class="btn-descarga-pdf">', unsafe_allow_html=True)
                st.download_button("📄 DESCARGAR PDF", buf_pdf.getvalue(), f"P000 | {nombre_limpio}.PDF", "application/pdf")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            # Previsualización
            vis = datos.copy()
            vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
            img_visor = Image.fromarray(vis)

# --- VISOR ---
if img_orig:
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    st.components.v1.html(f"""
    <style>body {{ margin: 0; background-color: {bg_css}; overflow: hidden; }} .f {{ width: 100vw; height: 100vh; background-image: radial-gradient(#333 1px, transparent 1px); background-size: 20px 20px; display: flex; align-items: center; justify-content: center; }}</style>
    <div class="f"><canvas id="c" style="cursor: move;"></canvas></div>
    <script>
        const c = document.getElementById('c'); const ctx = c.getContext('2d'); const img = new Image();
        img.src = "data:image/png;base64,{img_str}";
        let s=1, vX=0, vY=0, pX, pY, d=false;
        img.onload = () => {{ c.width=window.innerWidth; c.height=window.innerHeight; s=Math.min(c.width/img.width, c.height/img.height)*0.8; vX=(c.width-img.width*s)/2; vY=(c.height-img.height*s)/2; dr(); }};
        function dr() {{ ctx.clearRect(0,0,c.width,c.height); ctx.imageSmoothingEnabled=false; ctx.drawImage(img,vX,vY,img.width*s,img.height*s); }}
        c.onwheel = (e) => {{ e.preventDefault(); s *= e.deltaY > 0 ? 0.9 : 1.1; dr(); }};
        c.onmousedown = (e) => {{ d=true; pX=e.offsetX-vX; pY=e.offsetY-vY; }};
        window.onmouseup = () => d=false;
        c.onmousemove = (e) => {{ if(d) {{ vX=e.offsetX-pX; vY=e.offsetY-pY; dr(); }} }};
    </script>
    """, height=1200)
