import requests
from bs4 import BeautifulSoup

# 1. Definir la URL (Ellos cambiarán esto según su caso)
url = "https://www.google.com" 

# 2. Hacer la petición
headers = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(url, headers=headers)

# 3. "Cocinar" el HTML
soup = BeautifulSoup(response.text, 'html.parser')

# 4. Buscar algo (Ejemplo: El título de la página)
titulo = soup.title.string
print(f"He capturado el título: {titulo}")
