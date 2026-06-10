# Semana 15: Tableros interactivos

Dashboard interactivo en Streamlit para explorar indicadores de energia,
emisiones e intensidad ambiental.

## Archivos

- `app.py`: aplicacion Streamlit con tres niveles de analisis.
- `datos_energia_dashboard.csv`: dataset liviano exportado desde el procesamiento Spark/Pandas.

## Ejecucion

Desde la carpeta del proyecto dentro del contenedor:

```bash
cd /home/jovyan/work/semanas/Semana\ 15\ Tableros\ interactivos
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Luego abrir:

```text
http://localhost:8501
```

## Celda de exportacion sugerida

Si se vuelve a generar el dataframe procesado desde Spark, se puede exportar asi:

```python
df_completos.toPandas().to_csv(
    "/home/jovyan/work/semanas/Semana 15 Tableros interactivos/datos_energia_dashboard.csv",
    index=False,
)
print("Datos exportados listos para Streamlit")
```
