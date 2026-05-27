from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns
from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from huella_carbono_pipeline import DOCS_DIR, cargar_datos_mongo, construir_indicador_huella, crear_spark, guardar_huella
from huella_carbono_pipeline import limpiar_base


def ejecutar_semana9():
    spark = crear_spark("Semana9_EDA_Huella_Carbono")
    try:
        raw = cargar_datos_mongo(spark)
        print("Registros crudos:", raw.count())

        limpio = limpiar_base(raw)
        print("Registros tras limpieza:", limpio.count())

        huella = construir_indicador_huella(limpio)
        print("Registros comparables de huella de carbono:", huella.count())
        huella.select(
            "region",
            "tecnologia",
            "periodo",
            "generacion_mwh",
            "emisiones_tco2",
            "intensidad_kgco2_mwh",
            "nivel_huella",
        ).show(10, truncate=False)

        print("Estadisticas descriptivas:")
        huella.select("generacion_mwh", "emisiones_tco2", "intensidad_kgco2_mwh").describe().show()

        print("Valores nulos:")
        huella.select(
            [
                F.count(F.when(F.col(c).isNull(), c)).alias(c)
                for c in ["generacion_mwh", "emisiones_tco2", "intensidad_kgco2_mwh"]
            ]
        ).show()

        print("Promedio de intensidad por categoria:")
        huella.groupBy("categoria_energia").agg(
            F.count("*").alias("registros"),
            F.avg("intensidad_kgco2_mwh").alias("promedio_kgco2_mwh"),
        ).orderBy(F.desc("promedio_kgco2_mwh")).show(truncate=False)

        correlacion = huella.stat.corr("generacion_mwh", "emisiones_tco2", method="pearson")
        print(f"Correlacion Pearson generacion-emisiones: {correlacion:.4f}")

        guardar_huella(huella)
        muestra = huella.toPandas()
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=muestra, x="nivel_huella", y="intensidad_kgco2_mwh", order=["Baja", "Media", "Alta"])
        plt.title("Distribucion de intensidad de huella de carbono")
        plt.xlabel("Nivel de huella")
        plt.ylabel("kg CO2 / MWh")
        plt.tight_layout()
        plt.savefig(DOCS_DIR / "semana9_boxplot_huella.png", dpi=150)
        plt.close()
        return huella
    finally:
        spark.stop()


if __name__ == "__main__":
    ejecutar_semana9()
