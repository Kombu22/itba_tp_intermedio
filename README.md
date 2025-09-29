# itba_tp_intermedio

Trabajo práctico intermedio – Diplomatura **Cloud Data Engineering** (ITBA).

## Descripción
Repo con los ejercicios **Ej1–Ej4** usando **PostgreSQL 12.7** en Docker y un **ETL en Python** (también en Docker) para cargar el dataset **Real Estate Sales (Connecticut) 2001–2023 (GL)**.  
Para reproducibilidad y tiempos locales, el ETL carga una **muestra de 100.000 filas** (primeras filas del CSV). La base queda lista para consultas del Ej5.

---

## Requisitos
- Docker Desktop (incluye Docker Compose)
- Git
- (Windows) PowerShell o Git Bash

---

## Estructura del repo
docker/ # compose + .env.example (Postgres 12.7)
scripts/ # run_ddl.sh (aplica DDL)
sql/ # 01_schema.sql (tablas/PK/FK)
etl/ # Dockerfile + main.py + requirements (ETL en Python)
docs/ # dataset.md (Ej1: dataset + preguntas)
data/ # (local) CSV para el ETL — NO se versiona

> No subir datos crudos al repo ni a la imagen:
> - En **.gitignore**: `data/*.csv`
> - En **.dockerignore** (en la raíz): incluir `data/` para que el build no “hornee” CSVs en la imagen.

**Ejemplo de `.dockerignore`:**

No enviar datos crudos al build

data/

Otras exclusiones

.git
**/pycache/
**/*.pyc
node_modules
docker/pgdata


---

## Guía rápida (Ej1–Ej4)

### Ej1 — Dataset y preguntas
Ver `docs/dataset.md` (Real Estate Sales – Connecticut 2001–2023 GL).

---

### Ej2 — Base de datos (Docker Compose)
1) Crear `.env`:
en bash =>
cd docker
cp .env.example .env    # (opcional) ajustar PG_PORT/credenciales

2) Levantar Postgres:

docker compose up -d
docker compose ps

3.Probar conexión:

docker exec -it itba-postgres-12 psql -U itba -d real_estate -c "SELECT 1;"

## Ej3 — DDL (creación de tablas)

Desde la raíz del repo:

chmod +x scripts/run_ddl.sh
./scripts/run_ddl.sh

Verificar:

docker exec -it itba-postgres-12 psql -U itba -d real_estate -c "\dt"

## Ej4 — ETL (carga de datos)

El ETL carga una muestra de 100.000 filas.
La imagen no contiene datos crudos: el CSV se monta por volumen o se descarga en runtime.

0) Build de la imagen del ETL

docker build -t itba-etl -f etl/Dockerfile .


1) Git Bash — Descargar CSV y cargar (recomendado)
 
mkdir -p data
curl -L "https://data.ct.gov/api/views/5mzw-sjtu/rows.csv?accessType=DOWNLOAD" -o data/real_estate_sales.csv

2) Ejecutar ETL (monta el CSV; la imagen no lleva datos)
export MSYS_NO_PATHCONV=1
docker run --rm --env-file docker/.env \
  -e PGHOST=host.docker.internal \
  -e DATA_PATH=/data/real_estate_sales.csv \
  -v "$PWD/data:/data:ro" \
  itba-etl

### (Alternativa) PowerShell — Cargar descargando en runtime (sin archivo local)

docker run --rm --env-file docker/.env `
  -e PGHOST=host.docker.internal `
  -e DATA_URL="https://data.ct.gov/api/views/5mzw-sjtu/rows.csv?accessType=DOWNLOAD" `
  itba-etl

3) Verificación de la carga

docker exec -it itba-postgres-12 psql -U itba -d real_estate -c \
"SELECT
 (SELECT count(*) FROM sales)          AS sales,
 (SELECT count(*) FROM properties)     AS properties,
 (SELECT count(*) FROM municipalities) AS municipalities;"


### Reset rápido (si querés recargar la muestra)

docker exec -it itba-postgres-12 psql -U itba -d real_estate \
  -c "TRUNCATE sales, properties, municipalities RESTART IDENTITY CASCADE;"


### Prueba de consigna (la imagen no lleva datos)

docker run --rm itba-etl ls -l /data  # -> No such file or directory