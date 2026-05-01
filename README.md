# Proyecto Big Data 2026 - Sustentabilidad

Repositorio de trabajo para el Hito 1 del proyecto de Big Data orientado al analisis del impacto ambiental de la energia.

## Hito 1

### Situacion problema

La organizacion necesita comparar capacidad de generacion electrica por pais, region y tecnologia, pero esta informacion suele revisarse de forma manual en reportes o archivos separados. Eso dificulta decidir que tecnologias renovables y no renovables tienen mayor presencia, donde se concentran y que actores aparecen asociados a la generacion energetica.

### Propuesta de valor

El scraper de energia consolida datos publicos de plantas electricas en una estructura comun de 16 etiquetas. Esto permite cargar los registros en MongoDB, analizarlos con Spark y comparar categoria energetica, tecnologia, pais, actor y capacidad instalada sin depender de planillas manuales.

### Analisis de las 4V

**Volumen:** el aporte individual de Thalia Gonzalez contiene 500 registros validos, cumpliendo el minimo de 500 documentos por integrante solicitado en la pauta.

**Variedad:** cada documento usa 16 etiquetas: fuente, dataset, URL, grupo, tema, fecha, pais, region, periodo, indicador, categoria energetica, tecnologia, actor, item, valor y unidad.

**Veracidad:** el scraper elimina registros sin item, tecnologia, categoria energetica o valor. El campo `valor` se convierte a numero `float` y se descartan valores menores o iguales a cero.

**Velocidad:** para este sector, la actualizacion puede ejecutarse semanal o mensualmente, porque los datos de infraestructura energetica no cambian tan rapido como precios de retail, pero si requieren seguimiento periodico.

## Aporte individual: Thalia Gonzalez

- Rama de trabajo: `Thalia-Gonzalez`
- Scraper: `scrapers/scraper_thalia_gonzalez.py`
- Fuente: World Resources Institute
- Dataset: `global_power_plant_database`
- URL origen: `https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv`
- Registros preparados: `500`
- Coleccion MongoDB sugerida: `proyecto_bigdata.energia_sustentabilidad`
- Archivo cache usado para evidencia: `Energy/datos_auditoria_global.csv`

## Etiquetas extraidas

| # | Etiqueta | Descripcion |
|---|---|---|
| 1 | `fuente_sitio` | Organizacion o sitio fuente del dato |
| 2 | `dataset` | Nombre del dataset de origen |
| 3 | `url_origen` | URL desde donde se obtuvo el dato |
| 4 | `grupo` | Identificador del grupo de trabajo |
| 5 | `tema` | Tema del proyecto |
| 6 | `fecha_extraccion` | Fecha y hora de captura |
| 7 | `pais` | Pais asociado al registro |
| 8 | `region` | Region o codigo geografico |
| 9 | `periodo` | Periodo del dato |
| 10 | `indicador` | Indicador medido |
| 11 | `categoria_energia` | Clasificacion energetica |
| 12 | `tecnologia` | Tecnologia o fuente energetica |
| 13 | `actor` | Operador, propietario o actor asociado |
| 14 | `item` | Nombre identificador del registro |
| 15 | `valor` | Valor numerico limpio |
| 16 | `unidad` | Unidad de medida |

## Arquitectura

- `workspace`: contenedor Jupyter/PySpark para ejecutar notebooks y scripts.
- `database`: servicio MongoDB local.
- `visualizer`: Mongo Express para revisar colecciones.
- `filebrowser`: gestor de archivos del proyecto.
- `mongo_data`: volumen persistente para mantener datos de MongoDB aunque se reinicie el contenedor.

## Ejecucion

Levantar servicios:

```bash
docker-compose up -d --build
```

Ejecutar integracion:

```bash
python main.py
```

Variables opcionales:

```bash
set MONGO_URI=mongodb://database:27017/
set MONGO_DATABASE=proyecto_bigdata
set MONGO_COLLECTION=energia_sustentabilidad
set LIMITE_EXTRACCION=500
```

Para usar MongoDB Atlas, definir `MONGO_URI` con la cadena del grupo solo en el entorno local. No subir credenciales al repositorio.

## Validacion esperada

El programa imprime:

- muestra de 3 registros procesados;
- total de registros procesados;
- reporte Spark con capacidad promedio por categoria energetica y tecnologia.

Conteo en MongoDB:

```javascript
db.energia_sustentabilidad.countDocuments()
```

## Estado frente a la pauta

| Requisito | Estado |
|---|---|
| 500 registros por integrante | Cumplido: 500 registros preparados |
| 8 o mas etiquetas | Cumplido: 16 etiquetas |
| Tipos correctos en MongoDB | Cumplido en el scraper: `valor` se entrega como `float` |
| App + DB en Docker Compose | Cumplido: `workspace` + `database` |
| Persistencia con volumes | Cumplido: volumen `mongo_data` |
| Estructura NoSQL | Cumplido: coleccion sugerida `energia_sustentabilidad` |
| Actualizar en vez de duplicar | Cumplido en `main.py` con operaciones `upsert` |
| README con business case y 4V | Cumplido en este README |
| Evidencia docker stats | Cumplido: `docs/evidencias/docker_stats_thalia.png` |
| Evidencia conteo MongoDB | Cumplido: `docs/evidencias/conteo_mongodb_thalia.png` |
| Merge a rama principal/grupal | Pendiente: debe hacerlo el grupo cuando integren aportes |
| 5 commits por integrante en 3 semanas | Revisar historial de GitHub antes de la entrega final |
