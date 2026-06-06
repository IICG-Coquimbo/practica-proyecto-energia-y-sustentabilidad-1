# Proyecto Big Data 2026 - Sustentabilidad

Repositorio de trabajo para el Hito 1 del proyecto de Big Data orientado al analisis del impacto ambiental de la energia. El flujo integra extraccion, limpieza, consolidacion y almacenamiento en MongoDB usando Docker, PySpark y Jupyter.

## Hito 1

### Situacion problema

La toma de decisiones sobre energia y sustentabilidad suele hacerse con datos fragmentados: reportes publicos, planillas manuales y portales separados. Esto dificulta comparar generacion electrica, emisiones, tecnologias y capacidad instalada entre paises, regiones y periodos.

### Propuesta de valor

El scraping e integracion automatizada del sector energia permite consolidar datos publicos en una sola base NoSQL, normalizarlos con una estructura comun y dejarlos listos para analisis con Spark. Asi el equipo puede comparar transicion energetica, tecnologias prioritarias, presencia de renovables y capacidad de generacion sin depender de revision manual.

### Analisis de las 4V

**Volumen**

La pauta exige al menos 500 registros por integrante. El equipo integra aportes de Nicol Castillo, Thalia Gonzalez y Anggy Jeraldo; cada scraper prepara al menos 500 documentos, por lo que el volumen grupal esperado supera 1.500 registros.

**Variedad**

Los registros usan una estructura comun con fuente, dataset, URL, grupo, integrante o scraper de origen, tema, fecha de extraccion, pais, region, periodo, indicador, categoria energetica, tecnologia, actor, item, valor y unidad.

**Veracidad**

El integrador normaliza tipos, transforma `valor` a numerico, limpia strings vacios, descarta registros incompletos, deduplica y guarda con `upsert` para evitar duplicados logicos cuando un scraper vuelve a correr.

**Velocidad**

Las fuentes energeticas pueden actualizarse de forma semanal o mensual. Para datasets anuales se recomienda recargar cuando exista un nuevo corte oficial; para indicadores web dinamicos se puede ejecutar con mayor frecuencia.

## Arquitectura

- `workspace`: contenedor Jupyter/PySpark para ejecutar notebooks y el integrador.
- `database`: servicio MongoDB para almacenamiento persistente local.
- `admin-db`: Mongo Express para exploracion rapida de colecciones.
- `mongo_data`: volumen persistente para mantener los datos aunque el contenedor se reinicie.

El proyecto tambien soporta conexion a MongoDB Atlas mediante variables de entorno (`MONGODB_URI`, `MONGODB_DATABASE`, `MONGODB_COLLECTION`).

## Ejecucion

Levantar servicios:

```bash
docker compose up -d --build
```

Ejecutar la integracion:

```bash
docker compose exec workspace bash -lc "cd /home/jovyan/work && python main.py"
```

Jupyter:

```text
http://localhost:8889/lab
```

Mongo Express:

```text
http://localhost:8083
```

## Aportes individuales integrados

| Integrante | Rama | Scraper | Fuente principal | Registros esperados |
| --- | --- | --- | --- | --- |
| Nicol Castillo | `feature/Nicol-Castillo` | `scrapers/scraper_nicol_castillo.py` | EIA y CNE | 500+ |
| Thalia Gonzalez | `feature/Thalia-Gonzalez` | `scrapers/scraper_thalia_gonzalez.py` | World Resources Institute | 500 |
| Anggy Jeraldo | `feature/anggy-jeraldo` | `scrapers/scraper_anggy_jeraldo.py` | Our World in Data | 500 |

## Estructura de almacenamiento

El integrador guarda en la coleccion:

```text
proyecto_bigdata.union_semana7
```

Los documentos se separan logicamente mediante:

- `grupo`
- `integrante`
- `dataset`
- `indicador`
- `periodo`
- `scraper_origen`

## Tabla de atributos

