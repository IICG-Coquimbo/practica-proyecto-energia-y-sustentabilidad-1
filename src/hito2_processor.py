from __future__ import annotations

import sys
from pathlib import Path

from pyspark.sql import functions as F

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from huella_carbono_pipeline import (  # noqa: E402
    MONGO_DATABASE,
    MONGO_PROCESSED_COLLECTION,
    cargar_datos_mongo,
    construir_indicador_huella,
    crear_spark,
    guardar_huella,
    limpiar_base,
)


def construir_processed_data():
    spark = crear_spark("Hito2_Processor_Huella_Carbono")
    try:
        raw = cargar_datos_mongo(spark)
        limpio = limpiar_base(raw)
        huella = construir_indicador_huella(limpio)

        totales = huella.agg(
            F.sum("emisiones_tco2").alias("total_emisiones_tco2"),
            F.sum("generacion_mwh").alias("total_generacion_mwh"),
            F.avg("intensidad_kgco2_mwh").alias("promedio_intensidad_kgco2_mwh"),
        )
        processed = (
            huella.crossJoin(totales)
            .withColumn(
                "participacion_emisiones_pct",
                F.round(F.col("emisiones_tco2") / F.col("total_emisiones_tco2") * 100, 4),
            )
            .withColumn(
                "participacion_generacion_pct",
                F.round(F.col("generacion_mwh") / F.col("total_generacion_mwh") * 100, 4),
            )
            .withColumn(
                "brecha_vs_promedio_kgco2_mwh",
                F.round(F.col("intensidad_kgco2_mwh") - F.col("promedio_intensidad_kgco2_mwh"), 4),
            )
            .withColumn("pipeline_hito", F.lit("hito_2"))
            .withColumn("estado_dato", F.lit("processed"))
            .drop("total_emisiones_tco2", "total_generacion_mwh", "promedio_intensidad_kgco2_mwh")
        )

        guardar_huella(processed)
        print(f"Registros raw: {raw.count()}")
        print(f"Registros limpios base: {limpio.count()}")
        print(f"Registros processed_data: {processed.count()}")
        print(f"Escribiendo MongoDB: {MONGO_DATABASE}.{MONGO_PROCESSED_COLLECTION}")
        processed.write.format("mongodb").mode("overwrite").save()
        return processed
    finally:
        spark.stop()


if __name__ == "__main__":
    construir_processed_data()
