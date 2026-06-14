# Semana 15 - Dashboard interactivo de huella de carbono

Esta semana transforma los KPIs generados en Semana 14 en un tablero interactivo con Streamlit.

## Ejecutar

Desde la raiz del proyecto:

```powershell
docker compose up -d --build
docker compose exec workspace bash -lc "cd /home/jovyan/work/semanas/Semana\ 15\ Dashboard\ Huella\ Carbono && streamlit run app.py --server.address 0.0.0.0 --server.port 8501"
```

Abrir:

```text
http://localhost:8501
```

Si el puerto esta ocupado, definir otro puerto antes de levantar Docker:

```powershell
$env:STREAMLIT_PORT="8502"
docker compose up -d --build
```
