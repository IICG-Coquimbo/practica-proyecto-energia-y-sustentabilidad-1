from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from pyspark.ml.classification import (
    DecisionTreeClassifier,
    LinearSVC,
    LogisticRegression,
    OneVsRest,
    RandomForestClassifier,
)
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, RegressionEvaluator
from pyspark.ml.feature import OneHotEncoder, StringIndexer, VectorAssembler
from pyspark.ml.regression import LinearRegression

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from huella_carbono_pipeline import SALIDA_CLUSTERS, SEMANA12_DIR, crear_spark


def ejecutar_semana12():
    spark = crear_spark("Semana12_Modelos_Huella_Carbono")
    try:
        clusters = spark.read.parquet(str(SALIDA_CLUSTERS))
        supervisado = clusters.withColumnRenamed("prediction", "label")
        train, test = supervisado.randomSplit([0.7, 0.3], seed=42)
        print("Entrenamiento:", train.count(), "Prueba:", test.count())

        evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
        modelos = {
            "Arbol de Decision": DecisionTreeClassifier(
                featuresCol="scaledFeatures", labelCol="label", maxDepth=5, seed=42
            ),
            "Random Forest": RandomForestClassifier(
                featuresCol="scaledFeatures", labelCol="label", numTrees=30, seed=42
            ),
            "SVM OneVsRest": OneVsRest(
                classifier=LinearSVC(featuresCol="scaledFeatures", labelCol="label", maxIter=20),
                featuresCol="scaledFeatures",
                labelCol="label",
            ),
            "Regresion Logistica": LogisticRegression(
                featuresCol="scaledFeatures",
                labelCol="label",
                maxIter=20,
                family="multinomial",
                regParam=0.1,
            ),
        }

        resultados = []
        for nombre, estimador in modelos.items():
            modelo = estimador.fit(train)
            predicciones = modelo.transform(test)
            accuracy = evaluator.evaluate(predicciones)
            resultados.append({"modelo": nombre, "accuracy": accuracy})
            print(f"{nombre}: {accuracy * 100:.2f}%")
            if nombre == "Arbol de Decision":
                print(modelo.toDebugString)

        categoria_indexer = StringIndexer(inputCol="categoria_energia", outputCol="categoria_idx", handleInvalid="keep")
        indexado = categoria_indexer.fit(clusters).transform(clusters)
        encoder = OneHotEncoder(inputCols=["categoria_idx"], outputCols=["categoria_vec"])
        codificado = encoder.fit(indexado).transform(indexado)
        regresion_features = VectorAssembler(
            inputCols=["log_generacion_mwh", "categoria_vec"], outputCol="features_regresion"
        ).transform(codificado)

        train_reg, test_reg = regresion_features.randomSplit([0.7, 0.3], seed=42)
        regresion = LinearRegression(
            featuresCol="features_regresion",
            labelCol="intensidad_kgco2_mwh",
            predictionCol="prediccion_intensidad",
            maxIter=30,
            regParam=0.1,
        ).fit(train_reg)
        pred_reg = regresion.transform(test_reg)
        r2 = RegressionEvaluator(
            labelCol="intensidad_kgco2_mwh", predictionCol="prediccion_intensidad", metricName="r2"
        ).evaluate(pred_reg)
        rmse = RegressionEvaluator(
            labelCol="intensidad_kgco2_mwh", predictionCol="prediccion_intensidad", metricName="rmse"
        ).evaluate(pred_reg)
        print(f"Regresion intensidad carbono - R2: {r2:.4f} | RMSE: {rmse:.4f} kg CO2/MWh")
        print(
            "Interpretacion: la intensidad depende de tecnologia y mezcla de generacion; "
            "un R2 bajo indica que faltan variables operacionales o combustible detallado."
        )

        SEMANA12_DIR.joinpath("salidas").mkdir(parents=True, exist_ok=True)
        pd.DataFrame(resultados).to_csv(SEMANA12_DIR / "salidas" / "resultados_clasificacion.csv", index=False)
        pd.DataFrame([{"modelo": "Regresion Lineal", "r2": r2, "rmse": rmse}]).to_csv(
            SEMANA12_DIR / "salidas" / "resultados_regresion.csv", index=False
        )
        return resultados, r2, rmse
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_semana12()
