# Entrega Big Data - Thalia Gonzalez

Proyecto de energia y sustentabilidad para las semanas 5, 6 y 7.

## Contenido

- `scrapers/scraper_thalia_gonzalez.py`: extractor normalizado como funcion `ejecutar_extraccion()`.
- `main.py`: integrador que guarda datos en MongoDB y genera un reporte con Spark.
- `Energy/datos_auditoria_global.csv`: datos base usados como cache reproducible.

## Ejecucion

Desde Jupyter o desde la terminal del contenedor:

```bash
python main.py
```

Variables opcionales:

```bash
export MONGO_URI="mongodb://database:27017/"
export MONGO_DATABASE="proyecto_bigdata"
export MONGO_COLLECTION="energia_sustentabilidad"
export LIMITE_EXTRACCION="500"
```

## Evidencia esperada

El programa imprime:

- al menos 3 registros procesados;
- total de productos procesados;
- tabla Spark con capacidad promedio por categoria energetica y tecnologia.

