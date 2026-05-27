from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyspark.ml.classification import (
    DecisionTreeClassifier,
    LinearSVC,
    LogisticRegression,
    OneVsRest,
    RandomForestClassifier,
)
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator
from pyspark.ml.feature import StandardScaler, VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from sklearn.tree import DecisionTreeClassifier as SklearnDecisionTree
from sklearn.tree import plot_tree

PROJECT_DIR = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_DIR / "semanas" / "Semana 10 Clustering" / "modelos" / "datos_etiquetados_kmeans"
OUTPUT_DIR = Path(__file__).resolve().parent / "salidas"
FIGURE_DIR = OUTPUT_DIR / "figuras"

CLASSIFICATION_FEATURES = [
    "log_generacion",
    "log_emisiones",
    "intensidad_co2",
    "participacion_generacion",
]
REGRESSION_FEATURES = ["log_generacion", "participacion_generacion"]


def crear_spark() -> SparkSession:
    return SparkSession.builder.appName("Semana12_PseudoLabeling_Energia").getOrCreate()


def cargar_pseudo_etiquetas(spark: SparkSession) -> DataFrame:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Faltan las pseudo-etiquetas. Ejecuta primero el notebook o script de Semana 10."
        )
    df_clusters = spark.read.parquet(str(INPUT_PATH))
    required = set(CLASSIFICATION_FEATURES + ["prediction", "scaledFeatures", "region", "categoria_energia"])
    missing = required.difference(df_clusters.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas para Semana 12: {sorted(missing)}")
    return (
        df_clusters.withColumn("label", F.col("prediction").cast("double"))
        .drop("prediction")
        .na.drop(subset=CLASSIFICATION_FEATURES + ["label"])
        .cache()
    )


def tabla_confusion(predictions: DataFrame) -> pd.DataFrame:
    return (
        predictions.groupBy("label", "prediction")
        .count()
        .orderBy("label", "prediction")
        .toPandas()
        .pivot(index="label", columns="prediction", values="count")
        .fillna(0)
        .astype(int)
    )


def evaluar_clasificacion(df_supervisado: DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_data, test_data = df_supervisado.randomSplit([0.7, 0.3], seed=42)
    print(f"Registros de entrenamiento: {train_data.count()}")
    print(f"Registros de prueba: {test_data.count()}")
    print("Distribucion de etiquetas de entrenamiento:")
    train_data.groupBy("label").count().orderBy("label").show()

    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    models = [
        (
            "Arbol de decision",
            DecisionTreeClassifier(featuresCol="scaledFeatures", labelCol="label", maxDepth=5, seed=42),
        ),
        (
            "Random Forest",
            RandomForestClassifier(
                featuresCol="scaledFeatures", labelCol="label", numTrees=20, maxDepth=5, seed=42
            ),
        ),
        (
            "SVM OneVsRest",
            OneVsRest(
                classifier=LinearSVC(featuresCol="scaledFeatures", labelCol="label", maxIter=20),
                featuresCol="scaledFeatures",
                labelCol="label",
            ),
        ),
        (
            "Regresion logistica multinomial",
            LogisticRegression(
                featuresCol="scaledFeatures", labelCol="label", maxIter=30, family="multinomial"
            ),
        ),
    ]

    metricas: list[dict[str, float | str]] = []
    arbol_predictions: DataFrame | None = None
    arbol_model = None
    for name, estimator in models:
        model = estimator.fit(train_data)
        predictions = model.transform(test_data)
        accuracy = float(evaluator.evaluate(predictions))
        metricas.append({"modelo": name, "accuracy": accuracy})
        print(f"{name} Accuracy: {accuracy * 100:.2f}%")
        if name == "Arbol de decision":
            arbol_predictions = predictions
            arbol_model = model

    if arbol_predictions is None or arbol_model is None:
        raise RuntimeError("No se pudo entrenar el arbol de decision.")

    print("=== ESTRUCTURA LOGICA DEL ARBOL DE DECISION SPARK ===")
    print(arbol_model.toDebugString)
    confusion = tabla_confusion(arbol_predictions)
    resultados = pd.DataFrame(metricas).sort_values("accuracy", ascending=False).reset_index(drop=True)
    test_pdf = arbol_predictions.select("region", "categoria_energia", "label", "prediction").toPandas()
    return resultados, confusion, test_pdf


def exportar_arbol_visual(df_supervisado: DataFrame) -> None:
    muestra = df_supervisado.select(*CLASSIFICATION_FEATURES, "label").toPandas()
    model = SklearnDecisionTree(max_depth=3, random_state=42)
    model.fit(muestra[CLASSIFICATION_FEATURES], muestra["label"])
    clases = [f"Cluster {int(value)}" for value in model.classes_]

    plt.figure(figsize=(20, 10), dpi=120)
    plot_tree(
        model,
        feature_names=CLASSIFICATION_FEATURES,
        class_names=clases,
        filled=True,
        rounded=True,
        fontsize=10,
    )
    plt.title("Arbol de decision: reglas aproximadas de las pseudo-etiquetas K-means", fontsize=16)
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "arbol_pseudo_etiquetas.png", dpi=150)
    plt.close()


def ejecutar_regresion(df_supervisado: DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    # La intensidad incluye emisiones; no se usa emisiones como predictor para evitar leakage.
    assembler = VectorAssembler(inputCols=REGRESSION_FEATURES, outputCol="features_regresion")
    vectorizado = assembler.transform(df_supervisado)
    scaler = StandardScaler(
        inputCol="features_regresion", outputCol="scaledFeatures_regresion", withStd=True, withMean=True
    )
    preparado = (
        scaler.fit(vectorizado)
        .transform(vectorizado)
        .withColumn("label_intensidad", F.col("intensidad_co2").cast("double"))
    )
    train_reg, test_reg = preparado.randomSplit([0.7, 0.3], seed=42)
    model = LinearRegression(
        featuresCol="scaledFeatures_regresion",
        labelCol="label_intensidad",
        predictionCol="prediccion_intensidad",
        maxIter=50,
        regParam=0.01,
    ).fit(train_reg)
    predictions = model.transform(test_reg)
    r2 = float(
        RegressionEvaluator(
            labelCol="label_intensidad", predictionCol="prediccion_intensidad", metricName="r2"
        ).evaluate(predictions)
    )
    rmse = float(
        RegressionEvaluator(
            labelCol="label_intensidad", predictionCol="prediccion_intensidad", metricName="rmse"
        ).evaluate(predictions)
    )
    resultados = predictions.select(
        "region", "categoria_energia", "label_intensidad", "prediccion_intensidad"
    ).toPandas()
    metricas = {"r2": r2, "rmse": rmse, "intercepto": float(model.intercept)}
    for index, feature in enumerate(REGRESSION_FEATURES):
        metricas[f"coeficiente_{feature}"] = float(model.coefficients[index])
    print(f"Regresion intensidad CO2 - R2: {r2:.4f}; RMSE: {rmse:.6f}")
    print(f"Interseccion: {model.intercept:.6f}; coeficientes: {model.coefficients}")
    return resultados, metricas


def exportar_graficos(
    metricas_clasificacion: pd.DataFrame,
    confusion: pd.DataFrame,
    predicciones_regresion: pd.DataFrame,
) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(9, 5))
    sns.barplot(data=metricas_clasificacion, x="accuracy", y="modelo", color="#2a9d8f")
    plt.xlim(0, 1.05)
    plt.title("Accuracy para replicar pseudo-etiquetas K-means")
    plt.xlabel("Accuracy")
    plt.ylabel("Modelo")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "accuracy_modelos.png", dpi=150)
    plt.close()

    plt.figure(figsize=(6, 5))
    sns.heatmap(confusion, annot=True, cmap="Blues", fmt="d")
    plt.title("Matriz de confusion - Arbol de decision")
    plt.xlabel("Cluster predicho")
    plt.ylabel("Cluster K-means")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "matriz_confusion_arbol.png", dpi=150)
    plt.close()

    plt.figure(figsize=(7, 6))
    sns.scatterplot(
        data=predicciones_regresion,
        x="label_intensidad",
        y="prediccion_intensidad",
        hue="categoria_energia",
        s=70,
    )
    limites = [
        min(predicciones_regresion["label_intensidad"].min(), predicciones_regresion["prediccion_intensidad"].min()),
        max(predicciones_regresion["label_intensidad"].max(), predicciones_regresion["prediccion_intensidad"].max()),
    ]
    plt.plot(limites, limites, "--", color="gray")
    plt.title("Intensidad CO2 real frente a predicha")
    plt.xlabel("Intensidad real (t CO2/MWh)")
    plt.ylabel("Intensidad predicha (t CO2/MWh)")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / "regresion_intensidad_co2.png", dpi=150)
    plt.close()


