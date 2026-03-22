import streamlit as st
import numpy as np
from PIL import Image
import io

# Configuración de la interfaz estilo Novage
st.set_page_config(page_title="Corrector de Imágenes Novage", layout="wide")

# CSS para copiar el look exacto: fondo oscuro, botones amarillos y paneles
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
    .stButton > button { 
        width: 100%; 
        background-color: #d4ff00; 
        color: black; 
        font-weight: bold; 
        border-radius: 10px;
        border: none;
    }
    .stButton > button:hover { background-color: #e5ff5e; color: black; }
    .stAlert { background-color: #1f1906; border: 1px solid #ffd33d; color: #ffd33d; }
    h1, h2, h3 { color: white; font-family: 'sans-serif'; }
    </style>
    """, unsafe_allow_html=True)

# Panel Lateral (Paso 1 y 2)
st.sidebar.title("Corrector de Imágenes Novage")
st.sidebar.caption("Elimina semitransparencias para impresión DTF")

st.sidebar.subheader("Paso 1: Carga tu imagen (PNG)")
archivo = st.sidebar.file_uploader("Seleccionar archivo", type=["png"], label_visibility="collapsed")

if archivo:
    img = Image.open(archivo).convert("RGBA")
    datos = np.array(img)
    a = datos[:,:,3]
    
    # Alerta de semitransparencias (Look Novage)
    if np.any((a > 0) & (a < 255)):
        st.sidebar.warning("⚠️ Tiene semitransparencias.")
    
    st.sidebar.subheader("Paso 2: Ajusta la corrección")
    
    dpi_orig = img.info.get('dpi', (300, 300))[0]
    st.sidebar.number_input("DPI Original del Archivo", value=int(dpi_orig))
    
    umbral = st.sidebar.slider("Sensibilidad de corrección", 1, 254, 25, 
                               help="Valor bajo es más suave, uno alto es más agresivo.")
    
    st.sidebar.info(f"Valor: {umbral}. Un valor bajo es más suave, uno alto es más agresivo.")
    
    estilo = st.sidebar.selectbox("Estilo de corrección", ["Moderado (Recomendado)", "Agresivo"])

    # Procesamiento de imagen
    r, g, b = datos[:,:,0], datos[:,:,1], datos[:,:,2]
    nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
    img_limpia = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
    
    # Vista de bordes Magenta (Look Novage)
    vis_mag = datos.copy()
    mask_semi = (a > 0) & (a < 255)
    vis_mag[mask_semi] = [255, 0, 255, 255] # Magenta sólido en bordes
    img_mag = Image.fromarray(vis_mag)

    # Cuerpo Principal
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bordes detectados (Magenta)")
        st.image(img_mag, use_container_width=True)
    with col2:
        st.subheader("Resultado Limpio")
        st.image(img_limpia, use_container_width=True)
        
    # Botón de Descarga
    nombre_base = archivo.name.rsplit('.', 1)[0].upper()
    nombre_final = f"P000 | {nombre_base}.PNG"
    
    buf = io.BytesIO()
    img_limpia.save(buf, format="PNG", dpi=(dpi_orig, dpi_orig))
    
    st.sidebar.markdown("---")
    st.sidebar.download_button(
        label="📥 DESCARGAR RESULTADO LIMPIO",
        data=buf.getvalue(),
        file_name=nombre_final,
        mime="image/png"
    )
else:
    st.info("Subí un archivo PNG en el panel de la izquierda para empezar.")
