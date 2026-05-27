from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.stat import Correlation
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

PROJECT_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"
FIGURE_DIR = OUTPUT_DIR / "figuras"
CSV_FALLBACK = PROJECT_DIR / "semanas" / "Semana 7 La union" / "salidas" / "union_semana7.csv"

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://database:27017/")
MONGO_DATABASE = os.getenv("MONGODB_DATABASE", "proyecto_bigdata")
MONGO_COLLECTION = os.getenv("MONGODB_COLLECTION", "union_semana7")
FUENTE_DATOS = os.getenv("FUENTE_DATOS", "mongo").lower()

MONGO_JARS = [
    "/usr/local/spark/jars/mongo-spark-connector_2.12-10.3.0.jar",
    "/usr/local/spark/jars/mongodb-driver-sync-4.11.1.jar",
    "/usr/local/spark/jars/mongodb-driver-core-4.11.1.jar",
    "/usr/local/spark/jars/bson-4.11.1.jar",
]

FEATURE_COLUMNS = [
    "generacion_mwh",
    "emisiones_co2_mt",
    "intensidad_co2",
    "participacion_generacion",
]


def crear_spark() -> SparkSession:
    builder = SparkSession.builder.appName("Semana9_EDA_Energia")
    jars = [path for path in MONGO_JARS if Path(path).exists()]
    if jars:
        builder = builder.config("spark.jars", ",".join(jars))
        builder = builder.config("spark.driver.extraClassPath", ":".join(jars))
        builder = builder.config("spark.executor.extraClassPath", ":".join(jars))
    return builder.getOrCreate()


def cargar_datos(spark: SparkSession) -> tuple[DataFrame, str]:
    if FUENTE_DATOS != "csv":
        try:
            df = (
                spark.read.format("mongodb")
                .option("connection.uri", MONGO_URI)
                .option("database", MONGO_DATABASE)
                .option("collection", MONGO_COLLECTION)
                .load()
            )
            if df.limit(1).count() > 0:
                return df, f"MongoDB: {MONGO_DATABASE}.{MONGO_COLLECTION}"
        except Exception as error:
            print(f"No se pudo cargar MongoDB ({error}). Se usara el CSV de Semana 7.")

    if not CSV_FALLBACK.exists():
        raise FileNotFoundError(
            "No hay datos para analizar. Ejecuta main.py o define MONGODB_URI antes de Semana 9."
        )
    return spark.read.option("header", True).option("inferSchema", True).csv(str(CSV_FALLBACK)), str(CSV_FALLBACK)


def limpiar_registros(df_raw: DataFrame) -> DataFrame:
    required = {"region", "categoria_energia", "indicador", "valor", "dataset"}
    missing = required.difference(df_raw.columns)
    if missing:
        raise ValueError(f"Faltan columnas necesarias para EDA: {sorted(missing)}")

    return (
        df_raw.withColumn("valor", F.col("valor").cast("double"))
        .withColumn("periodo", F.col("periodo").cast("int"))
        .withColumn("region", F.trim("region"))
        .withColumn("categoria_energia", F.trim("categoria_energia"))
        .filter(F.col("dataset").isin("annual_generation_state", "emission_annual"))
        .filter(F.col("region").isNotNull() & F.col("categoria_energia").isNotNull())
        .filter(F.col("valor").isNotNull() & (F.col("valor") > 0))
        .dropDuplicates(["dataset", "region", "periodo", "indicador", "tecnologia", "actor", "valor"])
    )


def analizar_nulos(df: DataFrame) -> DataFrame:
    expressions = [
        F.sum(F.when(F.col(column).isNull(), 1).otherwise(0)).alias(column)
        for column in df.columns
    ]
    return df.select(*expressions)


def construir_caracteristicas(df_clean: DataFrame) -> DataFrame:
    agrupado = (
        df_clean.groupBy("periodo", "region", "categoria_energia")
        .agg(
            F.sum(
                F.when(F.col("indicador") == "generacion_electrica", F.col("valor")).otherwise(F.lit(0.0))
            ).alias("generacion_mwh"),
            F.sum(F.when(F.col("indicador") == "emisiones_co2", F.col("valor")).otherwise(F.lit(0.0))).alias(
                "emisiones_co2_mt"
            ),
        )
        .filter((F.col("generacion_mwh") > 0) & (F.col("emisiones_co2_mt") > 0))
    )

    ventana_region = Window.partitionBy("periodo", "region")
    features = (
        agrupado.withColumn("total_generacion_region", F.sum("generacion_mwh").over(ventana_region))
        .withColumn("intensidad_co2", F.col("emisiones_co2_mt") / F.col("generacion_mwh"))
        .withColumn("participacion_generacion", F.col("generacion_mwh") / F.col("total_generacion_region"))
        .withColumn("log_generacion", F.log1p("generacion_mwh"))
        .withColumn("log_emisiones", F.log1p("emisiones_co2_mt"))
    )

    media, desviacion = features.select(
        F.avg("intensidad_co2").alias("media"), F.stddev("intensidad_co2").alias("desviacion")
    ).first()
    return features.withColumn(
        "z_intensidad",
        (F.col("intensidad_co2") - F.lit(media)) / F.lit(desviacion) if desviacion else F.lit(0.0),
    )


