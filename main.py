from __future__ import annotations

import importlib
import os
import pkgutil
from pathlib import Path
from typing import Any

import certifi
from pymongo import MongoClient
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, trim, when

PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_DIR / "semanas" / "Semana 7 La union" / "salidas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MONGO_URI = os.getenv("MONGODB_URI", "mongodb://database:27017/")
MONGO_DATABASE = os.getenv("MONGODB_DATABASE", "proyecto_bigdata")
MONGO_COLLECTION = os.getenv("MONGODB_COLLECTION", "union_semana7")

TARGET_COLUMNS = [
    "fuente_sitio",
    "dataset",
    "url_origen",
    "grupo",
    "integrante",
    "tema",
    "fecha_extraccion",
    "pais",
    "region",
    "periodo",
    "indicador",
    "categoria_energia",
    "tecnologia",
    "actor",
    "item",
    "valor",
    "unidad",
    "scraper_origen",
]

STRING_COLUMNS = [
    "fuente_sitio",
    "dataset",
    "url_origen",
    "grupo",
    "integrante",
    "tema",
    "fecha_extraccion",
    "pais",
    "region",
    "indicador",
    "categoria_energia",
    "tecnologia",
    "actor",
    "item",
    "unidad",
    "scraper_origen",
]

MONGO_JARS = [
    "/usr/local/spark/jars/mongo-spark-connector_2.12-10.3.0.jar",
    "/usr/local/spark/jars/mongodb-driver-sync-4.11.1.jar",
    "/usr/local/spark/jars/mongodb-driver-core-4.11.1.jar",
    "/usr/local/spark/jars/bson-4.11.1.jar",
]


