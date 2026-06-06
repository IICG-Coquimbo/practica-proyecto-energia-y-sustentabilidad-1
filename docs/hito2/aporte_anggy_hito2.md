# Aporte Anggy Jeraldo - Hito 2

Este documento no reemplaza el informe grupal en PDF. Su objetivo es dejar
auditable el aporte individual de Anggy para que el grupo revise, consolide y
cargue un unico informe final con los aportes de las tres integrantes.

## Responsabilidad tecnica

| Estudiante | Rama | Responsabilidad |
| --- | --- | --- |
| Anggy Jeraldo | `feature/anggy-jeraldo` | Limpieza de datos energeticos, construccion de la variable dependiente, EDA multivariado, clustering y preparacion de insumos para el informe grupal |

## Pregunta de negocio abordada

Que combinaciones de region, tecnologia y categoria energetica presentan mayor
huella de carbono por unidad de energia generada.

## Datos utilizados

- Coleccion cruda de respaldo: `proyecto_bigdata.union_semana7`.
- Coleccion final requerida para Atlas: `processed_data`.
- Registros crudos usados en la prueba local: 2.686.
- Registros comparables procesados para huella de carbono: 164.
- Validacion local del processor: `processed_data` quedo con 164 documentos.

## Limpieza aplicada

- Conversion de `periodo` a entero.
- Conversion de `valor` a numerico.
- Normalizacion de `region`, `tecnologia` y `categoria_energia`.
- Eliminacion de valores nulos y registros con `valor <= 0`.
- Eliminacion de duplicados por dataset, region, periodo, indicador, tecnologia y valor.
- Filtro de intensidades fuera de rango operativo.

## Atributos derivados

- `intensidad_tco2_mwh`
- `intensidad_kgco2_mwh`
- `log_generacion_mwh`
- `log_emisiones_tco2`
- `nivel_huella`
- `participacion_emisiones_pct`
- `participacion_generacion_pct`
- `brecha_vs_promedio_kgco2_mwh`

## Resultados descriptivos

- Promedio energia renovable: 22,12 kg CO2/MWh.
- Promedio energia fosil: 876,64 kg CO2/MWh.
- Correlacion entre generacion y emisiones: 0,9334.
- La evidencia muestra que la categoria energetica y la tecnologia explican
  diferencias relevantes en la huella relativa.

## Segmentacion

Semana 10 aplica K-Means con `k=3`, PCA para visualizacion y DBSCAN para detectar
observaciones atipicas.

Distribucion K-Means:

| Cluster | Registros | Promedio kg CO2/MWh |
| --- | ---: | ---: |
| 0 | 57 | 438,13 |
| 1 | 49 | 1199,18 |
| 2 | 58 | 1161,25 |

DBSCAN detecto 16 observaciones como ruido o posibles casos atipicos.

## Variable dependiente propuesta para Hito 3

La variable dependiente propuesta es `intensidad_kgco2_mwh`, porque permite
predecir la huella relativa de carbono asociada a cada combinacion
region-tecnologia-periodo.

Los modelos supervisados de prueba muestran que las pseudo-etiquetas de cluster
son separables, pero la regresion lineal inicial indica que para predecir con
mayor precision se requieren variables operacionales adicionales: combustible,
factor de emision, eficiencia, horas de operacion y mezcla de generacion.

## Archivos de respaldo

- `src/hito2_processor.py`
- `huella_carbono_pipeline.py`
- `semanas/Semana 9 EDA Huella Carbono/Semana9_EDA_Huella_Carbono.ipynb`
- `semanas/Semana 10 Clustering Huella Carbono/Semana10_Clustering_Huella_Carbono.ipynb`
- `semanas/Semana 12 Modelos Huella Carbono/Semana12_Modelos_Huella_Carbono.ipynb`
- `docs/evidencias_semanas_9_12/`
