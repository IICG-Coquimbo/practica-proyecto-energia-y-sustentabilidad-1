from __future__ import annotations

import os

from pymongo import MongoClient
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from scrapers import scraper_thalia_gonzalez


MONGO_URI = os.getenv("MONGO_URI", "mongodb://database:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "proyecto_bigdata")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "energia_sustentabilidad")


def crear_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("IntegradoraBigDataThaliaGonzalez")
        .config(
            "spark.mongodb.read.connection.uri",
            f"{MONGO_URI}{MONGO_DATABASE}.{MONGO_COLLECTION}",
        )
        .config(
            "spark.mongodb.write.connection.uri",
            f"{MONGO_URI}{MONGO_DATABASE}.{MONGO_COLLECTION}",
        )
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0")
        .getOrCreate()
    )


def guardar_en_mongo(registros: list[dict]) -> None:
    if not registros:
        print("No hay registros para guardar en MongoDB.")
        return

    client = MongoClient(MONGO_URI)
    coleccion = client[MONGO_DATABASE][MONGO_COLLECTION]
    coleccion.insert_many(registros)
    print(f"Registros guardados en MongoDB: {len(registros)}")


def procesar_con_spark(registros: list[dict]) -> None:
    spark = crear_spark()
    df = spark.createDataFrame(registros)

    df_limpio = (
        df.dropDuplicates(["identificador", "pais", "tecnologia", "valor"])
        .withColumn("valor", F.col("valor").cast("double"))
        .filter((F.col("valor").isNotNull()) & (F.col("valor") > 0))
    )

    print("Muestra de productos procesados:")
    df_limpio.select("integrante", "identificador", "categoria_energia", "tecnologia", "valor", "unidad").show(
        3, truncate=False
    )

    print("Reporte Spark: capacidad promedio por categoria y tecnologia")
    reporte = (
        df_limpio.groupBy("categoria_energia", "tecnologia")
        .agg(
            F.count("identificador").alias("total_registros"),
            F.round(F.avg("valor"), 2).alias("capacidad_promedio_mw"),
            F.round(F.max("valor"), 2).alias("capacidad_maxima_mw"),
        )
        .orderBy(F.desc("capacidad_promedio_mw"))
    )
    reporte.show(20, truncate=False)

    total = df_limpio.count()
    print(f"Total de productos procesados: {total}")


def main() -> None:
    limite = int(os.getenv("LIMITE_EXTRACCION", "500"))
    registros = scraper_thalia_gonzalez.ejecutar_extraccion(limite=limite)
    print(f"Extraccion finalizada. Registros normalizados: {len(registros)}")
    guardar_en_mongo(registros)
    procesar_con_spark(registros)


if __name__ == "__main__":
    main()