def parse_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    cleaned = "".join(ch for ch in str(value).strip() if ch.isdigit() or ch in ",.-")
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        if cleaned.count(",") > 1:
            cleaned = cleaned.replace(",", "")
        else:
            whole, fraction = cleaned.rsplit(",", 1)
            if len(fraction) == 3 and whole.replace("-", "").isdigit():
                cleaned = whole + fraction
            else:
                cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        if cleaned.count(".") > 1:
            cleaned = cleaned.replace(".", "")
        else:
            whole, fraction = cleaned.rsplit(".", 1) if "." in cleaned else (cleaned, "")
            if "." in cleaned and len(fraction) == 3 and whole.replace("-", "").isdigit():
                cleaned = whole + fraction
            else:
                cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def normalizar_registro(record: dict[str, Any], scraper_origen: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError(f"Cada scraper debe retornar diccionarios, pero llego: {type(record)!r}")

    normalizado = {column: record.get(column) for column in TARGET_COLUMNS}
    normalizado["scraper_origen"] = scraper_origen
    normalizado["valor"] = parse_float(record.get("valor"))
    normalizado["periodo"] = parse_int(record.get("periodo"))

    for column in STRING_COLUMNS:
        value = normalizado.get(column)
        if value is not None:
            normalizado[column] = str(value).strip() or None

    return normalizado


def descubrir_scrapers() -> list[Any]:
    import scrapers

    modulos = []
    for module_info in pkgutil.iter_modules(scrapers.__path__):
        if module_info.name.startswith("scraper_"):
            modulos.append(importlib.import_module(f"scrapers.{module_info.name}"))

    if not modulos:
        raise RuntimeError("No se encontraron scrapers en la carpeta 'scrapers'.")

    return sorted(modulos, key=lambda module: module.__name__)


def ejecutar_scrapers() -> list[dict[str, Any]]:
    registros: list[dict[str, Any]] = []

    for modulo in descubrir_scrapers():
        if not hasattr(modulo, "ejecutar_extraccion"):
            raise AttributeError(f"El modulo {modulo.__name__} no expone ejecutar_extraccion().")

        print(f"Ejecutando {modulo.__name__}...")
        resultado = modulo.ejecutar_extraccion()
        if not isinstance(resultado, list):
            raise TypeError(
                f"{modulo.__name__}.ejecutar_extraccion() debe retornar una lista y retorno {type(resultado)!r}."
            )

        registros_modulo = [normalizar_registro(record, modulo.__name__.split(".")[-1]) for record in resultado]
        print(f"  -> {len(registros_modulo)} registros")
        registros.extend(registros_modulo)

    return registros


def verificar_conexion_mongo() -> None:
    kwargs: dict[str, Any] = {"serverSelectionTimeoutMS": 5000}
    if MONGO_URI.startswith("mongodb+srv://"):
        kwargs["tlsCAFile"] = certifi.where()

    cliente = MongoClient(MONGO_URI, **kwargs)
    try:
        cliente.admin.command("ping")
    finally:
        cliente.close()


def crear_spark() -> SparkSession:
    builder = SparkSession.builder.appName("IntegradoraBigDataSemana7")
    jars_disponibles = [jar for jar in MONGO_JARS if Path(jar).exists()]

    if jars_disponibles:
        jars_csv = ",".join(jars_disponibles)
        jars_cp = ":".join(jars_disponibles)
        builder = (
            builder.config("spark.jars", jars_csv)
            .config("spark.driver.extraClassPath", jars_cp)
            .config("spark.executor.extraClassPath", jars_cp)
        )

    builder = (
        builder.config("spark.mongodb.read.connection.uri", MONGO_URI)
        .config("spark.mongodb.write.connection.uri", MONGO_URI)
        .config("spark.mongodb.read.database", MONGO_DATABASE)
        .config("spark.mongodb.write.database", MONGO_DATABASE)
        .config("spark.mongodb.read.collection", MONGO_COLLECTION)
        .config("spark.mongodb.write.collection", MONGO_COLLECTION)
    )
    return builder.getOrCreate()


def limpiar_con_spark(spark: SparkSession, registros: list[dict[str, Any]]):
    df = spark.createDataFrame(registros)
    df = df.select(*TARGET_COLUMNS)

    for column in STRING_COLUMNS:
        df = df.withColumn(column, when(trim(col(column)) == "", lit(None)).otherwise(trim(col(column))))

    df = df.withColumn("valor", col("valor").cast("double"))
    df = df.withColumn("periodo", col("periodo").cast("int"))
    df = df.filter(col("valor").isNotNull() & (col("valor") > 0))
    df = df.filter(col("item").isNotNull())
    df = df.dropDuplicates(["dataset", "item", "periodo", "indicador", "integrante", "valor"])
    df = df.withColumn(
        "categoria_energia",
        when(col("categoria_energia").isNull(), lit("Otra")).otherwise(col("categoria_energia")),
    )
    return df


def exportar_resultados(df) -> None:
    pdf = df.orderBy("integrante", "dataset", "item").toPandas()
    csv_path = OUTPUT_DIR / "union_semana7.csv"
    json_path = OUTPUT_DIR / "union_semana7.json"
    pdf.to_csv(csv_path, index=False, encoding="utf-8")
    pdf.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"CSV generado en: {csv_path}")
    print(f"JSON generado en: {json_path}")


def guardar_en_mongo(df) -> None:
    (
        df.write.format("mongodb")
        .mode("append")
        .option("database", MONGO_DATABASE)
        .option("collection", MONGO_COLLECTION)
        .save()
    )


def main() -> None:
    verificar_conexion_mongo()
    registros = ejecutar_scrapers()
    if not registros:
        raise RuntimeError("No se obtuvieron registros desde los scrapers.")

    spark = crear_spark()
    try:
        df_limpio = limpiar_con_spark(spark, registros)
        total = df_limpio.count()
        if total == 0:
            raise RuntimeError("Todos los registros fueron descartados durante la limpieza.")

        exportar_resultados(df_limpio)
        guardar_en_mongo(df_limpio)

        print(f"Registros finales: {total}")
        print(f"Destino MongoDB: {MONGO_DATABASE}.{MONGO_COLLECTION}")
        df_limpio.groupBy("integrante", "dataset").count().orderBy("integrante", "dataset").show(truncate=False)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
