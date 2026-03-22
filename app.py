import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Importación de herramientas para PDF
try:
    from pdf2image import convert_from_bytes
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.utils import ImageReader
    pdf_tools_ready = True
except ImportError:
    pdf_tools_ready = False

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR SEMITRANSPARENCIAS", layout="wide")

# CSS: ESTILO NOVAGE
st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    .sidebar-title { color: white; font-size: 22px; font-weight: bold; text-transform: uppercase; }
    .step-label { color: white; font-weight: bold; margin-top: 15px; border-left: 3px solid #d4ff00; padding-left: 10px; }
    .stButton > button { width: 100%; background-color: #d4ff00 !important; color: black !important; font-weight: bold !important; }
    .btn-pdf > div > button { background-color: #d93025 !important; color: white !important; }
    .btn-png > div > button { background-color: #24a148 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state: st.session_state.procesado = False

with st.sidebar:
    st.markdown('<div class="sidebar-title">CORRECTOR SEMITRANSPARENCIAS</div>', unsafe_allow_html=True)
    st.markdown('<span class="step-label">Paso 1: Carga (PNG, JPG o PDF)</span>', unsafe_allow_html=True)
    archivo = st.file_uploader("Subir", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")
    
    img_orig = None
    if archivo:
        try:
            if archivo.type == "application/pdf":
                # Convertimos solo la primera página para procesar
                images = convert_from_bytes(archivo.read(), first_page=1, last_page=1)
                img_orig = images[0].convert("RGBA")
            else:
                img_orig = Image.open(archivo).convert("RGBA")
        except Exception as e:
            st.error(f"Error: Instala poppler-utils en packages.txt. Detalle: {e}")

    if img_orig:
        datos = np.array(img_orig)
        a = datos[:,:,3]
        
        st.markdown('<span class="step-label">Paso 2: Ajustes</span>', unsafe_allow_html=True)
        dpi_val = st.number_input("DPI de salida", value=300)
        umbral = st.slider("Umbral de transparencia", 1, 254, 128)
        
        if st.button("Aplicar Corrección"):
            st.session_state.procesado = True

        if st.session_state.procesado:
            # Corrección Alpha Binario
            nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
            img_final = Image.fromarray(np.stack([datos[:,:,0], datos[:,:,1], datos[:,:,2], nuevo_a], axis=-1))
            
            st.markdown("---")
            nombre = archivo.name.rsplit('.', 1)[0].upper()
            
            # DESCARGA PNG
            buf_png = io.BytesIO()
            img_final.save(buf_png, format="PNG", dpi=(dpi_val, dpi_val))
            st.markdown('<div class="btn-png">', unsafe_allow_html=True)
            st.download_button("📥 PNG SIN GHOST PIXELS", buf_png.getvalue(), f"P000 | {nombre}.PNG", "image/png")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # DESCARGA PDF (CORREGIDO: Tamaño original y sin fondo negro)
            buf_pdf = io.BytesIO()
            # Calcular tamaño en puntos (1px = 72/DPI pts)
            w_pts, h_pts = (img_final.size[0] * 72 / dpi_val), (img_final.size[1] * 72 / dpi_val)
            p = pdf_canvas.Canvas(buf_pdf, pagesize=(w_pts, h_pts))
            
            # Usar un buffer temporal para la imagen con transparencia
            img_tmp = io.BytesIO()
            img_final.save(img_tmp, format="PNG")
            img_tmp.seek(0)
            
            p.drawImage(ImageReader(img_tmp), 0, 0, width=w_pts, height=h_pts, mask='auto')
            p.save()
            st.markdown('<div class="btn-pdf">', unsafe_allow_html=True)
            st.download_button("📄 PDF PARA IMPRESIÓN", buf_pdf.getvalue(), f"P000 | {nombre}.PDF", "application/pdf")
            st.markdown('</div>', unsafe_allow_html=True)

# VISOR (Previsualización)
if img_orig:
    # Si no está procesado, mostramos Ghost Pixels en magenta
    if not st.session_state.procesado:
        vis = np.array(img_orig)
        vis[(vis[:,:,3] > 0) & (vis[:,:,3] < 255)] = [255, 0, 255, 255]
        img_visor = Image.fromarray(vis)
    else:
        img_visor = img_final
        
    st.image(img_visor, use_container_width=True, caption="Previsualización de Calidad")
