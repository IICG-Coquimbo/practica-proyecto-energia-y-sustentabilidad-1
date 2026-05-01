import requests
import pandas as pd

# Intentemos capturar datos reales de la API de intercambio de monedas
try:
    url = 'https://api.exchangerate-api.com/v4/latest/USD'
    respuesta = requests.get(url)
    datos = respuesta.json()
    
    # Creamos un pequeño resumen de los tipos de cambio
    df = pd.DataFrame(datos['rates'].items(), columns=['Moneda', 'Valor'])
    print("¡Conexión exitosa! Aquí los primeros datos capturados:")
    print(df.head())
except Exception as e:
    print(f"Error en la conexión: {e}")