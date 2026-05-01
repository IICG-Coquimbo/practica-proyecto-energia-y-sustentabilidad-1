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
