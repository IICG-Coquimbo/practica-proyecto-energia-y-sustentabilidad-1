from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.ml.feature import PCA, StandardScaler, VectorAssembler
from pyspark.ml.functions import vector_to_array
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from sklearn.cluster import DBSCAN

PROJECT_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_DIR / "semanas" / "Semana 9 EDA Spark" / "salidas" / "features_eda_semana9.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"
FIGURE_DIR = OUTPUT_DIR / "figuras"
MODEL_DIR = Path(__file__).resolve().parent / "modelos"
LABELED_DATA_PATH = MODEL_DIR / "datos_etiquetados_kmeans"
KMEANS_MODEL_PATH = MODEL_DIR / "kmeans_energia_v1"

MODEL_FEATURES = [
    "log_generacion",
    "log_emisiones",
    "intensidad_co2",
    "participacion_generacion",
]


def crear_spark() -> SparkSession:
    return SparkSession.builder.appName("Semana10_Clustering_Energia").getOrCreate()


def cargar_features(spark: SparkSession) -> DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Falta features_eda_semana9.csv. Ejecuta primero el notebook o script de Semana 9."
        )
    df = spark.read.option("header", True).option("inferSchema", True).csv(str(INPUT_PATH))
    return df.na.drop(subset=MODEL_FEATURES).filter(
        (F.col("generacion_mwh") > 0) & (F.col("emisiones_co2_mt") > 0)
    )


def preparar_vectores(df: DataFrame) -> tuple[DataFrame, object]:
    assembler = VectorAssembler(inputCols=MODEL_FEATURES, outputCol="features")
    vectorizado = assembler.transform(df)
    scaler = StandardScaler(inputCol="features", outputCol="scaledFeatures", withStd=True, withMean=True)
    scaler_model = scaler.fit(vectorizado)
    return scaler_model.transform(vectorizado), scaler_model


def calcular_pca(df_scaled: DataFrame) -> tuple[DataFrame, object]:
    pca_model = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures").fit(df_scaled)
    transformed = (
        pca_model.transform(df_scaled)
        .withColumn("pca_array", vector_to_array("pcaFeatures"))
        .withColumn("PC1", F.col("pca_array")[0])
        .withColumn("PC2", F.col("pca_array")[1])
    )
    return transformed, pca_model


def evaluar_k(df_scaled: DataFrame) -> pd.DataFrame:
    count = df_scaled.count()
    if count < 3:
        raise ValueError("Se requieren al menos tres observaciones para aplicar clustering.")
    max_k = min(10, count - 1)
    evaluator = ClusteringEvaluator(featuresCol="scaledFeatures", metricName="silhouette")
    rows: list[dict[str, float | int]] = []
    for k in range(2, max_k + 1):
        model = KMeans(k=k, seed=42, featuresCol="scaledFeatures").fit(df_scaled)
        predictions = model.transform(df_scaled)
        rows.append(
            {
                "k": k,
                "inercia": float(model.summary.trainingCost),
                "silhouette": float(evaluator.evaluate(predictions)),
            }
        )
    return pd.DataFrame(rows)


def entrenar_kmeans(df_pca: DataFrame, evaluacion: pd.DataFrame) -> tuple[DataFrame, object, int]:
    k_optimo = int(evaluacion.sort_values(["silhouette", "k"], ascending=[False, True]).iloc[0]["k"])
    model = KMeans(k=k_optimo, seed=42, featuresCol="scaledFeatures").fit(df_pca)
    return model.transform(df_pca), model, k_optimo


def aplicar_dbscan(pca_pdf: pd.DataFrame) -> pd.DataFrame:
    eps = float(os.getenv("DBSCAN_EPS", "0.5"))
    min_samples = int(os.getenv("DBSCAN_MIN_SAMPLES", "5"))
    result = pca_pdf.copy()
    result["cluster_dbscan"] = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(result[["PC1", "PC2"]])
    return result


