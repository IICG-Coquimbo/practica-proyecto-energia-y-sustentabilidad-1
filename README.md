# Proyecto Big Data 2026 - Sustentabilidad

Repositorio de trabajo para el Hito 1 del proyecto de Big Data orientado al analisis del impacto ambiental de la energia. El flujo integra extraccion, limpieza, consolidacion y almacenamiento en MongoDB usando Docker, PySpark y Jupyter.

## Hito 1

### Situacion problema
Hoy la toma de decisiones sobre energia y sustentabilidad suele hacerse con datos fragmentados: una parte en reportes publicos, otra en planillas manuales y otra en portales distintos. Eso dificulta comparar generacion electrica, emisiones y proyectos energeticos entre paises, regiones y tecnologias dentro del mismo periodo.

### Propuesta de valor
El scraping e integracion automatizada del sector energia permite consolidar en una sola base NoSQL datos publicos de EIA y CNE, normalizarlos y dejar listas comparaciones entre generacion, emisiones y almacenamiento. Esto reduce trabajo manual, mejora la trazabilidad del dato y acelera decisiones sobre transicion energetica, tecnologias prioritarias y seguimiento de proyectos.

### Analisis de las 4V

**Volumen**

El criterio del curso exige mas de 500 registros por integrante y mas de 3.000 a nivel grupal. En este aporte individual se consolidaron 2.186 registros validos para un solo ano comparable, por lo que el volumen individual ya supera el minimo exigido. La integracion grupal permite escalar el total del repositorio hasta el umbral global.

**Variedad**

Cada documento contiene 18 etiquetas, incluyendo fuente, dataset, URL, grupo, integrante, tema, fecha de extraccion, pais, region, periodo, indicador, categoria energetica, tecnologia, actor, item, valor, unidad y scraper de origen. Esta variedad permite contextualizar los valores numericos antes de compararlos.

**Veracidad**

La veracidad se asegura con limpieza de tipos, normalizacion de numericos, descarte de vacios, filtrado de valores no validos, deduplicacion y seleccion automatica del ultimo ano comun entre todos los datasets. Asi se evita comparar periodos distintos o cargar precios/valores como strings inconsistentes.

**Velocidad**

La frecuencia ideal de actualizacion depende de la fuente. Para los proyectos de energia y almacenamiento conviene una revision mensual, mientras que los datasets anuales de generacion y emisiones pueden recargarse cuando la fuente publica entregue un nuevo corte oficial. En el proyecto se priorizo una fotografia consistente del ano 2024 para comparacion.

## Arquitectura

- `workspace`: contenedor Jupyter/PySpark para ejecutar notebooks y el integrador.
- `database`: servicio MongoDB para almacenamiento persistente local.
- `admin-db`: Mongo Express para exploracion rapida de colecciones.
- `mongo_data`: volumen persistente para mantener los datos aunque el contenedor se reinicie.

El proyecto tambien soporta conexion a MongoDB Atlas mediante variables de entorno (`MONGODB_URI`, `MONGODB_DATABASE`, `MONGODB_COLLECTION`).

## Ejecucion

Comando solicitado por la pauta:

```bash
docker compose up -d
```

Comando recomendado para primera ejecucion o cuando cambia la imagen:

```bash
docker compose up -d --build
```

Para ejecutar la integracion:

```bash
docker compose exec workspace bash -lc "cd /home/jovyan/work && python main.py"
```

Para visualizar en Jupyter:

```text
http://localhost:8889/lab
```

Notebook principal de visualizacion:

- `semanas/Semana 7 La union/Visualizacion_Semana7.ipynb`

## Resultados tecnicos del aporte individual

- Registros validados: `2186`
- Ano comun utilizado para la comparacion: `2024`
- Datasets consolidados:
  - `annual_generation_state`: 1437
  - `emission_annual`: 715
  - `pmgd`: 27
  - `pgeneracion`: 5
  - `bess`: 2
- Campos por documento: `18`

El integrador realiza limpieza con Spark y luego guarda en Mongo usando `upsert`, evitando duplicados logicos cuando el scraper vuelve a procesar los mismos registros.

## Estructura de almacenamiento

