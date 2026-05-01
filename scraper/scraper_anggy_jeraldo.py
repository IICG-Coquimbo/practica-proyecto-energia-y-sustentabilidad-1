from datetime import datetime, timezone

import pandas as pd


INTEGRANTE = "Anggy_Jeraldo"
CATEGORIA_PRODUCTO = "Energia"
FUENTE_DATOS = (
    "https://ourworldindata.org/grapher/share-electricity-low-carbon.csv"
    "?v=1&csvType=full&useColumnShortNames=false"
)


def _normalizar_columnas(dataframe):
    columnas = {columna.lower(): columna for columna in dataframe.columns}
    entidad = columnas.get("entity")
    anio = columnas.get("year")
    valor = next(
        (
            columna
            for columna in dataframe.columns
            if columna not in {entidad, anio, columnas.get("code")}
        ),
        None,
    )

    if not entidad or not anio or not valor:
        raise ValueError("No se encontraron las columnas esperadas en la fuente.")

    return dataframe.rename(
        columns={
            entidad: "pais",
            anio: "anio",
            valor: "porcentaje_electricidad_baja_carbono",
        }
    )


def ejecutar_extraccion(limite_registros=500, pausa_manual=False):
    """Extrae indicadores de energia y retorna una lista de diccionarios."""
    print("Descargando datos de energia baja en carbono...")

    df = pd.read_csv(
        FUENTE_DATOS,
        storage_options={"User-Agent": "BigData IICG energia scraper/1.0"},
    )
    df = _normalizar_columnas(df)
    df = df.dropna(subset=["pais", "anio", "porcentaje_electricidad_baja_carbono"])
    df["anio"] = df["anio"].astype(int)
    df["valor"] = df["porcentaje_electricidad_baja_carbono"].astype(float)

    df_reciente = (
        df.sort_values(["anio", "valor"], ascending=[False, False])
        .head(limite_registros)
    )

    fecha_captura = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    datos_finales = [
        {
            "identificador": fila["pais"],
            "valor": float(fila["valor"]),
            "unidad": "% electricidad baja en carbono",
            "anio": int(fila["anio"]),
            "categoria": CATEGORIA_PRODUCTO,
            "fuente": "Our World in Data",
            "integrante": INTEGRANTE,
            "grupo": "G1_Energia_AnggyJeraldo",
            "fecha_captura": fecha_captura,
        }
        for _, fila in df_reciente.iterrows()
    ]

    print(f"Registros energeticos extraidos: {len(datos_finales)}")
    return datos_finales


if __name__ == "__main__":
    registros = ejecutar_extraccion(limite_registros=500)
    for registro in registros[:3]:
        print(registro)