def exportar_graficos(
    evaluacion: pd.DataFrame, kmeans_pdf: pd.DataFrame, dbscan_pdf: pd.DataFrame, k_optimo: int
) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    axes[0].plot(evaluacion["k"], evaluacion["inercia"], "bx-")
    axes[0].set_title("Metodo del codo")
    axes[0].set_xlabel("Numero de clusters (k)")
    axes[0].set_ylabel("Inercia")
    axes[1].plot(evaluacion["k"], evaluacion["silhouette"], "go-")
    axes[1].set_title("Calidad de separacion")
    axes[1].set_xlabel("Numero de clusters (k)")
    axes[1].set_ylabel("Silhouette")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "seleccion_k.png", dpi=150)
    plt.close(fig)

    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=kmeans_pdf, x="PC1", y="PC2", hue="cluster_kmeans", palette="viridis", s=70)
    plt.title(f"K-means sobre PCA para perfiles energeticos (k={k_optimo})")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "clusters_kmeans_pca.png", dpi=150)
    plt.close()

    plt.figure(figsize=(10, 7))
    sns.scatterplot(data=dbscan_pdf, x="PC1", y="PC2", hue="cluster_dbscan", palette="Set1", s=70)
    plt.title("DBSCAN sobre PCA (-1 corresponde a ruido)")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "clusters_dbscan_pca.png", dpi=150)
    plt.close()


def ejecutar_clustering() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    spark = crear_spark()
    try:
        df = cargar_features(spark).cache()
        print(f"Observaciones disponibles: {df.count()}")
        df_scaled, _ = preparar_vectores(df)
        df_pca, pca_model = calcular_pca(df_scaled)

        evaluacion = evaluar_k(df_scaled)
        predictions, model, k_optimo = entrenar_kmeans(df_pca, evaluacion)
        print(f"Varianza explicada por PCA: {pca_model.explainedVariance.toArray()}")
        print(f"K seleccionado por mayor silhouette: {k_optimo}")
        evaluacion.round(4).to_csv(OUTPUT_DIR / "evaluacion_kmeans.csv", index=False, encoding="utf-8")
        predictions.write.mode("overwrite").parquet(str(LABELED_DATA_PATH))
        model.write().overwrite().save(str(KMEANS_MODEL_PATH))
        print(f"Datos pseudo-etiquetados guardados en: {LABELED_DATA_PATH}")
        print(f"Modelo K-means guardado en: {KMEANS_MODEL_PATH}")

        resumen = predictions.groupBy("prediction").agg(
            F.count("*").alias("observaciones"),
            F.round(F.avg("generacion_mwh"), 2).alias("generacion_media_mwh"),
            F.round(F.avg("emisiones_co2_mt"), 2).alias("emisiones_media_mt"),
            F.round(F.avg("intensidad_co2"), 6).alias("intensidad_media"),
        ).orderBy("prediction")
        print("Perfil de clusters K-means:")
        resumen.show(truncate=False)

        kmeans_pdf = (
            predictions.select(
                "periodo",
                "region",
                "categoria_energia",
                "generacion_mwh",
                "emisiones_co2_mt",
                "intensidad_co2",
                "PC1",
                "PC2",
                F.col("prediction").alias("cluster_kmeans"),
            )
            .toPandas()
        )
        dbscan_pdf = aplicar_dbscan(kmeans_pdf)
        print("Distribucion DBSCAN (-1 indica ruido):")
        print(dbscan_pdf["cluster_dbscan"].value_counts().sort_index())

        kmeans_pdf.to_csv(OUTPUT_DIR / "clusters_kmeans.csv", index=False, encoding="utf-8")
        dbscan_pdf.to_csv(OUTPUT_DIR / "clusters_dbscan.csv", index=False, encoding="utf-8")
        exportar_graficos(evaluacion, kmeans_pdf, dbscan_pdf, k_optimo)
        print(f"Salidas generadas en: {OUTPUT_DIR}")
        return {
            "evaluacion": evaluacion,
            "k_optimo": k_optimo,
            "centros": model.clusterCenters(),
            "kmeans": kmeans_pdf,
            "dbscan": dbscan_pdf,
        }
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_clustering()
