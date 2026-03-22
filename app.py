import streamlit as st
import numpy as np
from PIL import Image
import io
import base64
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.pagesizes import A4

# CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="CORRECTOR STRATEGIA INK", layout="wide", initial_sidebar_state="expanded")

# CSS: ESTILO FIEL A LA CAPTURA NOVAGE
st.markdown("""
    <style>
    .main { overflow: hidden; }
    .block-container { padding: 0rem !important; max-width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    
    /* Contenedores de pasos */
    .step-box {
        background-color: #1a1c23;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
    }
    
    /* Títulos y etiquetas */
    .sidebar-title { color: white; font-size: 22px; font-weight: bold; margin-bottom: 5px; }
    .sidebar-subtitle { color: #8b949e; font-size: 14px; margin-bottom: 20px; }
    .step-label { color: white; font-weight: bold; font-style: italic; margin-bottom: 10px; display: block; }
    
    /* Alerta de Semitransparencias */
    .warning-box {
        background-color: #2b2106;
        color: #e3b341;
        padding: 10px;
        border-radius: 6px;
        border: 1px solid #e3b341;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
    }
    
    /* Botones específicos */
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; text-transform: uppercase; height: 3.5em; }
    .btn-aplicar > div > button { background-color: #d4ff00 !important; color: black !important; border: none !important; }
    .btn-reiniciar > div > button { background-color: #3e1a1a !important; color: white !important; border: 1px solid #ff4b4b !important; }
    
    /* Visor */
    .mesa-trabajo {
        width: 100%; height: 98vh; background-color: #0d1117;
        background-image: radial-gradient(#333 1px, transparent 1px);
        background-size: 20px 20px;
        overflow: hidden;
    }
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

# INICIALIZACIÓN DE ESTADOS
if 'procesado' not in st.session_state: st.session_state.procesado = False

# --- SIDEBAR: PANEL DE CONTROL ---
with st.sidebar:
    st.markdown('<div class="sidebar-title">Corrector de Imágenes Novage</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtitle">Elimina semitransparencias para impresión DTF</div>', unsafe_allow_html=True)
    
    # PASO 1: CARGA
    st.markdown('<span class="step-label">Paso 1: Carga tu imagen (PNG)</span>', unsafe_allow_html=True)
    archivo = st.file_uploader("Cargar PNG", type=["png"], label_visibility="collapsed")
    
    if archivo:
        img_orig = Image.open(archivo).convert("RGBA")
        datos = np.array(img_orig)
        r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
        
        # Detección de Semitransparencias
        hay_semi = np.any((a > 0) & (a < 255))
        if hay_semi:
            st.markdown('<div class="warning-box">⚠️ Tiene semitransparencias.</div>', unsafe_allow_html=True)
        
        # SELECTOR DE FONDO (Transparente, Blanco, Negro)
        st.markdown('<span class="step-label">Fondo del Visor:</span>', unsafe_allow_html=True)
        opcion_fondo = st.selectbox("Seleccionar fondo", ["Transparente", "Blanco", "Negro"], label_visibility="collapsed")
        bg_color = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

        st.markdown("---")
        
        # PASO 2: AJUSTES
        st.markdown('<span class="step-label">Paso 2: Ajusta la corrección</span>', unsafe_allow_html=True)
        
        st.write("DPI Original del Archivo")
        dpi_val = st.number_input("DPI", value=300, label_visibility="collapsed")
        
        st.write("Sensibilidad de corrección")
        umbral = st.slider("Umbral", 1, 254, 128, label_visibility="collapsed")
        st.caption(f"Valor: {umbral}. Un valor bajo es más suave, uno alto es más agresivo.")
        
        st.write("Estilo de corrección")
        estilo = st.selectbox("Estilo", ["Moderado (Recomendado)", "Agresivo"], label_visibility="collapsed")
        
        # ACCIONES
        st.markdown('<div class="btn-aplicar">', unsafe_allow_html=True)
        if st.button("Aplicar Corrección"):
            st.session_state.procesado = True
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.procesado:
            # Procesamiento de imagen
            nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
            img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
            img_visor = img_final
            
            st.markdown('<div class="btn-reiniciar">', unsafe_allow_html=True)
            if st.button("Reiniciar y Cargar Otra"):
                st.session_state.procesado = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            # DESCARGAS
            st.markdown("---")
            nombre_base = archivo.name.rsplit('.', 1)[0].upper()
            
            # PNG
            buf_png = io.BytesIO()
            img_final.save(buf_png, format="PNG", dpi=(dpi_val, dpi_val))
            st.download_button(f"📥 Descargar PNG", buf_png.getvalue(), f"P000 | {nombre_base}.PNG", "image/png")
            
            # PDF (ReportLab)
            buf_pdf = io.BytesIO()
            p = pdf_canvas.Canvas(buf_pdf, pagesize=A4)
            width_a4, height_a4 = A4
            # Ajuste de escala simple para PDF
            img_w, img_h = img_final.size
            scale = min(width_a4/img_w, height_a4/img_h) * 0.8
            p.drawInlineImage(img_final, (width_a4-img_w*scale)/2, (height_a4-img_h*scale)/2, width=img_w*scale, height=img_h*scale)
            p.save()
            st.download_button(f"📄 Descargar PDF", buf_pdf.getvalue(), f"P000 | {nombre_base}.PDF", "application/pdf")
            
        else:
            # Modo visualización Magenta para Ghost Pixels
            vis = datos.copy()
            vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
            img_visor = Image.fromarray(vis)

# --- VISOR PRINCIPAL (DERECHA) ---
if archivo:
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html_visor = f"""
    <div class="mesa-trabajo" id="box" style="background-color: {bg_color};">
        <canvas id="canvas" style="cursor: grab; width: 100%; height: 100%;"></canvas>
    </div>
    <script>
        const box = document.getElementById('box');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";

        let scale = 1, viewX = 0, viewY = 0, isPanning = false, startX, startY;

        function init() {{
            canvas.width = box.clientWidth;
            canvas.height = box.clientHeight;
            scale = Math.min(canvas.width / img.width, canvas.height / img.height) * 0.8;
            viewX = (canvas.width - img.width * scale) / 2;
            viewY = (canvas.height - img.height * scale) / 2;
            draw();
        }}
        img.onload = init;
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.save();
            ctx.translate(viewX, viewY);
            ctx.scale(scale, scale);
            ctx.drawImage(img, 0, 0);
            ctx.restore();
        }}
        canvas.onwheel = (e) => {{
            e.preventDefault();
            const zoom = e.deltaY > 0 ? 0.8 : 1.2;
            viewX = e.offsetX - (e.offsetX - viewX) * zoom;
            viewY = e.offsetY - (e.offsetY - viewY) * zoom;
            scale *= zoom;
            draw();
        }};
        canvas.onmousedown = (e) => {{ isPanning = true; startX = e.offsetX - viewX; startY = e.offsetY - viewY; }};
        window.onmouseup = () => isPanning = false;
        canvas.onmousemove = (e) => {{
            if (!isPanning) return;
            viewX = e.offsetX - startX;
            viewY = e.offsetY - startY;
            draw();
        }};
    </script>
    """
    st.components.v1.html(html_visor, height=1000, scrolling=False)
else:
    st.info("Sube un archivo para comenzar.")