| Etiqueta | Descripcion |
| --- | --- |
| `fuente_sitio` | Organizacion o fuente publica de origen |
| `dataset` | Dataset especifico dentro de la fuente |
| `url_origen` | URL desde la que se obtuvo el dato |
| `grupo` | Identificador del grupo de trabajo |
| `integrante` | Responsable del registro cuando el scraper lo informa |
| `tema` | Tema general del proyecto |
| `fecha_extraccion` | Momento de carga o extraccion |
| `pais` | Pais del registro |
| `region` | Estado, region o ubicacion geografica |
| `periodo` | Ano o periodo comparable del dato |
| `indicador` | Dimension analitica principal |
| `categoria_energia` | Clasificacion general de energia |
| `tecnologia` | Tecnologia o fuente especifica |
| `actor` | Productor, propietario, integrante o actor asociado |
| `item` | Identificador analitico del registro |
| `valor` | Valor numerico limpio |
| `unidad` | Unidad de medida |
| `scraper_origen` | Modulo que produjo el dato |

## Evidencias

La pauta pide adjuntar:

1. Captura de `docker stats`.
2. Captura de conteo de documentos en MongoDB.

Evidencias disponibles:

- `docs/evidencias/docker-stats.png`
- `docs/evidencias/mongo-count.png`
- `docs/evidencias/docker_stats_thalia.png`
- `docs/evidencias/conteo_mongodb_thalia.png`

Comandos sugeridos para nuevas evidencias:

```bash
docker stats --no-stream
```

```javascript
db.union_semana7.countDocuments()
```

## Estado frente a la pauta

| Requisito | Estado |
| --- | --- |
| 500 registros por integrante | Cumplido por los scrapers integrados |
| 8 o mas etiquetas | Cumplido |
| App + DB en Docker Compose | Cumplido |
| Persistencia con volumes | Cumplido con `mongo_data` |
| Estructura NoSQL | Cumplido con coleccion comun y campos de trazabilidad |
| Tipos correctos en MongoDB | Cumplido por normalizacion de `valor` y `periodo` |
| Actualizar en vez de duplicar | Cumplido con `upsert` |
| Merge a `main` | Cumplido mediante merge de ramas individuales |

## Archivos principales

- `main.py`: orquestador de scrapers, limpieza con Spark y carga a Mongo.
- `scrapers/`: carpeta de scrapers integrados.
- `docker-compose.yml`: coordinacion de servicios.
- `Dockerfile`: dependencias para scraping, Spark y conectores MongoDB.
- `docs/evidencias/`: capturas de evidencia.

## Semanas 9 a 12: huella de carbono

Este avance conserva la coleccion grupal `proyecto_bigdata.union_semana7` y utiliza
los datos de energia ya recolectados. La variable ambiental construida es la
intensidad de carbono:

```text
intensidad_kgco2_mwh = emisiones_tco2 / generacion_mwh * 1000
```

Los registros se comparan por `region`, `periodo`, `tecnologia` y
`categoria_energia`, cruzando generacion electrica con emisiones de CO2.

| Semana | Trabajo implementado | Archivo principal |
| --- | --- | --- |
| 9 | Limpieza Spark, indicador de huella, estadisticas y EDA | `semanas/Semana 9 EDA Huella Carbono/Semana9_EDA_Huella_Carbono.ipynb` |
| 10 | Estandarizacion, PCA, K-Means, metodo del codo y DBSCAN | `semanas/Semana 10 Clustering Huella Carbono/Semana10_Clustering_Huella_Carbono.ipynb` |
| 12 | Pseudo-etiquetas, clasificacion y regresion de intensidad | `semanas/Semana 12 Modelos Huella Carbono/Semana12_Modelos_Huella_Carbono.ipynb` |

El respaldo CSV de la tabla limpia queda en
`semanas/Semana 9 EDA Huella Carbono/salidas/huella_carbono_limpia.csv` y las
metricas en `semanas/Semana 12 Modelos Huella Carbono/salidas/`. Los archivos
Parquet y modelos Spark se regeneran al ejecutar los notebooks, mientras las
graficas de evidencia quedan en `docs/evidencias_semanas_9_12/`.

### Ejecucion

Con los servicios levantados mediante `docker compose up -d --build`, abrir
JupyterLab en `http://localhost:8889` y ejecutar los notebooks en orden:
Semana 9, Semana 10 y Semana 12.

Si otro avance del grupo ya ocupa esos puertos, se pueden seleccionar otros
sin modificar sus contenedores, por ejemplo:

