import os
from io import StringIO
from datetime import datetime, timezone

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


INTEGRANTE = os.getenv("INTEGRANTE", "anggy jeraldo")
NOMBRE_GRUPO = os.getenv("NOMBRE_GRUPO", "energia-y-sustentabilidad-1")
TEMA_PROYECTO = os.getenv("TEMA_PROYECTO", "Impacto ambiental de la energia")
DATASET = "share-electricity-low-carbon"
FUENTE_DATOS = (
    "https://ourworldindata.org/grapher/share-electricity-low-carbon.csv"
    "?v=1&csvType=full&useColumnShortNames=false"
)
URL_ORIGEN = "https://ourworldindata.org/grapher/share-electricity-low-carbon"


def _crear_driver():
    options = Options()

    if os.path.exists("/usr/bin/google-chrome"):
        options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/brave-browser"):
        options.binary_location = "/usr/bin/brave-browser"

    if os.getenv("SCRAPER_HEADLESS", "1") == "1":
        options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(options=options)


def _descargar_csv_con_selenium():
    driver = _crear_driver()
    try:
        driver.get(URL_ORIGEN)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        texto_csv = driver.execute_async_script(
            """
            const url = arguments[0];
            const done = arguments[arguments.length - 1];
            fetch(url)
                .then(response => response.text())
                .then(text => done(text))
                .catch(error => done(`ERROR: ${error}`));
            """,
            FUENTE_DATOS,
        ).strip()

        if "Entity" not in texto_csv or "Year" not in texto_csv:
            raise ValueError("Selenium no obtuvo el CSV esperado desde la pagina.")

        return texto_csv
    finally:
        driver.quit()


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
    print("Descargando datos de energia baja en carbono con Selenium...")

    texto_csv = _descargar_csv_con_selenium()
    df = pd.read_csv(StringIO(texto_csv))
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
            "fuente_sitio": "Our World in Data",
            "dataset": DATASET,
            "url_origen": URL_ORIGEN,
            "grupo": NOMBRE_GRUPO,
            "tema": TEMA_PROYECTO,
            "fecha_extraccion": fecha_captura,
            "pais": fila["pais"],
            "region": "Internacional",
            "periodo": int(fila["anio"]),
            "indicador": "Porcentaje de electricidad baja en carbono",
            "categoria_energia": "Electricidad baja en carbono",
            "tecnologia": "Renovables y nuclear",
            "actor": INTEGRANTE,
            "item": f"{fila['pais']} - electricidad baja en carbono - {int(fila['anio'])}",
            "valor": float(fila["valor"]),
            "unidad": "% electricidad baja en carbono",
        }
        for _, fila in df_reciente.iterrows()
    ]

    print(f"Registros energeticos extraidos: {len(datos_finales)}")
    return datos_finales


if __name__ == "__main__":
    registros = ejecutar_extraccion(limite_registros=500)
    for registro in registros[:3]:
        print(registro)
