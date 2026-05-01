import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


INTEGRANTE = "Anggy_Jeraldo"
CATEGORIA_PRODUCTO = "Laptops"
URL_BUSQUEDA = "https://www.amazon.es/s?k=laptops"


def _limpiar_precio(valor):
    texto = str(valor).replace(".", "").replace(",", "").strip()
    return float(texto) if texto.isdigit() else 0.0


def _crear_driver():
    options = Options()

    if os.path.exists("/usr/bin/google-chrome"):
        options.binary_location = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/brave-browser"):
        options.binary_location = "/usr/bin/brave-browser"

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    return webdriver.Chrome(options=options)


def ejecutar_extraccion(limite_paginas=1, pausa_manual=True):
    """Extrae productos de Amazon y retorna una lista de diccionarios."""
    datos_finales = []
    driver = None

    try:
        driver = _crear_driver()
        driver.get(URL_BUSQUEDA)

        if pausa_manual:
            print("Accede a http://localhost:6080/vnc.html y valida el navegador.")
            input("Presiona ENTER cuando la pagina este lista para extraer datos...")

        titulo = driver.title.lower()
        if "robot" in titulo or "captcha" in titulo:
            print("Bloqueo real detectado en el titulo del navegador.")
            return datos_finales

        for numero_pagina in range(limite_paginas):
            print(f"Procesando pagina {numero_pagina + 1}")
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
                )
            )

            bloques = driver.find_elements(
                By.CSS_SELECTOR, "div[data-component-type='s-search-result']"
            )

            for bloque in bloques:
                try:
                    nombre = bloque.find_element(By.TAG_NAME, "h2").text.strip()
                    precio = bloque.find_element(By.CSS_SELECTOR, ".a-price-whole").text
                    valor = _limpiar_precio(precio)

                    if nombre and valor > 0:
                        datos_finales.append(
                            {
                                "identificador": nombre,
                                "valor": valor,
                                "categoria": CATEGORIA_PRODUCTO,
                                "integrante": INTEGRANTE,
                                "grupo": "G1_Amazon_AnggyJeraldo",
                                "fecha_captura": time.strftime("%Y-%m-%d %H:%M:%S"),
                            }
                        )
                except Exception:
                    continue

            if numero_pagina == limite_paginas - 1:
                break

            try:
                boton_siguiente = driver.find_element(By.CLASS_NAME, "s-pagination-next")
                driver.execute_script("arguments[0].click();", boton_siguiente)
                time.sleep(5)
            except Exception:
                break

    except Exception as exc:
        print(f"Error en Selenium: {exc}")
    finally:
        if driver is not None:
            driver.quit()

    print(f"Productos extraidos: {len(datos_finales)}")
    return datos_finales


if __name__ == "__main__":
    productos = ejecutar_extraccion(limite_paginas=1, pausa_manual=True)
    for producto in productos[:3]:
        print(producto)

