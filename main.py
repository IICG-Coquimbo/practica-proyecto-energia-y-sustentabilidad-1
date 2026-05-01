import os

from pymongo import MongoClient
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count, regexp_replace, split

from scraper import scraper_anggy_jeraldo


MONGO_URI = os.getenv("MONGO_URI", "mongodb://database:27017")
DATABASE_NAME = os.getenv("MONGO_DATABASE", "TiendaBigData")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "AmazonLaptops")


def guardar_en_mongo(datos):
    if not datos:
        print("No hay datos para guardar en MongoDB.")
        return 0

    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    coleccion = client[DATABASE_NAME][COLLECTION_NAME]
    resultado = coleccion.insert_many(datos)
    return len(resultado.inserted_ids)


def construir_spark():
    return (
        SparkSession.builder.appName("IntegradoraBigData_AnggyJeraldo")
        .config("spark.mongodb.read.connection.uri", f"{MONGO_URI}/{DATABASE_NAME}.{COLLECTION_NAME}")
        .config("spark.mongodb.write.connection.uri", f"{MONGO_URI}/{DATABASE_NAME}.{COLLECTION_NAME}")
        .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.3.0")
        .getOrCreate()
    )


def analizar_con_spark(spark, datos):
    if not datos:
        print("No hay datos para procesar con Spark.")
        return None

    df = spark.createDataFrame(datos)
    df_limpio = (
        df.withColumn(
            "valor_numerico",
            regexp_replace(col("valor").cast("string"), "[^0-9.]", "").cast("double"),
        )
        .filter(col("valor_numerico") > 100)
        .withColumn("marca", split(col("identificador"), " ")[0])
    )

    print("Total de productos procesados:", df_limpio.count())
    reporte_marcas = (
        df_limpio.groupBy("marca")
        .agg(
            count("identificador").alias("total_productos"),
            avg("valor_numerico").alias("precio_promedio"),
        )
        .orderBy(col("precio_promedio").desc())
    )
    reporte_marcas.show(truncate=False)
    return reporte_marcas


def main():
    datos_anggy = scraper_anggy_jeraldo.ejecutar_extraccion(
        limite_paginas=int(os.getenv("LIMITE_PAGINAS", "1")),
        pausa_manual=os.getenv("PAUSA_MANUAL", "1") == "1",
    )

    print("Primeros productos extraidos:")
    for producto in datos_anggy[:3]:
        print(producto)

    guardados = guardar_en_mongo(datos_anggy)
    print(f"Datos guardados en MongoDB: {guardados}")

    spark = construir_spark()
    analizar_con_spark(spark, datos_anggy)


if __name__ == "__main__":
    main()