Se usa una coleccion general con separacion logica por medio de los campos:

- `grupo`
- `integrante`
- `dataset`
- `indicador`
- `periodo`

Esto permite filtrar por responsable, fuente y dimension analitica sin perder trazabilidad.

## Tabla de atributos

| Integrante | Etiqueta | Descripcion |
| --- | --- | --- |
| Nicol Castillo | `fuente_sitio` | Organizacion o fuente publica de origen |
| Nicol Castillo | `dataset` | Dataset especifico dentro de la fuente |
| Nicol Castillo | `url_origen` | URL desde la que se obtuvo el dato |
| Nicol Castillo | `grupo` | Identificador del grupo de trabajo |
| Nicol Castillo | `integrante` | Responsable del registro |
| Nicol Castillo | `tema` | Tema general del proyecto |
| Nicol Castillo | `fecha_extraccion` | Momento de carga o extraccion |
| Nicol Castillo | `pais` | Pais del registro |
| Nicol Castillo | `region` | Estado, region o ubicacion geografica |
| Nicol Castillo | `periodo` | Ano comparable del dato |
| Nicol Castillo | `indicador` | Dimension analitica principal |
| Nicol Castillo | `categoria_energia` | Clasificacion general de energia |
| Nicol Castillo | `tecnologia` | Tecnologia o fuente especifica |
| Nicol Castillo | `actor` | Productor, propietario o actor asociado |
| Nicol Castillo | `item` | Identificador analitico del registro |
| Nicol Castillo | `valor` | Valor numerico limpio |
| Nicol Castillo | `unidad` | Unidad de medida |
| Nicol Castillo | `scraper_origen` | Modulo que produjo el dato |

## Evidencias solicitadas

La pauta pide adjuntar dos capturas en el README o en el repositorio:

1. Evidencia 1: `docker stats` mostrando consumo de contenedores.
2. Evidencia 2: conteo de documentos en MongoDB (`db.coleccion.countDocuments()`).

Se dejo la carpeta `docs/evidencias/` para agregar esas imagenes antes del cierre final del hito.

Comandos sugeridos para obtenerlas:

```bash
docker stats --no-stream
```

```javascript
db.union_semana7.countDocuments()
```

## Actividad Git

La rama individual `feature/Nicol-Castillo` contiene actividad distribuida en varias semanas, incluyendo preparacion de entorno, integracion, visualizacion y ajuste del ano comun para comparacion consistente.

## Semanas 9 y 10: EDA y aprendizaje no supervisado

La entrega extiende la integracion de Semana 7 usando los registros EIA del periodo comun. Los datos CNE permanecen disponibles en la coleccion, pero se excluyen de las relaciones generacion-emisiones porque representan proyectos en `MW` y no energia generada en `MWh`.

### Semana 9 - Procesamiento con Spark y EDA

Notebook principal:

- `semanas/Semana 9 EDA Spark/EDA_Semana9.ipynb`

Script reproducible:

- `semanas/Semana 9 EDA Spark/eda_semana9.py`

El analisis lee MongoDB mediante Spark y usa automaticamente el CSV de Semana 7 como respaldo si Mongo no esta disponible. Incluye limpieza y deduplicacion, revision de nulos, creacion de intensidad de CO2 (`toneladas CO2 / MWh`), participacion de generacion, transformaciones logaritmicas, puntaje z, outliers IQR, asimetria, correlaciones Pearson/Spearman y graficos.

### Semana 10 - Clustering

Notebook principal:

- `semanas/Semana 10 Clustering/Clustering_Semana10.ipynb`

Script reproducible:

- `semanas/Semana 10 Clustering/clustering_semana10.py`

Este flujo consume `features_eda_semana9.csv`, estandariza variables, reduce dimensiones con PCA y aplica K-means. La seleccion de `k` evalua inercia y silhouette para no imponer un numero de clusters sin evidencia. DBSCAN complementa el analisis identificando puntos aislados (`cluster = -1`).

### Ejecucion

Primero levante el entorno actualizado:

```bash
docker compose up -d --build
```

En una instalacion nueva o si la coleccion MongoDB esta vacia, genere primero la base integrada de Semana 7:

