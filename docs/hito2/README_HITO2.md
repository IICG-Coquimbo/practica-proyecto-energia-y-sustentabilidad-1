# Hito 2 - Analisis inteligente y segmentacion

## Caso de negocio

El proyecto grupal analiza emisiones de energia y sustentabilidad. Para el Hito 2,
el foco tecnico de esta rama es transformar datos crudos de generacion y emisiones
en una tabla procesada de huella de carbono, expresada como `kg CO2/MWh`.

## Flujo de datos

1. `raw_data` o `union_semana7`: datos crudos integrados desde los scrapers del grupo.
2. `src/hito2_processor.py`: limpieza, deduplicacion, ingenieria de atributos y escritura.
3. `processed_data`: coleccion final del Hito 2 con datos limpios y atributos derivados.
4. Notebooks Semana 9, 10 y 12: EDA, clustering y definicion predictiva.

Validacion local realizada:

- `union_semana7`: 2.686 documentos.
- `processed_data`: 164 documentos procesados.
- La validacion local usa MongoDB en Docker como respaldo. Para la entrega final,
  la URI debe apuntar a MongoDB Atlas mediante variables de entorno.

## Atributos derivados

- `intensidad_tco2_mwh`
- `intensidad_kgco2_mwh`
- `log_generacion_mwh`
- `log_emisiones_tco2`
- `nivel_huella`
- `participacion_emisiones_pct`
- `participacion_generacion_pct`
- `brecha_vs_promedio_kgco2_mwh`

## Variable dependiente propuesta

Para el Hito 3 se propone predecir `intensidad_kgco2_mwh`, porque representa la
huella relativa de carbono de cada combinacion region-tecnologia-periodo.

## Archivos clave

- `src/hito2_processor.py`
- `huella_carbono_pipeline.py`
- `semanas/Semana 9 EDA Huella Carbono/Semana9_EDA_Huella_Carbono.ipynb`
- `semanas/Semana 10 Clustering Huella Carbono/Semana10_Clustering_Huella_Carbono.ipynb`
- `semanas/Semana 12 Modelos Huella Carbono/Semana12_Modelos_Huella_Carbono.ipynb`
- `docs/hito2/aporte_anggy_hito2.md`
