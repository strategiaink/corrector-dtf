import streamlit as st
import numpy as np
from PIL import Image
import io

# Configuración visual
st.set_page_config(page_title="CORRECTOR DTF PRO", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div.stButton > button { width: 100%; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛠️ MI LIMPIADOR DTF PERSONAL")

# 1. Carga de archivo
archivo = st.file_uploader("Sube tu archivo PNG aquí", type=["png"])

if archivo:
    img = Image.open(archivo).convert("RGBA")
    nombre_base = archivo.name.rsplit('.', 1)[0].upper()
    
    # 2. Controles en barra lateral
    st.sidebar.header("AJUSTES DE LIMPIEZA")
    umbral = st.sidebar.slider("SENSIBILIDAD UMBRAL", 1, 254, 128)
    
    # 3. Procesamiento
    datos = np.array(img)
    r, g, b, a = datos[:,:,0], datos[:,:,1], datos[:,:,2], datos[:,:,3]
    
    # Aplicar Umbral (Limpieza)
    nuevo_a = np.where(a < umbral, 0, 255).astype(np.uint8)
    img_limpia = Image.fromarray(np.stack([r, g, b, nuevo_a], axis=-1))
    
    # Magenta para detección
    vis_mag = datos.copy()
    vis_mag[(a > 0) & (a < 255)] = [255, 0, 255, 255]
    img_mag = Image.fromarray(vis_mag)
    
    # 4. Mostrar imágenes (con opción de zoom nativo de Streamlit)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bordes a Limpiar (Magenta)")
        st.image(img_mag, use_container_width=True)
    with col2:
        st.subheader("Resultado Final Sólido")
        st.image(img_limpia, use_container_width=True)
        
    # 5. Descarga con formato solicitado
    nombre_final = f"P000 | {nombre_base}.PNG"
    buf = io.BytesIO()
    img_limpia.save(buf, format="PNG", dpi=img.info.get('dpi'), compress_level=0)
    
    st.download_button(
        label="📥 DESCARGAR RESULTADO LIMPIO",
        data=buf.getvalue(),
        file_name=nombre_final,
        mime="image/png"
    )
