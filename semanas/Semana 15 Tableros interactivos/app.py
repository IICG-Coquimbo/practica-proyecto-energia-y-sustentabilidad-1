from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st


DATA_PATH = Path(__file__).with_name("datos_energia_dashboard.csv")


st.set_page_config(
    page_title="Dashboard Energia y Sustentabilidad",
    layout="wide",
)


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    columnas_numericas = [
        "periodo",
        "emisiones_co2_mt",
        "generacion_mwh",
        "intensidad_co2",
        "participacion_generacion",
        "intensidad_co2_ajustada",
        "cluster_kmeans",
    ]
    for columna in columnas_numericas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df.dropna(subset=["generacion_mwh", "emisiones_co2_mt", "intensidad_co2_ajustada"])


def formato_numero(valor: float, decimales: int = 1) -> str:
    return f"{valor:,.{decimales}f}".replace(",", ".")


df = cargar_datos()

st.title("Cuadro de Mando Integral - Energia y Sustentabilidad")
st.caption(
    "Dashboard interactivo construido con Streamlit a partir del dataset procesado "
    "de intensidad de emisiones y generacion energetica."
)

tab_est, tab_tac, tab_op = st.tabs(
    [
        "Nivel Estrategico",
        "Nivel Tactico",
        "Nivel Operacional",
    ]
)

with tab_est:
    st.header("Panorama ejecutivo de emisiones y generacion")
    st.caption("Frecuencia: mensual | Objetivo: priorizar el seguimiento ambiental.")

    total_registros = len(df)
    total_generacion = df["generacion_mwh"].sum()
    total_emisiones = df["emisiones_co2_mt"].sum()
    intensidad_promedio = df["intensidad_co2_ajustada"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Registros analiticos", f"{total_registros}")
    col2.metric("Generacion total MWh", formato_numero(total_generacion, 0))
    col3.metric("Emisiones CO2 mt", formato_numero(total_emisiones, 0))
    col4.metric("Intensidad promedio", formato_numero(intensidad_promedio, 3))

    df_categoria = (
        df.groupby("categoria_energia", as_index=False)
        .agg(
            generacion_mwh=("generacion_mwh", "sum"),
            emisiones_co2_mt=("emisiones_co2_mt", "sum"),
            intensidad_media=("intensidad_co2_ajustada", "mean"),
        )
        .sort_values("emisiones_co2_mt", ascending=False)
    )

    col_grafico, col_tabla = st.columns([2, 1])
    with col_grafico:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        sns.barplot(
            data=df_categoria,
            x="emisiones_co2_mt",
            y="categoria_energia",
            hue="categoria_energia",
            palette="viridis",
            legend=False,
            ax=ax,
        )
        ax.set_xlabel("Emisiones CO2 mt")
        ax.set_ylabel("Categoria")
        ax.set_title("Emisiones por categoria de energia")
        sns.despine(left=True, bottom=False)
        st.pyplot(fig)

    with col_tabla:
        st.dataframe(df_categoria, hide_index=True, use_container_width=True)

with tab_tac:
    st.header("Comparacion tactica por categoria y cluster")
    st.caption("Frecuencia: semanal | Objetivo: detectar segmentos con mayor intensidad.")

    categorias = sorted(df["categoria_energia"].dropna().unique())
    seleccion_categorias = st.multiselect(
        "Filtrar categorias de energia",
        options=categorias,
        default=categorias,
    )

    df_filtrado = df[df["categoria_energia"].isin(seleccion_categorias)]

    df_cluster = (
        df_filtrado.groupby("cluster_kmeans", as_index=False)
        .agg(
            registros=("cluster_kmeans", "size"),
            intensidad_media=("intensidad_co2_ajustada", "mean"),
            generacion_media_mwh=("generacion_mwh", "mean"),
            emisiones_media_mt=("emisiones_co2_mt", "mean"),
        )
        .sort_values("intensidad_media", ascending=False)
    )

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Perfil de clusters")
        st.dataframe(df_cluster, hide_index=True, use_container_width=True)

    with col2:
        fig, ax = plt.subplots(figsize=(9, 4.8))
        sns.scatterplot(
            data=df_filtrado,
            x="generacion_mwh",
            y="emisiones_co2_mt",
            size="intensidad_co2_ajustada",
            hue="cluster_kmeans",
            palette="Set2",
            sizes=(60, 260),
            alpha=0.75,
            ax=ax,
        )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Generacion MWh (escala log)")
        ax.set_ylabel("Emisiones CO2 mt (escala log)")
        ax.set_title("Relacion entre generacion, emisiones e intensidad")
        sns.despine(left=True, bottom=False)
        st.pyplot(fig)

with tab_op:
    st.header("Alertas operacionales de intensidad ambiental")
    st.caption("Frecuencia: diaria | Objetivo: identificar regiones para revision prioritaria.")

    umbral_intensidad = st.slider(
        "Ajustar umbral critico de intensidad CO2",
        min_value=float(df["intensidad_co2_ajustada"].min()),
        max_value=float(df["intensidad_co2_ajustada"].max()),
        value=float(df["intensidad_co2_ajustada"].quantile(0.75)),
        step=0.05,
    )

    min_generacion = st.number_input(
        "Generacion minima MWh para alerta",
        min_value=0.0,
        value=float(df["generacion_mwh"].median()),
        step=100000.0,
    )

    alertas = df[
        (df["intensidad_co2_ajustada"] >= umbral_intensidad)
        & (df["generacion_mwh"] >= min_generacion)
    ].sort_values("intensidad_co2_ajustada", ascending=False)

    st.warning(f"Regiones/categorias en revision prioritaria: {len(alertas)}")

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(
        df["intensidad_co2_ajustada"],
        df["generacion_mwh"],
        alpha=0.35,
        s=70,
        color="#607D8B",
        label="Registros",
    )
    ax.scatter(
        alertas["intensidad_co2_ajustada"],
        alertas["generacion_mwh"],
        color="#C62828",
        edgecolor="black",
        s=130,
        label="Alerta",
        zorder=4,
    )
    ax.axvline(umbral_intensidad, color="#C62828", linestyle="--", alpha=0.7)
    ax.axhline(min_generacion, color="#C62828", linestyle="--", alpha=0.7)
    ax.set_xlabel("Intensidad CO2 ajustada")
    ax.set_ylabel("Generacion MWh")
    ax.set_title("Matriz de alertas por intensidad y volumen energetico")
    ax.legend()
    sns.despine(left=True, bottom=False)
    st.pyplot(fig)

    columnas_alerta = [
        "periodo",
        "pais",
        "region",
        "categoria_energia",
        "generacion_mwh",
        "emisiones_co2_mt",
        "intensidad_co2_ajustada",
        "cuartil_intensidad",
        "cluster_kmeans",
    ]
    st.dataframe(alertas[columnas_alerta], hide_index=True, use_container_width=True)
