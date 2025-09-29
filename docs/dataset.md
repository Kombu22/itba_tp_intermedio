# Dataset: Real Estate Sales (Connecticut) 2001–2023 (GL)

## Fuente
- Catálogo (histórico): https://catalog.data.gov/dataset/real-estate-sales-2001-2018
- Portal oficial (recurso vigente): data.ct.gov – “Real Estate Sales 2001–2023 (Grand List)”

## Descripción breve del dataset
Conjunto de datos de **ventas inmobiliarias** en el estado de Connecticut.  
Cada registro representa una operación de venta e incluye: **fecha de venta**, **precio de venta**, **dirección** y/o municipio/ZIP, **tipo de propiedad** (residencial, apartamento, comercial, industrial o terreno), y en muchos casos **valuación fiscal**.

**Notas de alcance**
- El dataset se publica por **año de Grand List (GL)**: va del **1 de octubre** al **30 de septiembre** del año siguiente.
- Algunas municipalidades pueden no reportar un año inmediatamente posterior a una revaluación.

## Preguntas de negocio (consultables en SQL)
1. **Tendencia anual de precios:** ¿Cómo evolucionó el **precio de venta** (media/mediana) por año GL?
2. **Comparativa por zona:** ¿Qué municipios presentan los **precios promedio** más altos y más bajos?
3. **Tipo de propiedad:** ¿Cómo varía el **precio de venta** según el **tipo de propiedad**?
4. **Distribución de precios:** ¿Cuál es la **distribución** (percentiles) por municipio y por año GL?
5. **Relación con atributos del inmueble:** Cuando hay información de superficies o año de construcción, ¿cómo se relacionan con el precio?
6. **Detección de outliers:** ¿Qué ventas muestran precios atípicos por municipio o en el total?

## Muestra usada para el TP
Por tamaño del dataset y reproducibilidad local, en el ETL del Ej4 se cargó una **muestra de 100.000 registros** (primeras filas del CSV).  
La base queda lista para las consultas del Ej5. Para cargar el dataset completo, ajustar el límite en `etl/main.py`.
