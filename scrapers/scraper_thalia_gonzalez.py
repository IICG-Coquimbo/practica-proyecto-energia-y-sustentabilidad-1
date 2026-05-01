from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd


GRUPO = "Thalia-Gonzalez"
TEMA = "Impacto ambiental de la energia"
FUENTE_SITIO = "World Resources Institute"
DATASET = "global_power_plant_database"
URL_ORIGEN = "https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv"


def _clasificar_categoria(tecnologia: str) -> str:
    renovables = {"Hydro", "Solar", "Wind", "Geothermal", "Biomass", "Wave and Tidal"}
    return "Renovable" if tecnologia in renovables else "No renovable"


def ejecutar_extraccion(limite: int | None = 500, usar_cache: bool = True) -> list[dict]:
    """Extrae y normaliza datos de plantas de generacion electrica.

    Retorna una lista de diccionarios con el esquema acordado para Semana 7:
    identificador, item, valor, integrante/grupo, categoria_energia y metadatos.
    """
    cache = Path(__file__).resolve().parents[1] / "Energy" / "datos_auditoria_global.csv"
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if usar_cache and cache.exists():
        df = pd.read_csv(cache)
    else:
        df = pd.read_csv(URL_ORIGEN, low_memory=False)
        df = df.rename(
            columns={
                "country_long": "pais",
                "country": "region",
                "primary_fuel": "tecnologia",
                "name": "nombre_planta",
                "capacity_mw": "valor",
                "owner": "actor",
            }
        )
        df["categoria_energia"] = df["tecnologia"].apply(_clasificar_categoria)
        df["item"] = df["nombre_planta"].astype(str) + " - " + df["tecnologia"].astype(str)
        df["unidad"] = "MW"
        df["indicador"] = "capacidad_generacion"
        df["periodo"] = datetime.now().year

    columnas_necesarias = ["item", "valor", "tecnologia", "categoria_energia"]
    df = df.dropna(subset=columnas_necesarias).copy()
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df[df["valor"] > 0]

    if limite is not None:
        df = df.head(limite)

    registros: list[dict] = []
    for _, fila in df.iterrows():
        item = str(fila.get("item", "")).strip()
        tecnologia = str(fila.get("tecnologia", "")).strip()
        registro = {
            "fuente_sitio": str(fila.get("fuente_sitio", FUENTE_SITIO)),
            "dataset": str(fila.get("dataset", DATASET)),
            "url_origen": str(fila.get("url_origen", URL_ORIGEN)),
            "grupo": GRUPO,
            "integrante": GRUPO,
            "tema": str(fila.get("tema", TEMA)),
            "fecha_extraccion": str(fila.get("fecha_extraccion", fecha)),
            "pais": str(fila.get("pais", "")),
            "region": str(fila.get("region", "")),
            "periodo": str(fila.get("periodo", datetime.now().year)),
            "indicador": str(fila.get("indicador", "capacidad_generacion")),
            "categoria_energia": str(fila.get("categoria_energia", _clasificar_categoria(tecnologia))),
            "tecnologia": tecnologia,
            "actor": str(fila.get("actor", "Sin informacion")),
            "identificador": item,
            "item": item,
            "valor": float(fila["valor"]),
            "unidad": str(fila.get("unidad", "MW")),
        }
        registros.append(registro)

    return registros


if __name__ == "__main__":
    cantidad = int(os.getenv("LIMITE_EXTRACCION", "10"))
    datos = ejecutar_extraccion(limite=cantidad)
    print(f"Registros extraidos: {len(datos)}")
    for registro in datos[:3]:
        print(registro)