def marcar_outliers(features: DataFrame) -> tuple[DataFrame, tuple[float, float]]:
    q1, q3 = features.approxQuantile("intensidad_co2", [0.25, 0.75], 0.01)
    iqr = q3 - q1
    limites = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    return (
        features.withColumn(
            "es_outlier_intensidad",
            (F.col("intensidad_co2") < limites[0]) | (F.col("intensidad_co2") > limites[1]),
        ),
        limites,
    )


def matriz_correlacion(features: DataFrame, method: str = "pearson") -> pd.DataFrame:
    source_columns = FEATURE_COLUMNS
    data = features
    if method == "spearman":
        rank_columns = []
        for column in FEATURE_COLUMNS:
            rank_name = f"rank_{column}"
            data = data.withColumn(rank_name, F.percent_rank().over(Window.orderBy(F.col(column))))
            rank_columns.append(rank_name)
        source_columns = rank_columns

    assembled = VectorAssembler(inputCols=source_columns, outputCol="features").transform(data.na.drop())
    matrix = Correlation.corr(assembled, "features", "pearson").head()[0].toArray()
    return pd.DataFrame(matrix, index=FEATURE_COLUMNS, columns=FEATURE_COLUMNS)


def exportar_graficos(features_pdf: pd.DataFrame, pearson: pd.DataFrame) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(9, 5))
    sns.boxplot(data=features_pdf, x="categoria_energia", y="intensidad_co2")
    plt.title("Intensidad de emisiones por categoria energetica")
    plt.xlabel("Categoria energetica")
    plt.ylabel("Toneladas CO2 por MWh")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "boxplot_intensidad_categoria.png", dpi=150)
    plt.close()

    plt.figure(figsize=(9, 6))
    sns.scatterplot(
        data=features_pdf,
        x="generacion_mwh",
        y="emisiones_co2_mt",
        hue="categoria_energia",
        alpha=0.75,
    )
    plt.xscale("log")
    plt.yscale("log")
    plt.title("Generacion y emisiones por region y categoria")
    plt.xlabel("Generacion electrica (MWh, escala log)")
    plt.ylabel("Emisiones CO2 (toneladas metricas, escala log)")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "dispersion_generacion_emisiones.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 6))
    sns.heatmap(pearson, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".2f")
    plt.title("Matriz de correlacion de Pearson")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "correlacion_pearson.png", dpi=150)
    plt.close()


def ejecutar_eda() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    spark = crear_spark()
    try:
        df_raw, origen = cargar_datos(spark)
        print(f"Fuente analizada: {origen}")
        print(f"Registros de entrada: {df_raw.count()}")

        df_clean = limpiar_registros(df_raw).cache()
        print(f"Registros EIA limpios: {df_clean.count()}")
        print("Valores faltantes despues de limpieza:")
        analizar_nulos(df_clean).show(truncate=False)

        features = construir_caracteristicas(df_clean)
        features, limites = marcar_outliers(features)
        features = features.cache()

        print("Resumen estadistico de variables derivadas:")
        features.select(*FEATURE_COLUMNS).describe().show(truncate=False)
        print(f"Limites IQR para intensidad CO2: inferior={limites[0]:.6f}, superior={limites[1]:.6f}")
        features.groupBy("es_outlier_intensidad").count().show()
        features.groupBy("categoria_energia").agg(
            F.count("*").alias("observaciones"),
            F.round(F.avg("intensidad_co2"), 6).alias("intensidad_media"),
            F.round(F.skewness("intensidad_co2"), 4).alias("skewness_intensidad"),
        ).orderBy(F.desc("observaciones")).show(truncate=False)

        pearson = matriz_correlacion(features, "pearson")
        spearman = matriz_correlacion(features, "spearman")
        print("Correlacion Pearson:")
        print(pearson.round(4))
        print("Correlacion Spearman (calculada sobre rangos):")
        print(spearman.round(4))

        ordered = features.orderBy("periodo", "region", "categoria_energia")
        features_pdf = ordered.toPandas()
        features_pdf.to_csv(OUTPUT_DIR / "features_eda_semana9.csv", index=False, encoding="utf-8")
        pearson.to_csv(OUTPUT_DIR / "correlacion_pearson.csv", encoding="utf-8")
        spearman.to_csv(OUTPUT_DIR / "correlacion_spearman.csv", encoding="utf-8")
        exportar_graficos(features_pdf, pearson)

        print(f"Salidas generadas en: {OUTPUT_DIR}")
        return {
            "features": features_pdf,
            "pearson": pearson,
            "spearman": spearman,
            "limites_iqr": limites,
        }
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_eda()
