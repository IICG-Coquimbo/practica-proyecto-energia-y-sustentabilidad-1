import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración general de la página
st.set_page_config(
    page_title="Dashboard Energía y Sustentabilidad",
    layout="wide"
)

st.title("Dashboard Ejecutivo - Energía y Sustentabilidad")
st.markdown(
    "Este tablero presenta indicadores estratégicos, tácticos y operacionales "
    "a partir de los datos analizados en el proyecto de energía y sustentabilidad."
)

st.markdown("---")

# Carga de datos
@st.cache_data
def cargar_datos():
    return pd.read_csv("datos_energia_dashboard.csv")

df = cargar_datos()

# Crear pestañas por nivel organizacional
tab_est, tab_tac, tab_op = st.tabs([
    "Nivel Estratégico",
    "Nivel Táctico",
    "Nivel Operacional"
])

# =====================================================
# PESTAÑA 1: NIVEL ESTRATÉGICO
# =====================================================
with tab_est:
    st.header("KPI Estratégico: Participación de capacidad instalada por categoría energética")
    st.caption("Frecuencia: Mensual / Trimestral | Objetivo: evaluar la composición de la matriz energética.")

    total_capacidad = df["capacidad_mw"].sum()

    df_est = df.groupby("categoria_energia")["capacidad_mw"].sum().reset_index()
    df_est["participacion_porcentaje"] = (df_est["capacidad_mw"] / total_capacidad) * 100
    df_est = df_est.sort_values(by="capacidad_mw", ascending=False)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("Capacidad total analizada MW", f"{total_capacidad:,.2f}")
        st.metric("Cantidad de proyectos", len(df))
        st.dataframe(df_est, hide_index=True)

    with col2:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(df_est["categoria_energia"], df_est["participacion_porcentaje"])
        ax.set_title("Participación por categoría energética")
        ax.set_xlabel("Categoría de energía")
        ax.set_ylabel("Participación (%)")

        for i, valor in enumerate(df_est["participacion_porcentaje"]):
            ax.text(i, valor, f"{valor:.1f}%", ha="center", va="bottom")

        st.pyplot(fig)

    st.markdown(
        "Este indicador permite observar si la capacidad instalada se concentra "
        "principalmente en energías renovables o no renovables, apoyando decisiones "
        "de planificación estratégica y sostenibilidad."
    )

# =====================================================
# PESTAÑA 2: NIVEL TÁCTICO
# =====================================================
with tab_tac:
    st.header("KPI Táctico: Capacidad promedio por tecnología")
    st.caption("Frecuencia: Semanal / Mensual | Objetivo: comparar tecnologías energéticas y apoyar decisiones de inversión.")

    tecnologias = sorted(df["tecnologia"].dropna().unique())

    tecnologias_seleccionadas = st.multiselect(
        "Selecciona tecnologías para comparar:",
        options=tecnologias,
        default=tecnologias
    )

    df_filtrado = df[df["tecnologia"].isin(tecnologias_seleccionadas)]

    df_tac = df_filtrado.groupby("tecnologia")["capacidad_mw"].agg(
        cantidad_proyectos="count",
        capacidad_promedio_mw="mean",
        capacidad_minima_mw="min",
        capacidad_maxima_mw="max"
    ).reset_index()

    df_tac = df_tac.sort_values(by="capacidad_promedio_mw", ascending=False)

    st.dataframe(df_tac, hide_index=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df_tac["tecnologia"], df_tac["capacidad_promedio_mw"])
    ax.set_title("Capacidad promedio por tecnología")
    ax.set_xlabel("Capacidad promedio MW")
    ax.set_ylabel("Tecnología")

    st.pyplot(fig)

    st.markdown(
        "Este indicador permite comparar qué tecnologías poseen mayor capacidad promedio, "
        "lo que puede apoyar decisiones tácticas relacionadas con inversión, priorización "
        "de tecnologías y análisis de competitividad energética."
    )

# =====================================================
# PESTAÑA 3: NIVEL OPERACIONAL
# =====================================================
with tab_op:
    st.header("KPI Operacional: Proyectos con baja capacidad instalada")
    st.caption("Frecuencia: Diario / Semanal | Objetivo: identificar proyectos que requieren seguimiento técnico.")

    umbral_capacidad = st.slider(
        "Selecciona el umbral de baja capacidad MW:",
        min_value=1.0,
        max_value=100.0,
        value=20.0,
        step=1.0
    )

    df_op = df[df["capacidad_mw"] < umbral_capacidad].copy()
    df_op = df_op.sort_values(by="capacidad_mw", ascending=True)

    st.warning(f"Se detectaron {len(df_op)} proyectos bajo {umbral_capacidad:.0f} MW.")

    st.dataframe(
        df_op[["item", "pais", "tecnologia", "categoria_energia", "capacidad_mw"]],
        hide_index=True
    )

    df_op_top = df_op.head(20)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df_op_top["item"], df_op_top["capacidad_mw"])
    ax.set_title("Primeros 20 proyectos con menor capacidad instalada")
    ax.set_xlabel("Capacidad MW")
    ax.set_ylabel("Proyecto")

    st.pyplot(fig)

    st.markdown(
        "Este indicador permite identificar proyectos pequeños que podrían necesitar "
        "monitoreo, revisión técnica o evaluación de eficiencia operacional."
    )