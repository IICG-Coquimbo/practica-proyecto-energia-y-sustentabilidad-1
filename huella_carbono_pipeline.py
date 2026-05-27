from __future__ import annotations

import os
from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


PROJECT_DIR = Path(__file__).resolve().parent
SEMANA9_DIR = PROJECT_DIR / "semanas" / "Semana 9 EDA Huella Carbono"
SEMANA10_DIR = PROJECT_DIR / "semanas" / "Semana 10 Clustering Huella Carbono"
SEMANA12_DIR = PROJECT_DIR / "semanas" / "Semana 12 Modelos Huella Carbono"
DOCS_DIR = PROJECT_DIR / "docs" / "evidencias_semanas_9_12"

SALIDA_HUELLA = SEMANA9_DIR / "salidas" / "huella_carbono_limpia.parquet"
SALIDA_CLUSTERS = SEMANA10_DIR / "modelos" / "datos_etiquetados_kmeans"
MODELO_KMEANS = SEMANA10_DIR / "modelos" / "kmeans_huella_carbono"

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://database:27017/")
MONGO_DATABASE = os.getenv("MONGODB_DATABASE", "proyecto_bigdata")
MONGO_COLLECTION = os.getenv("MONGODB_COLLECTION", "union_semana7")

MONGO_JARS = [
    "/usr/local/spark/jars/mongo-spark-connector_2.12-10.3.0.jar",
    "/usr/local/spark/jars/mongodb-driver-sync-4.11.1.jar",
    "/usr/local/spark/jars/mongodb-driver-core-4.11.1.jar",
    "/usr/local/spark/jars/bson-4.11.1.jar",
]


def asegurar_directorios() -> None:
    for directory in [SEMANA9_DIR / "salidas", SEMANA10_DIR / "modelos", SEMANA12_DIR / "salidas", DOCS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def crear_spark(app_name: str) -> SparkSession:
    builder = SparkSession.builder.appName(app_name)
    jars = [jar for jar in MONGO_JARS if Path(jar).exists()]
    if jars:
        jars_csv = ",".join(jars)
        classpath = ":".join(jars)
        builder = (
            builder.config("spark.jars", jars_csv)
            .config("spark.driver.extraClassPath", classpath)
            .config("spark.executor.extraClassPath", classpath)
        )

    return (
        builder.config("spark.mongodb.read.connection.uri", MONGO_URI)
        .config("spark.mongodb.read.database", MONGO_DATABASE)
        .config("spark.mongodb.read.collection", MONGO_COLLECTION)
        .getOrCreate()
    )


def cargar_datos_mongo(spark: SparkSession) -> DataFrame:
    print(f"Leyendo MongoDB: {MONGO_DATABASE}.{MONGO_COLLECTION}")
    return spark.read.format("mongodb").load()


def limpiar_base(df_raw: DataFrame) -> DataFrame:
    requeridas = [
        "dataset",
        "integrante",
        "pais",
        "region",
        "periodo",
        "indicador",
        "categoria_energia",
        "tecnologia",
        "valor",
        "unidad",
    ]
    faltantes = [column for column in requeridas if column not in df_raw.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en MongoDB: {faltantes}")

    df = (
        df_raw.select(*requeridas)
        .withColumn("periodo", F.col("periodo").cast("int"))
        .withColumn("valor", F.col("valor").cast("double"))
        .withColumn("region", F.upper(F.trim(F.col("region"))))
        .withColumn("tecnologia", F.lower(F.trim(F.col("tecnologia"))))
        .withColumn("categoria_energia", F.trim(F.col("categoria_energia")))
        .filter(F.col("valor").isNotNull() & (F.col("valor") > 0))
        .filter(F.col("region").isNotNull() & F.col("tecnologia").isNotNull())
        .dropDuplicates(["dataset", "region", "periodo", "indicador", "tecnologia", "valor"])
    )
    return df


def construir_indicador_huella(df_clean: DataFrame) -> DataFrame:
    claves = ["region", "periodo", "tecnologia", "categoria_energia"]

    generacion = (
        df_clean.filter(F.lower(F.col("indicador")) == "generacion_electrica")
        .groupBy(*claves)
        .agg(F.sum("valor").alias("generacion_mwh"))
    )
    emisiones = (
        df_clean.filter(F.lower(F.col("indicador")) == "emisiones_co2")
        .groupBy(*claves)
        .agg(F.sum("valor").alias("emisiones_tco2"))
    )

    df_huella = (
        generacion.join(emisiones, on=claves, how="inner")
        .filter(F.col("generacion_mwh") > 0)
        .withColumn("intensidad_tco2_mwh", F.col("emisiones_tco2") / F.col("generacion_mwh"))
        .withColumn("intensidad_kgco2_mwh", F.col("intensidad_tco2_mwh") * F.lit(1000.0))
        .filter(F.col("intensidad_kgco2_mwh").between(0.0, 2000.0))
        .withColumn("log_generacion_mwh", F.log1p(F.col("generacion_mwh")))
        .withColumn("log_emisiones_tco2", F.log1p(F.col("emisiones_tco2")))
        .withColumn(
            "nivel_huella",
            F.when(F.col("intensidad_kgco2_mwh") < 100, F.lit("Baja"))
            .when(F.col("intensidad_kgco2_mwh") < 500, F.lit("Media"))
            .otherwise(F.lit("Alta")),
        )
        .orderBy(F.desc("intensidad_kgco2_mwh"))
    )
    return df_huella


def guardar_huella(df_huella: DataFrame) -> None:
    asegurar_directorios()
    df_huella.write.mode("overwrite").parquet(str(SALIDA_HUELLA))
    df_huella.toPandas().to_csv(SEMANA9_DIR / "salidas" / "huella_carbono_limpia.csv", index=False)
