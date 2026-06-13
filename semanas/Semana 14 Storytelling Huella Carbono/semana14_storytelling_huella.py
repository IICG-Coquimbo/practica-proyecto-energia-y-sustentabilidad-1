from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SALIDA_HUELLA = PROJECT_ROOT / "semanas" / "Semana 9 EDA Huella Carbono" / "salidas" / "huella_carbono_limpia.parquet"
SALIDA_CLUSTERS = PROJECT_ROOT / "semanas" / "Semana 10 Clustering Huella Carbono" / "modelos" / "datos_etiquetados_kmeans"
SEMANA14_DIR = PROJECT_ROOT / "semanas" / "Semana 14 Storytelling Huella Carbono"
SALIDAS_DIR = SEMANA14_DIR / "salidas"
DOCS_DIR = PROJECT_ROOT / "docs" / "evidencias_semana_14"


def main():
    SALIDAS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    spark = SparkSession.builder.appName("Semana14_Storytelling_Huella_Carbono").getOrCreate()
    try:
        df_completos = spark.read.parquet(str(SALIDA_HUELLA))
        df_historico = spark.read.parquet(str(SALIDA_CLUSTERS))
        total_registros = df_historico.count()
        print(f"EXITO: Datos recuperados para storytelling: {total_registros} registros")

        total_emisiones = df_completos.agg(F.sum("emisiones_tco2")).first()[0]
        kpi_estrategico = (
            df_completos.groupBy("region")
            .agg(
                F.round(F.sum("emisiones_tco2"), 2).alias("emisiones_totales_tco2"),
                F.round(F.sum("generacion_mwh"), 2).alias("generacion_total_mwh"),
                F.round(F.avg("intensidad_kgco2_mwh"), 2).alias("intensidad_promedio_kgco2_mwh"),
                F.round((F.sum("emisiones_tco2") / F.lit(total_emisiones)) * 100, 2).alias("participacion_emisiones_pct"),
            )
            .orderBy(F.desc("participacion_emisiones_pct"))
        )

        kpi_tactico = (
            df_completos.groupBy("tecnologia")
            .agg(
                F.round(F.min("intensidad_kgco2_mwh"), 2).alias("intensidad_minima"),
                F.round(F.avg("intensidad_kgco2_mwh"), 2).alias("intensidad_promedio"),
                F.round(F.max("intensidad_kgco2_mwh"), 2).alias("intensidad_maxima"),
                F.round(F.stddev("intensidad_kgco2_mwh"), 2).alias("dispersion_intensidad"),
            )
            .orderBy(F.desc("dispersion_intensidad"))
        )

        umbral_generacion = df_completos.approxQuantile("generacion_mwh", [0.5], 0.01)[0]
        kpi_operacional = (
            df_completos.filter((F.col("intensidad_kgco2_mwh") >= 500) & (F.col("generacion_mwh") >= F.lit(umbral_generacion)))
            .select("region", "periodo", "tecnologia", "categoria_energia", "generacion_mwh", "emisiones_tco2", "intensidad_kgco2_mwh", "nivel_huella")
            .orderBy(F.desc("intensidad_kgco2_mwh"))
        )

        print("\n[KPI ESTRATEGICO] Concentracion de emisiones por region")
        kpi_estrategico.show(10, truncate=False)
        print("\n[KPI TACTICO] Dispersion de intensidad por tecnologia")
        kpi_tactico.show(10, truncate=False)
        print(f"\n[KPI OPERACIONAL] Alertas criticas: {kpi_operacional.count()}")
        kpi_operacional.show(10, truncate=False)

        df_est = kpi_estrategico.toPandas()
        df_tac = kpi_tactico.toPandas()
        df_op = kpi_operacional.toPandas()
        df_todos = df_completos.select("region", "tecnologia", "generacion_mwh", "intensidad_kgco2_mwh", "nivel_huella").toPandas()

        df_est.to_csv(SALIDAS_DIR / "kpi_estrategico_regiones.csv", index=False)
        df_tac.to_csv(SALIDAS_DIR / "kpi_tactico_tecnologias.csv", index=False)
        df_op.to_csv(SALIDAS_DIR / "kpi_operacional_alertas.csv", index=False)

        sns.set_theme(style="whitegrid")
        top_est = df_est.head(10)
        plt.figure(figsize=(12, 6))
        ax = sns.barplot(data=top_est, x="participacion_emisiones_pct", y="region", palette="Reds_r")
        for p in ax.patches:
            ax.annotate(f"{p.get_width():.1f}%", (p.get_width() + 0.3, p.get_y() + p.get_height() / 2), va="center")
        plt.title("Vista estrategica: participacion de emisiones por region")
        plt.xlabel("Participacion en emisiones totales (%)")
        plt.ylabel("Region")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana14_kpi_estrategico_regiones.png", dpi=150)
        plt.close()

        plt.figure(figsize=(12, 6))
        plt.vlines(df_tac["tecnologia"], df_tac["intensidad_minima"], df_tac["intensidad_maxima"], color="gray", alpha=0.6)
        plt.scatter(df_tac["tecnologia"], df_tac["intensidad_promedio"], color="navy", s=90, label="Promedio")
        plt.xticks(rotation=45, ha="right")
        plt.title("Vista tactica: dispersion de intensidad por tecnologia")
        plt.xlabel("Tecnologia")
        plt.ylabel("kg CO2 / MWh")
        plt.legend()
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana14_kpi_tactico_tecnologias.png", dpi=150)
        plt.close()

        alertas = df_todos[(df_todos["intensidad_kgco2_mwh"] >= 500) & (df_todos["generacion_mwh"] >= umbral_generacion)]
        plt.figure(figsize=(12, 7))
        sns.scatterplot(data=df_todos, x="generacion_mwh", y="intensidad_kgco2_mwh", hue="nivel_huella", alpha=0.7, s=70)
        sns.scatterplot(data=alertas, x="generacion_mwh", y="intensidad_kgco2_mwh", color="crimson", s=130, edgecolor="black", label="Alertas criticas")
        plt.axhline(500, color="red", linestyle="--", alpha=0.7)
        plt.axvline(umbral_generacion, color="red", linestyle="--", alpha=0.7)
        plt.title("Vista operacional: alertas de alta huella de carbono")
        plt.xlabel("Generacion electrica (MWh)")
        plt.ylabel("Intensidad kg CO2 / MWh")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana14_kpi_operacional_alertas.png", dpi=150)
        plt.close()

        top_region = df_est.iloc[0]
        top_tecnologia = df_tac.iloc[0]
        guion = f"""# Semana 14 - Arco narrativo: contar historias con datos

## Contexto comercial y recuperacion de datos

Se recuperan los datos persistidos de las semanas 9 y 10 para transformar el analisis tecnico de huella de carbono en una narrativa de negocio basada en KPIs.

Registros recuperados: {total_registros}

## Matriz de KPIs

| Nivel | KPI | Variable principal | Frecuencia | Objetivo |
|---|---|---|---|---|
| Estrategico | Concentracion de emisiones por region | emisiones_tco2 | Mensual / trimestral | Priorizar territorios con mayor riesgo ambiental |
| Tactico | Dispersion de intensidad por tecnologia | intensidad_kgco2_mwh | Semanal | Comparar tecnologias y definir acciones de mejora |
| Operacional | Alertas criticas de alta huella | intensidad_kgco2_mwh y generacion_mwh | Diario | Detectar casos de alto impacto que requieren accion inmediata |

## Guion de storytelling

### Vision estrategica
La region {top_region['region']} concentra {top_region['participacion_emisiones_pct']}% de las emisiones analizadas. Para la direccion, este KPI muestra donde se concentra el riesgo ambiental y donde conviene priorizar planes de reduccion o transicion energetica.

### Vision tactica
La tecnologia {top_tecnologia['tecnologia']} presenta la mayor dispersion de intensidad de carbono. Para la gerencia tecnica, esto indica que no basta mirar promedios: hay que revisar casos extremos por tecnologia, periodo y region.

### Vision operacional
Se detectaron {len(df_op)} alertas criticas con alta intensidad de carbono y generacion relevante. Estas observaciones deben revisarse de forma diaria porque combinan alto impacto ambiental con volumen importante de energia generada.
"""
        (SALIDAS_DIR / "guion_storytelling_semana14.md").write_text(guion, encoding="utf-8")
        print("\nSemana 14 completada. Revisa salidas y docs/evidencias_semana_14.")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
