from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from pyspark.ml.clustering import KMeans
from pyspark.ml.feature import PCA, StandardScaler, VectorAssembler
from sklearn.cluster import DBSCAN

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from huella_carbono_pipeline import DOCS_DIR, MODELO_KMEANS, SALIDA_CLUSTERS, SALIDA_HUELLA, crear_spark


def ejecutar_semana10():
    spark = crear_spark("Semana10_Clustering_Huella_Carbono")
    try:
        huella = spark.read.parquet(str(SALIDA_HUELLA))
        columnas_modelo = ["log_generacion_mwh", "log_emisiones_tco2", "intensidad_kgco2_mwh"]
        vectorizado = VectorAssembler(inputCols=columnas_modelo, outputCol="features").transform(huella)
        scaler = StandardScaler(inputCol="features", outputCol="scaledFeatures", withStd=True, withMean=True)
        escalado = scaler.fit(vectorizado).transform(vectorizado)
        pca = PCA(k=2, inputCol="scaledFeatures", outputCol="pcaFeatures")
        df_pca = pca.fit(escalado).transform(escalado)

        costos = []
        ks = list(range(2, 7))
        for k in ks:
            model = KMeans(featuresCol="scaledFeatures", k=k, seed=42).fit(df_pca)
            costos.append(model.summary.trainingCost)

        k_optimo = 3
        modelo = KMeans(featuresCol="scaledFeatures", k=k_optimo, seed=42).fit(df_pca)
        clusters = modelo.transform(df_pca)
        clusters.groupBy("prediction").count().orderBy("prediction").show()
        clusters.groupBy("prediction").avg("intensidad_kgco2_mwh").orderBy("prediction").show()

        SALIDA_CLUSTERS.parent.mkdir(parents=True, exist_ok=True)
        clusters.write.mode("overwrite").parquet(str(SALIDA_CLUSTERS))
        if MODELO_KMEANS.exists():
            import shutil

            shutil.rmtree(MODELO_KMEANS)
        modelo.save(str(MODELO_KMEANS))

        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(8, 5))
        plt.plot(ks, costos, "bx-")
        plt.xlabel("Numero de clusters (k)")
        plt.ylabel("Costo (inercia)")
        plt.title("Metodo del codo - Huella de carbono")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana10_metodo_codo.png", dpi=150)
        plt.close()

        visual = clusters.select("pcaFeatures", "prediction", "region", "tecnologia").toPandas()
        coordenadas = np.array(visual["pcaFeatures"].apply(lambda x: x.toArray()).tolist())
        visual[["PC1", "PC2"]] = pd.DataFrame(coordenadas, index=visual.index)
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=visual, x="PC1", y="PC2", hue="prediction", palette="viridis", alpha=0.75)
        plt.title("Clusters K-Means de intensidad de carbono (PCA)")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana10_clusters_kmeans.png", dpi=150)
        plt.close()

        dbscan_labels = DBSCAN(eps=0.5, min_samples=5).fit_predict(coordenadas)
        visual["cluster_dbscan"] = dbscan_labels
        print("Distribucion DBSCAN:")
        print(visual["cluster_dbscan"].value_counts().sort_index())
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=visual, x="PC1", y="PC2", hue="cluster_dbscan", palette="Set1", alpha=0.75)
        plt.title("DBSCAN - Deteccion de perfiles y ruido en huella de carbono")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana10_clusters_dbscan.png", dpi=150)
        plt.close()
        return clusters
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_semana10()