```bash
docker compose exec workspace bash -lc "cd /home/jovyan/work && python main.py"
```

Luego abra Jupyter en `http://localhost:8889/lab` y ejecute, en orden:

1. `semanas/Semana 9 EDA Spark/EDA_Semana9.ipynb`
2. `semanas/Semana 10 Clustering/Clustering_Semana10.ipynb`
3. `semanas/Semana 12 Pseudo-labeling/PseudoLabeling_Semana12.ipynb`

Las salidas se escriben en las carpetas `salidas/` de cada semana, incluyendo CSV analiticos y figuras PNG. Para probar Semana 9 solamente con el CSV local, se puede definir `FUENTE_DATOS=csv` antes de ejecutar el script.

### Resultados verificados

La ejecucion en Docker leyendo `proyecto_bigdata.union_semana7` mediante Spark-MongoDB produjo:

- `3.180` documentos de entrada y `2.152` registros EIA limpios.
- `80` perfiles region-categoria con generacion y emisiones comparables.
- `6` perfiles atipicos segun IQR de intensidad CO2.
- Correlacion Pearson generacion-emisiones: `0,9484`.
- PCA con dos componentes: `91,23%` de varianza explicada acumulada.
- K-means: `k=3` seleccionado por silhouette.
- DBSCAN: `20` observaciones marcadas como ruido para investigacion posterior.

## Semana 12: Aprendizaje semi-supervisado

Semana 12 reutiliza el resultado de K-means como pseudo-etiqueta. Por esta razon, Semana 10 ahora guarda automaticamente:

- `semanas/Semana 10 Clustering/modelos/datos_etiquetados_kmeans`: registros y clusters en formato Parquet.
- `semanas/Semana 10 Clustering/modelos/kmeans_energia_v1`: modelo K-means persistido por Spark.

Notebook principal:

- `semanas/Semana 12 Pseudo-labeling/PseudoLabeling_Semana12.ipynb`

Script reproducible:

- `semanas/Semana 12 Pseudo-labeling/pseudo_labeling_semana12.py`

El analisis convierte el cluster de K-means en `label`, divide los datos en entrenamiento/prueba y compara Arbol de Decision, Random Forest, SVM con estrategia OneVsRest y Regresion Logistica Multinomial. Tambien entrena una regresion lineal para predecir `intensidad_co2`; no usa emisiones como predictor porque eso constituiria fuga de informacion.

El ticket de salida distingue entre replicar las reglas geometricas de K-means y predecir un fenomeno ambiental real: para mejorar este ultimo caso se requieren variables como combustible, tecnologia detallada, eficiencia y condiciones operacionales.

### Resultados verificados de Semana 12

La ejecucion en Docker usando las `80` pseudo-etiquetas obtenidas en Semana 10 produjo:

- Arbol de Decision: `96,97%` de accuracy.
- Random Forest: `100,00%` de accuracy.
- SVM OneVsRest: `96,97%` de accuracy.
- Regresion Logistica Multinomial: `100,00%` de accuracy.
- Regresion lineal regularizada de intensidad CO2: `R2 = -0,0616` y `RMSE = 0,670230`.

Los clasificadores replican muy bien la regla geometrica creada por K-means, mientras que la regresion evidencia que volumen y participacion de generacion no explican por si solos la intensidad ambiental real.

## Archivos principales

- `main.py`: orquestador de scrapers, limpieza con Spark y carga a Mongo.
- `scrapers/scraper_nicol_castillo.py`: scraper e integracion del aporte individual.
- `semanas/Semana 7 La union/Visualizacion_Semana7.ipynb`: revision de resultados en Jupyter.
- `semanas/Semana 9 EDA Spark/EDA_Semana9.ipynb`: EDA, correlaciones y variables derivadas.
- `semanas/Semana 10 Clustering/Clustering_Semana10.ipynb`: PCA, K-means y DBSCAN.
- `semanas/Semana 12 Pseudo-labeling/PseudoLabeling_Semana12.ipynb`: pseudo-etiquetas, clasificadores y regresion.
- `docker-compose.yml`: coordinacion de servicios.
- `Dockerfile.jupyter`: dependencias para scraping, Spark y conectores MongoDB.
