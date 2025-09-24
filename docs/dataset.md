# Dataset elegido: Real Estate Sales 2001–2018

## Fuente
- URL: https://catalog.data.gov/dataset/real-estate-sales-2001-2018
- Origen: Portal de datos abiertos (ventas inmobiliarias, 2001–2018)
- Formato: CSV (múltiples columnas por venta; apto para carga en PostgreSQL)
- Tamaño: mediano (adecuado para Docker + Postgres local)

## Descripción breve
Registros de **ventas de inmuebles** (residenciales/comerciales) con atributos típicos:
- Fecha de venta y **precio de venta**.
- Identificador/parcel ID del inmueble, **dirección**, ciudad/municipio, ZIP.
- Características del inmueble (p. ej. **año de construcción**, superficie cubierta/terreno si están disponibles).
- Campos de valuación administrativa (assessment/appraisal) y metadatos de la escritura (si aplica).

> Nota: los nombres exactos de columnas pueden variar según la versión del dataset; ajustaremos el DDL en el Ej3 al confirmar el layout final.

## Motivación
- Datos reales y **fuertemente relacionales** (propiedad ↔ ventas ↔ ubicación).
- Permite análisis de negocio reales: tendencia de precios, “hot areas”, relación precio/m², sesgos por año de construcción, etc.
- Volumen suficiente para practicar índices, partición temporal, y reporting.

## Esquema lógico (propuesto para Postgres)
- **municipalities**
  - `municipality_id SERIAL PRIMARY KEY`
  - `name TEXT UNIQUE NOT NULL`
- **properties**
  - `property_id BIGSERIAL PRIMARY KEY`
  - `parcel_id TEXT UNIQUE`            -- si existe en el dataset
  - `address TEXT`, `zip_code TEXT`
  - `municipality_id INT REFERENCES municipalities(municipality_id)`
  - `year_built INT`, `building_sqft INT`, `land_sqft INT`
  - `property_type TEXT`               -- residential, commercial, etc. (si existe)
  - `lat NUMERIC(9,6)`, `lon NUMERIC(9,6)`  -- si hay coordenadas
- **sales**
  - `sale_id BIGSERIAL PRIMARY KEY`
  - `property_id BIGINT REFERENCES properties(property_id)`
  - `sale_date DATE NOT NULL`
  - `sale_price NUMERIC(14,2) NOT NULL`
  - `assessed_value NUMERIC(14,2)`, `appraised_value NUMERIC(14,2)`  -- si existen
  - `is_non_arms_length BOOLEAN`                                      -- si podemos inferirlo
  - `deed_book TEXT`, `deed_page TEXT`                                -- si existen

**Índices sugeridos**:
- `sales (sale_date)`, `sales (sale_price)`, `properties (municipality_id)`, `properties (parcel_id)`.

## Preguntas de negocio (consultables en SQL)
1. **Tendencia anual por municipio:** ¿cómo evoluciona la **mediana** del precio de venta por año y municipio? (top municipalidades por crecimiento YoY).
2. **Precio por m² (o sqft):** para propiedades residenciales, ¿qué municipios tienen **mayor** y **menor** precio por m² promedio?
3. **Género de stock/antigüedad:** ¿cómo se relaciona el **año de construcción** con el precio (curva precio vs. antigüedad)?
4. **Ratio valuación/venta:** ¿cómo varía el **assessment-to-sale ratio** por municipio y año? (útil para detectar sub/sobrevaluación).
5. **Reventas del mismo inmueble:** en propiedades con múltiples ventas, ¿cuál es el **cambio porcentual** entre ventas consecutivas?
6. **Detección de outliers:** ventas con precio **anómalo** (p. ej., < 25% del valor fiscal o igual a 0) por municipio.

## Alcance y siguientes pasos
- En el **Ej3** confirmamos columnas reales y ajustamos el DDL.
- En el **Ej4** descargamos el CSV desde Internet y cargamos la DB con Python dentro de Docker.
- En el **Ej5** generamos un reporte con consultas (tendencias, top municipios, etc.).
