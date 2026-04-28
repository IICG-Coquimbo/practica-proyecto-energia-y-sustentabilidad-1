from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

INTEGRANTE = os.getenv("INTEGRANTE", "Nicol Castillo")
NOMBRE_GRUPO = os.getenv("NOMBRE_GRUPO", "energia-y-sustentabilidad-1")
TEMA_PROYECTO = os.getenv("TEMA_PROYECTO", "Impacto ambiental de la energia")

EIA_GENERATION_URL = "https://www.eia.gov/electricity/data/state/annual_generation_state.xls"
EIA_EMISSIONS_URL = "https://www.eia.gov/electricity/data/state/emission_annual.xlsx"
CNE_PROJECTS_URL = "https://www.cne.cl/wp-content/uploads/2026/03/Tablas-Declaracion-Construccion-Marzo-2026.xlsx"

COLUMNAS_ESTANDAR = [
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
]

RENEWABLE_KEYWORDS = [
    "solar",
    "wind",
    "hydro",
    "geothermal",
    "wood",
    "biomass",
    "waste",
    "renewable",
    "fotovoltaico",
    "eolico",
    "hidro",
]
FOSSIL_KEYWORDS = ["coal", "petroleum", "natural gas", "other gases", "diesel", "carbon"]
NUCLEAR_KEYWORDS = ["nuclear"]
STORAGE_KEYWORDS = ["bess", "storage", "almacenamiento"]


def clasificar_categoria(texto: object) -> str:
    texto_normalizado = str(texto).strip().lower()
    if any(keyword in texto_normalizado for keyword in STORAGE_KEYWORDS):
        return "Almacenamiento"
    if any(keyword in texto_normalizado for keyword in RENEWABLE_KEYWORDS):
        return "Renovable"
    if any(keyword in texto_normalizado for keyword in FOSSIL_KEYWORDS):
        return "Fosil"
    if any(keyword in texto_normalizado for keyword in NUCLEAR_KEYWORDS):
        return "Nuclear"
    return "Otra"