def ejecutar_semana12() -> dict[str, object]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    spark = crear_spark()
    try:
        df_supervisado = cargar_pseudo_etiquetas(spark)
        print(f"Pseudo-etiquetas recuperadas: {df_supervisado.count()}")
        df_supervisado.groupBy("label").count().orderBy("label").show()

        metricas_clasificacion, confusion, prueba_arbol = evaluar_clasificacion(df_supervisado)
        exportar_arbol_visual(df_supervisado)
        regresion, metricas_regresion = ejecutar_regresion(df_supervisado)
        exportar_graficos(metricas_clasificacion, confusion, regresion)

        metricas_clasificacion.to_csv(OUTPUT_DIR / "metricas_clasificacion.csv", index=False, encoding="utf-8")
        confusion.to_csv(OUTPUT_DIR / "matriz_confusion_arbol.csv", encoding="utf-8")
        prueba_arbol.to_csv(OUTPUT_DIR / "predicciones_arbol.csv", index=False, encoding="utf-8")
        regresion.to_csv(OUTPUT_DIR / "predicciones_regresion.csv", index=False, encoding="utf-8")
        pd.DataFrame([metricas_regresion]).to_csv(
            OUTPUT_DIR / "metricas_regresion.csv", index=False, encoding="utf-8"
        )

        mejor_modelo = metricas_clasificacion.iloc[0]
        print("=== TICKET DE SALIDA ===")
        print(
            f"El mejor clasificador replica los clusters con {mejor_modelo['accuracy'] * 100:.2f}% "
            "porque aprende pseudo-etiquetas creadas con reglas geometricas de K-means."
        )
        print(
            "Para predecir impacto real faltan variables explicativas como tecnologia detallada, "
            "eficiencia de planta, combustible y condiciones operacionales."
        )
        print(f"Salidas generadas en: {OUTPUT_DIR}")
        return {
            "clasificacion": metricas_clasificacion,
            "confusion": confusion,
            "regresion": metricas_regresion,
        }
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_semana12()
