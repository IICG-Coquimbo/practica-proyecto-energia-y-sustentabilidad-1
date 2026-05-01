from __future__ import annotations

import os

import certifi
from pymongo import MongoClient
from pymongo import UpdateOne
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from scrapers import scraper_thalia_gonzalez


MONGO_URI = os.getenv("MONGO_URI", "mongodb://database:27017/")
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "proyecto_bigdata")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "energia_sustentabilidad")


def mongo_collection_uri() -> str:
    if "?" in MONGO_URI:
        base, query = MONGO_URI.split("?", 1)
        base = base.rstrip("/")
        if base.endswith(f"/{MONGO_DATABASE}"):
            return f"{base}.{MONGO_COLLECTION}?{query}"
        return f"{base}/{MONGO_DATABASE}.{MONGO_COLLECTION}?{query}"

    return f"{MONGO_URI.rstrip('/')}/{MONGO_DATABASE}.{MONGO_COLLECTION}"


def crear_cliente_mongo() -> MongoClient:
    opciones = {"serverSelectionTimeoutMS": 5000}
    if MONGO_URI.startswith("mongodb+srv://"):
        opciones["tlsCAFile"] = certifi.where()
    return MongoClient(MONGO_URI, **opciones)


def crear_spark() -> SparkSession:
    return (
        SparkSession.builder.appName("IntegradoraBigDataThaliaGonzalez")
        .config(
            "spark.mongodb.read.connection.uri",
            mongo_collection_uri(),
        )
        .config(
            "spark.mongodb.write.connection.uri",
            mongo_collection_uri(),
        )
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0")
        .getOrCreate()
    )


def guardar_en_mongo(registros: list[dict]) -> None:
    if not registros:
        print("No hay registros para guardar en MongoDB.")
        return

    client = crear_cliente_mongo()
    coleccion = client[MONGO_DATABASE][MONGO_COLLECTION]
    operaciones = [
        UpdateOne(
            {
                "fuente_sitio": registro["fuente_sitio"],
                "dataset": registro["dataset"],
                "pais": registro["pais"],
                "region": registro["region"],
                "periodo": registro["periodo"],
                "tecnologia": registro["tecnologia"],
                "item": registro["item"],
            },
            {"$set": registro},
            upsert=True,
        )
        for registro in registros
    ]
    resultado = coleccion.bulk_write(operaciones, ordered=False)
    print(
        "MongoDB actualizado: "
        f"{resultado.upserted_count} nuevos, {resultado.modified_count} modificados."
    )


def procesar_con_spark(registros: list[dict]) -> None:
    spark = crear_spark()
    df = spark.createDataFrame(registros)

    df_limpio = (
        df.dropDuplicates(["item", "pais", "region", "tecnologia", "valor"])
        .withColumn("valor", F.col("valor").cast("double"))
        .filter((F.col("valor").isNotNull()) & (F.col("valor") > 0))
    )

    print("Muestra de productos procesados:")
    df_limpio.select("grupo", "item", "categoria_energia", "tecnologia", "valor", "unidad").show(3, truncate=False)

    print("Reporte Spark: capacidad promedio por categoria y tecnologia")
    reporte = (
        df_limpio.groupBy("categoria_energia", "tecnologia")
        .agg(
            F.count("item").alias("total_registros"),
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
