import streamlit as st
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import fsolve
from streamlit_extras.metric_cards import style_metric_cards

# --- 1. CONFIGURACIÓN DE INTERFAZ DE ALTO NIVEL ---
st.set_page_config(page_title="HDS | Pro Simulation", layout="wide")

# CSS para tipografía 'Inter' y estética de Estación de Trabajo
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .main-title { font-weight: 800; font-size: 3rem; color: #FFFFFF; letter-spacing: -2px; margin-bottom: -10px; }
        .sub-header { color: #666; font-weight: 300; font-size: 1.2rem; margin-bottom: 2rem; }
        section[data-testid="stSidebar"] { background-color: #0E1117; border-right: 1px solid #333; }
    </style>
""", unsafe_allow_html=True)

# --- 2. PANEL DE CONTROL (SIDEBAR) ---
with st.sidebar:
    st.markdown("### 🛠️ PARÁMETROS TÉCNICOS")
    L = st.slider("Longitud Total (pies)", 100, 5000, 1200)
    D_in = st.number_input("Diámetro Interno (pulgadas)", value=2.067, step=0.001)
    Z_delta = st.slider("Carga Estática ΔZ (pies)", 0, 150, 20)
    
    st.markdown("---")
    st.markdown("### 💧 PROPIEDADES DEL FLUIDO")
    visc_op = st.selectbox("Fluido de Proceso", ["Agua @ 20°C", "Aceite SAE 30", "Glicerina"])
    
    # Lógica de constantes físicas
    rho = 62.3 # lb/ft3
    mu = 0.000672 if "Agua" in visc_op else 0.0672 # lb/ft-s simplificado

# --- 3. CORE DE INGENIERÍA (CÁLCULOS) ---
D_ft = D_in / 12
def calc_sistema(Q_gpm):
    if Q_gpm <= 0: return Z_delta
    v = (Q_gpm / 448.831) / (np.pi * (D_ft**2) / 4)
    Re = (rho * v * D_ft) / mu
    # Factor de fricción (Haaland para flujo turbulento)
    f = (1.11 * np.log10(6.9/Re + (0.00015/(3.7*D_ft))**1.11))**-2 if Re > 2300 else 64/Re
    h_f = f * (L/D_ft) * (v**2 / (2 * 32.2))
    return Z_delta + h_f

def curva_bomba(Q): 
    # Modelo cuadrático basado en tus datos de 100, 200, 300 GPM
    return -0.00041*Q**2 + 0.048*Q + 59.5

# Encontrar punto de equilibrio (Cruce de curvas)
Q_op = fsolve(lambda q: curva_bomba(q) - calc_sistema(q), 150)[0]
H_op = calc_sistema(Q_op)

# --- 4. LAYOUT DE RESULTADOS (DASHBOARD) ---
st.markdown('<p class="main-title">Hydraulic Design Suite</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Análisis Dinámico de Sistemas de Bombeo | M5 Engine</p>', unsafe_allow_html=True)

# Tarjetas de KPI
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
col_kpi1.metric("Caudal Operativo", f"{Q_op:.1f} GPM")
col_kpi2.metric("Presión de Descarga", f"{H_op:.1f} ft")
col_kpi3.metric("Eficiencia Est.", "60.0 %", delta="-2.1%")
style_metric_cards(background_color="#161b22", border_left_color="#58a6ff")

# Visualización Gráfica
col_plot1, col_plot2 = st.columns([1, 1])

with col_plot1:
    st.markdown("#### 📈 Curvas de Performance")
    q_range = np.linspace(1, 400, 100)
    fig_op = go.Figure()
    fig_op.add_trace(go.Scatter(x=q_range, y=[curva_bomba(q) for q in q_range], name="Bomba (H-Q)", line=dict(color='#ff4b4b', width=4)))
    fig_op.add_trace(go.Scatter(x=q_range, y=[calc_sistema(q) for q in q_range], name="Sistema", line=dict(color='#00d4ff', width=4)))
    fig_op.add_trace(go.Scatter(x=[Q_op], y=[H_op], mode='markers', marker=dict(size=15, color='white', line=dict(width=2, color='black')), name="Punto de Op."))
    
    fig_op.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                         margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig_op, use_container_width=True)

with col_plot2:
    st.markdown("#### 📐 Isométrico de Energía 3D")
    # Generar trayectoria 3D representativa
    t = np.linspace(0, 1, 100)
    x_3d = np.linspace(0, L, 100)
    z_3d = np.linspace(0, Z_delta, 100)
    presion_gradient = H_op - (H_op - Z_delta) * (x_3d / L) # Caída lineal estimada
    
    fig_3d = go.Figure(data=[go.Scatter3d(
        x=x_3d, y=np.zeros(100), z=z_3d,
        mode='lines',
        line=dict(color=presion_gradient, colorscale='Viridis', width=12,
                  colorbar=dict(title=dict(text="Gradiente Presión", font=dict(size=12), side="right"), thickness=15))
    )])
    
    fig_3d.update_layout(template="plotly_dark", scene=dict(aspectmode='manual', aspectratio=dict(x=2, y=1, z=1)),
                         margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_3d, use_container_width=True)

st.info(f"💡 El sistema está operando a un Reynolds de {(rho * (Q_op/448.83) * D_ft / mu):.0f}. Régimen: Turbulento.")