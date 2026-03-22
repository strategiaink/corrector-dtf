import streamlit as st
import numpy as np
from PIL import Image
import io
import base64

# Intentar importar reportlab para el PDF
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    from reportlab.lib.pagesizes import A4
    pdf_disponible = True
except ImportError:
    pdf_disponible = False

# CONFIGURACIÓN DE PÁGINA - Layout Wide es clave
st.set_page_config(page_title="CORRECTOR NOVAGE v4.0", layout="wide", initial_sidebar_state="expanded")

# CSS: ESTO ELIMINA EL RECUADRO LIMITADO
st.markdown("""
    <style>
    /* Eliminar scroll del cuerpo principal y paddings de Streamlit */
    .main { overflow: hidden; }
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important; 
        padding-left: 0rem !important; 
        padding-right: 0rem !important; 
        max-width: 100% !important; 
    }
    
    /* Sidebar Novage */
    [data-testid="stSidebar"] { background-color: #111418; min-width: 350px !important; }
    
    /* Estilos de Carteles */
    .warning-box { background-color: #2b2106; color: #e3b341; padding: 12px; border-radius: 8px; border: 1px solid #e3b341; font-weight: bold; text-align: center; margin: 15px 10px; }
    .success-box { background-color: #061f10; color: #3df18d; padding: 12px; border-radius: 8px; border: 1px solid #3df18d; font-weight: bold; text-align: center; margin: 15px 10px; }

    /* Botones */
    .stButton > button { width: 100%; border-radius: 8px !important; font-weight: bold !important; text-transform: uppercase; height: 3.5em; }
    div.stButton > button:first-child { background-color: #d4ff00 !important; color: black !important; border: none !important; }
    .btn-descarga-png > div > button { background-color: #24a148 !important; color: white !important; }
    .btn-descarga-pdf > div > button { background-color: #d93025 !important; color: white !important; }

    /* EL CONTENEDOR: Forzamos el alto al 100% de la ventana visible */
    .mesa-trabajo-full {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 0;
    }
    
    header, footer { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)

if 'procesado' not in st.session_state: st.session_state.procesado = False

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('<div style="color:white; font-size:24px; font-weight:bold;">Corrector Novage</div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#8b949e; font-size:14px; font-style:italic; margin-bottom:20px;">Strategia Ink Edition</div>', unsafe_allow_html=True)
    
    archivo = st.file_uploader("Cargar PNG", type=["png"], label_visibility="collapsed")
    
    if archivo:
        img_orig = Image.open(archivo).convert("RGBA")
        datos = np.array(img_orig)
        r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
        
        hay_semi = np.any((a > 0) & (a < 255))
        if hay_semi:
            st.markdown('<div class="warning-box">⚠️ Tiene semitransparencias.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="success-box">✅ IMAGEN LIMPIA</div>', unsafe_allow_html=True)
        
        st.markdown('<b style="color:white;">Fondo del Visor:</b>', unsafe_allow_html=True)
        opcion_fondo = st.selectbox("Fondo", ["Negro", "Blanco", "Transparente"], label_visibility="collapsed")
        bg_css = {"Transparente": "transparent", "Blanco": "#ffffff", "Negro": "#000000"}[opcion_fondo]

        st.markdown("---")
        umbral = st.slider("Umbral de Sensibilidad", 1, 254, 128)
        dpi_val = st.number_input("DPI", value=300)
        
        if st.button("Aplicar Corrección"):
            st.session_state.procesado = True
        
        if st.session_state.procesado:
            nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
            img_final = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
            img_visor = img_final
            
            if st.button("Restaurar Cambios"):
                st.session_state.procesado = False
                st.rerun()
            
            st.markdown("---")
            nombre_base = archivo.name.rsplit('.', 1)[0].upper()
            
            buf_png = io.BytesIO()
            img_final.save(buf_png, format="PNG", dpi=(dpi_val, dpi_val))
            st.markdown('<div class="btn-descarga-png">', unsafe_allow_html=True)
            st.download_button("📥 DESCARGAR PNG", buf_png.getvalue(), f"P000 | {nombre_base}.PNG", "image/png")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if pdf_disponible:
                buf_pdf = io.BytesIO()
                p = pdf_canvas.Canvas(buf_pdf, pagesize=A4)
                w_a4, h_a4 = A4
                iw, ih = img_final.size
                sc = min(w_a4/iw, h_a4/ih) * 0.9
                p.drawInlineImage(img_final, (w_a4-iw*sc)/2, (h_a4-ih*sc)/2, width=iw*sc, height=ih*sc)
                p.save()
                st.markdown('<div class="btn-descarga-pdf">', unsafe_allow_html=True)
                st.download_button("📄 DESCARGAR PDF", buf_pdf.getvalue(), f"P000 | {nombre_base}.PDF", "application/pdf")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            vis = datos.copy()
            vis[(a > 0) & (a < 255)] = [255, 0, 255, 255]
            img_visor = Image.fromarray(vis)

# --- VISOR (OCUPA TODO EL ANCHO Y ALTO RESTANTE) ---
if archivo:
    buffered = io.BytesIO()
    img_visor.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # El truco es usar vh (viewport height) directamente en el componente
    st.components.v1.html(f"""
    <style>
        body {{ margin: 0; padding: 0; background-color: {bg_css}; overflow: hidden; }}
        .full-container {{
            width: 100vw; 
            height: 100vh; 
            background-image: radial-gradient(#333 1px, transparent 1px); 
            background-size: 20px 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        canvas {{ cursor: move; }}
    </style>
    <div class="full-container">
        <canvas id="canvas"></canvas>
    </div>
    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const img = new Image();
        img.src = "data:image/png;base64,{img_str}";
        let scale = 1, vX = 0, vY = 0, pX, pY, down = false;

        img.onload = () => {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            scale = Math.min(canvas.width/img.width, canvas.height/img.height) * 0.8;
            vX = (canvas.width - img.width*scale)/2;
            vY = (canvas.height - img.height*scale)/2;
            draw();
        }};
        function draw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(img, vX, vY, img.width*scale, img.height*scale);
        }}
        canvas.onwheel = (e) => {{
            e.preventDefault();
            const z = e.deltaY > 0 ? 0.9 : 1.1;
            scale *= z; draw();
        }};
        canvas.onmousedown = (e) => {{ down = true; pX = e.offsetX - vX; pY = e.offsetY - vY; }};
        window.onmouseup = () => down = false;
        canvas.onmousemove = (e) => {{ if(down) {{ vX = e.offsetX - pX; vY = e.offsetY - pY; draw(); }} }};
        window.onresize = () => {{ canvas.width = window.innerWidth; canvas.height = window.innerHeight; draw(); }};
    </script>
    """, height=1200) # Altura exagerada para que nunca se corte