```powershell
$env:JUPYTER_PORT="8890"; $env:VNC_PORT="6082"; $env:SPARK_UI_PORT="4042"; $env:MONGO_PORT="27019"; $env:MONGO_EXPRESS_PORT="8084"; docker compose up -d --build
```

## Hito 2: analisis inteligente y segmentacion

### Objetivo de negocio

El Hito 2 transforma los datos energeticos crudos del grupo en conocimiento para
responder la pregunta: **que combinaciones de region, tecnologia y categoria
energetica presentan mayor huella de carbono por unidad de energia generada**.

La variable central del analisis es:

```text
intensidad_kgco2_mwh = emisiones_tco2 / generacion_mwh * 1000
```

Esta metrica permite comparar emisiones relativas aunque las regiones o
tecnologias tengan escalas de generacion distintas.

### Propiedad de modulo

| Integrante | Rama | Propiedad tecnica para Hito 2 |
| --- | --- | --- |
| Anggy Jeraldo | `feature/anggy-jeraldo` | Limpieza de datos energeticos, construccion de la variable dependiente `intensidad_kgco2_mwh`, EDA multivariado, clustering e insumos para el informe grupal |
| Nicol Castillo | `feature/Nicol-Castillo` | Aporte de datos EIA/CNE sobre generacion y emisiones energeticas |
| Thalia Gonzalez | `feature/Thalia-Gonzalez` | Aporte de datos de infraestructura/capacidad energetica para contexto de sustentabilidad |

### Pipeline raw_data a processed_data

La entrega 2 separa datos crudos y datos limpios:

- Coleccion cruda: `raw_data` en Atlas para persistencia final, o
  `union_semana7` en ejecuciones locales de respaldo.
- Coleccion procesada: `processed_data`.
- Script del processor: `src/hito2_processor.py`.

Variables de entorno requeridas, usando `.env.example` como plantilla:

```text
MONGODB_URI=mongodb+srv://USUARIO:CLAVE@cluster.mongodb.net/proyecto_bigdata?retryWrites=true&w=majority
MONGODB_DATABASE=proyecto_bigdata
MONGODB_COLLECTION=raw_data
MONGODB_PROCESSED_COLLECTION=processed_data
```

Ejecutar el contenedor processor:

```bash
docker compose --profile hito2 run --rm processor
```

En pruebas locales, si aun se trabaja con el respaldo de la primera integracion,
`MONGODB_COLLECTION` puede apuntar a `union_semana7`.

### Requerimientos tecnicos cubiertos

| Requisito Hito 2 | Implementacion |
| --- | --- |
| Limpieza de nulos, duplicados y formatos | `limpiar_base()` normaliza tipos, elimina registros incompletos y deduplica por claves energeticas |
| 3+ atributos derivados | `intensidad_kgco2_mwh`, `log_generacion_mwh`, `log_emisiones_tco2`, `nivel_huella`, participaciones porcentuales y brecha contra promedio |
| EDA multivariado | Semana 9 compara region, tecnologia, categoria, generacion, emisiones e intensidad |
| Clustering | Semana 10 aplica PCA, K-Means y DBSCAN |
| Variable dependiente Hito 3 | `intensidad_kgco2_mwh` |
| Separacion raw/processed | `src/hito2_processor.py` escribe en `processed_data` |
| Insumo para informe grupal | `docs/hito2/aporte_anggy_hito2.md` |

### Resultados principales

- Datos crudos usados en el respaldo local: 2.686 documentos.
- Registros procesados comparables de huella: 164.
- Promedio renovable: 22,12 kg CO2/MWh.
- Promedio fosil: 876,64 kg CO2/MWh.
- K-Means genera 3 perfiles de huella.
- DBSCAN detecta observaciones atipicas para revision.
- La variable predictiva propuesta para el Hito 3 es `intensidad_kgco2_mwh`.

### Archivos del Hito 2

- `src/hito2_processor.py`: processor del pipeline.
- `docs/hito2/README_HITO2.md`: resumen operativo del hito.
- `docs/hito2/aporte_anggy_hito2.md`: texto y resultados del modulo de Anggy para que el grupo los revise antes de consolidar el informe final.
- `docs/evidencias_semanas_9_12/`: graficos EDA y clustering.
