from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parents[1]
SEMANA14_SALIDAS = PROJECT_ROOT / "semanas" / "Semana 14 Storytelling Huella Carbono" / "salidas"


st.set_page_config(page_title="Dashboard Huella de Carbono", layout="wide")
st.title("Cuadro de Mando Integral - Huella de Carbono")
st.markdown("---")


@st.cache_data
def cargar_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    estrategico = pd.read_csv(SEMANA14_SALIDAS / "kpi_estrategico_regiones.csv")
    tactico = pd.read_csv(SEMANA14_SALIDAS / "kpi_tactico_tecnologias.csv")
    operacional = pd.read_csv(SEMANA14_SALIDAS / "kpi_operacional_alertas.csv")
    return estrategico, tactico, operacional


df_est, df_tac, df_op = cargar_datos()
sns.set_theme(style="whitegrid")

tab_est, tab_tac, tab_op = st.tabs(
    [
        "Nivel Estrategico",
        "Nivel Tactico",
        "Nivel Operacional",
    ]
)

with tab_est:
    st.header("Concentracion de emisiones por region")
    st.caption("Frecuencia: mensual / trimestral | Objetivo: priorizar territorios con mayor riesgo ambiental")

    top_region = df_est.iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("Regiones analizadas", len(df_est))
    col2.metric("Region con mayor participacion", top_region["region"])
    col3.metric("Participacion lider", f"{top_region['participacion_emisiones_pct']:.1f}%")

    top_n = st.slider("Cantidad de regiones a visualizar", 5, min(20, len(df_est)), 10)
    df_est_vista = df_est.head(top_n)

    col_tabla, col_grafico = st.columns([1, 2])
    with col_tabla:
        st.dataframe(df_est_vista, hide_index=True)
    with col_grafico:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(
            data=df_est_vista,
            x="participacion_emisiones_pct",
            y="region",
            hue="region",
            palette="Reds_r",
            legend=False,
            ax=ax,
        )
        ax.set_xlabel("Participacion en emisiones totales (%)")
        ax.set_ylabel("Region")
        sns.despine(left=True, bottom=False)
        st.pyplot(fig)

with tab_tac:
    st.header("Dispersion de intensidad de carbono por tecnologia")
    st.caption("Frecuencia: semanal | Objetivo: comparar tecnologias y definir acciones de mejora")

    tecnologias = df_tac["tecnologia"].dropna().unique().tolist()
    seleccion = st.multiselect("Filtrar tecnologias", options=tecnologias, default=tecnologias)
    df_tac_vista = df_tac[df_tac["tecnologia"].isin(seleccion)].copy()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(df_tac_vista, hide_index=True)
    with col2:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.vlines(
            x=df_tac_vista["tecnologia"],
            ymin=df_tac_vista["intensidad_minima"],
            ymax=df_tac_vista["intensidad_maxima"],
            colors="#90A4AE",
            alpha=0.8,
            linewidth=3,
        )
        ax.scatter(df_tac_vista["tecnologia"], df_tac_vista["intensidad_promedio"], color="#1A237E", s=120)
        ax.set_ylabel("kg CO2 / MWh")
        ax.set_xlabel("Tecnologia")
        plt.xticks(rotation=30, ha="right")
        sns.despine(left=True)
        st.pyplot(fig)

with tab_op:
    st.header("Alertas operacionales de alta huella")
    st.caption("Frecuencia: diaria | Objetivo: detectar casos de alto impacto que requieren revision inmediata")

    intensidad_min = st.slider("Umbral de intensidad critica (kg CO2 / MWh)", 400, 1200, 500, 50)
    generacion_min = st.number_input("Generacion minima para considerar alerta (MWh)", value=0.0, step=100000.0)

    alertas = df_op[
        (df_op["intensidad_kgco2_mwh"] >= intensidad_min)
        & (df_op["generacion_mwh"] >= generacion_min)
    ].copy()

    st.warning(f"Se detectaron {len(alertas)} alertas criticas con los umbrales seleccionados.")

    col1, col2 = st.columns([1, 2])
    with col1:
        columnas = ["region", "periodo", "tecnologia", "generacion_mwh", "emisiones_tco2", "intensidad_kgco2_mwh"]
        st.dataframe(alertas[columnas], hide_index=True)
    with col2:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.scatterplot(
            data=df_op,
            x="generacion_mwh",
            y="intensidad_kgco2_mwh",
            hue="tecnologia",
            alpha=0.65,
            s=80,
            ax=ax,
        )
        sns.scatterplot(
            data=alertas,
            x="generacion_mwh",
            y="intensidad_kgco2_mwh",
            color="crimson",
            edgecolor="black",
            s=140,
            label="Alertas filtradas",
            ax=ax,
        )
        ax.axhline(intensidad_min, color="crimson", linestyle="--", alpha=0.7)
        ax.set_xlabel("Generacion electrica (MWh)")
        ax.set_ylabel("Intensidad kg CO2 / MWh")
        sns.despine(left=True)
        st.pyplot(fig)