def snake(value: object) -> str:
    value = str(value).strip().lower()
    replacements = {
        " ": "_",
        "\n": "_",
        ".": "",
        ",": "",
        "-": "_",
        "/": "_",
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        "[": "",
        "]": "",
        "(": "",
        ")": "",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    while "__" in value:
        value = value.replace("__", "_")
    return value.strip("_")


def serie(df: pd.DataFrame, col: str, default: object = "") -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def metadata_base() -> dict[str, object]:
    return {
        "grupo": NOMBRE_GRUPO,
        "integrante": INTEGRANTE,
        "tema": TEMA_PROYECTO,
        "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def cargar_eia_generacion() -> pd.DataFrame:
    df = pd.read_excel(EIA_GENERATION_URL, header=1)
    df.columns = [snake(col) for col in df.columns]
    df = df.rename(
        columns={
            "type_of_producer": "actor",
            "energy_source": "tecnologia",
            "generation_megawatthours": "valor",
            "year": "periodo",
            "state": "region",
        }
    )
    df = df[(df["periodo"] >= 2020) & df["region"].notna() & df["tecnologia"].notna()]
    df = df[~df["tecnologia"].isin(["Total", "All Sources"])]
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df = df[df["valor"] > 0]

    meta = metadata_base()
    df["fuente_sitio"] = "EIA"
    df["dataset"] = "annual_generation_state"
    df["url_origen"] = EIA_GENERATION_URL
    df["grupo"] = meta["grupo"]
    df["integrante"] = meta["integrante"]
    df["tema"] = meta["tema"]
    df["fecha_extraccion"] = meta["fecha_extraccion"]
    df["pais"] = "Estados Unidos"
    df["indicador"] = "generacion_electrica"
    df["categoria_energia"] = df["tecnologia"].map(clasificar_categoria)
    df["item"] = df["region"].astype(str) + " - " + df["tecnologia"].astype(str)
    df["unidad"] = "MWh"
    return df[COLUMNAS_ESTANDAR]


def cargar_eia_emisiones() -> pd.DataFrame:
    df = pd.read_excel(EIA_EMISSIONS_URL)
    df.columns = [snake(col) for col in df.columns]
    df = df.rename(
        columns={
            "producer_type": "actor",
            "energy_source": "tecnologia",
            "co2_metric_tons": "valor",
            "year": "periodo",
            "state": "region",
        }
    )
    df = df[(df["periodo"] >= 2020) & df["region"].notna() & df["tecnologia"].notna()]
    df = df[~df["tecnologia"].isin(["Total", "All Sources"])]
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df = df.dropna(subset=["valor"])
    df = df[df["valor"] >= 0]

    meta = metadata_base()
    df["fuente_sitio"] = "EIA"
    df["dataset"] = "emission_annual"
    df["url_origen"] = EIA_EMISSIONS_URL
    df["grupo"] = meta["grupo"]
    df["integrante"] = meta["integrante"]
    df["tema"] = meta["tema"]
    df["fecha_extraccion"] = meta["fecha_extraccion"]
    df["pais"] = "Estados Unidos"
    df["indicador"] = "emisiones_co2"
    df["categoria_energia"] = df["tecnologia"].map(clasificar_categoria)
    df["item"] = df["region"].astype(str) + " - " + df["tecnologia"].astype(str)
    df["unidad"] = "metric_tons_co2"
    return df[COLUMNAS_ESTANDAR]


def cargar_cne_proyectos() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    workbook = pd.ExcelFile(CNE_PROJECTS_URL)
    hojas_objetivo = workbook.sheet_names[2:5]
    meta = metadata_base()

    for sheet in hojas_objetivo:
        df = pd.read_excel(CNE_PROJECTS_URL, sheet_name=sheet, skiprows=2)
        df.columns = [snake(col) for col in df.columns]
        if "proyecto" not in df.columns:
            continue

        fecha = pd.to_datetime(serie(df, "fecha_estimada_de_interconexion", None), errors="coerce")
        tecnologia = serie(df, "tipo_de_tecnologia")

        base = pd.DataFrame(
            {
                "fuente_sitio": "CNE",
                "dataset": snake(sheet),
                "url_origen": CNE_PROJECTS_URL,
                "grupo": meta["grupo"],
                "integrante": meta["integrante"],
                "tema": meta["tema"],
                "fecha_extraccion": meta["fecha_extraccion"],
                "pais": "Chile",
                "region": serie(df, "ubicacion"),
                "periodo": fecha.dt.year,
                "indicador": "potencia_neta",
                "categoria_energia": tecnologia.map(clasificar_categoria),
                "tecnologia": tecnologia,
                "actor": serie(df, "propietario"),
                "item": serie(df, "proyecto"),
                "valor": pd.to_numeric(serie(df, "potencia_neta_mw"), errors="coerce"),
                "unidad": "MW",
            }
        )
        frames.append(base)

        if "capacidad_de_almacenamiento_mwh" in df.columns:
            almacenamiento = pd.DataFrame(
                {
                    "fuente_sitio": "CNE",
                    "dataset": snake(sheet),
                    "url_origen": CNE_PROJECTS_URL,
                    "grupo": meta["grupo"],
                    "integrante": meta["integrante"],
                    "tema": meta["tema"],
                    "fecha_extraccion": meta["fecha_extraccion"],
                    "pais": "Chile",
                    "region": serie(df, "ubicacion"),
                    "periodo": fecha.dt.year,
                    "indicador": "capacidad_almacenamiento",
                    "categoria_energia": tecnologia.map(clasificar_categoria),
                    "tecnologia": tecnologia,
                    "actor": serie(df, "propietario"),
                    "item": serie(df, "proyecto"),
                    "valor": pd.to_numeric(serie(df, "capacidad_de_almacenamiento_mwh"), errors="coerce"),
                    "unidad": "MWh",
                }
            )
            frames.append(almacenamiento)

    if not frames:
        return pd.DataFrame(columns=COLUMNAS_ESTANDAR)

    df_final = pd.concat(frames, ignore_index=True)
    df_final = df_final.dropna(subset=["item", "valor"])
    df_final = df_final[df_final["valor"] > 0]
    return df_final[COLUMNAS_ESTANDAR]


def ejecutar_extraccion() -> list[dict[str, object]]:
    df_final = pd.concat(
        [cargar_eia_generacion(), cargar_eia_emisiones(), cargar_cne_proyectos()],
        ignore_index=True,
    )
    df_final["periodo"] = pd.to_numeric(df_final["periodo"], errors="coerce").astype("Int64")
    df_final = df_final.drop_duplicates(subset=["dataset", "item", "periodo", "indicador", "integrante", "valor"])
    df_final = df_final.sort_values(
        ["pais", "indicador", "region", "periodo", "item"],
        na_position="last",
    ).reset_index(drop=True)
    df_final = df_final.where(pd.notnull(df_final), None)
    return df_final.to_dict("records")
