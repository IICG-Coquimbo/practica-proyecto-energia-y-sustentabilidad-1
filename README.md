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

## Archivos principales

- `main.py`: orquestador de scrapers, limpieza con Spark y carga a Mongo.
- `scrapers/scraper_nicol_castillo.py`: scraper e integracion del aporte individual.
- `semanas/Semana 7 La union/Visualizacion_Semana7.ipynb`: revision de resultados en Jupyter.
- `docker-compose.yml`: coordinacion de servicios.
- `Dockerfile.jupyter`: dependencias para scraping, Spark y conectores MongoDB.
