#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ETL_IMG="itba-etl"
RPT_IMG="itba-report"
CONTAINER="itba-postgres-12"
DATA_URL="https://data.ct.gov/api/views/5mzw-sjtu/rows.csv?accessType=DOWNLOAD"

echo "==> 1) Build imágenes (ETL y Reporte)"
docker build -t "$ETL_IMG" -f "$ROOT_DIR/etl/Dockerfile" "$ROOT_DIR"
docker build -t "$RPT_IMG" -f "$ROOT_DIR/reports/Dockerfile" "$ROOT_DIR"

echo "==> 2) Levantar Postgres (docker compose)"
pushd "$ROOT_DIR/docker" >/dev/null
cp -n .env.example .env || true
docker compose up -d
popd >/dev/null

# Cargar variables desde docker/.env (para POSTGRES_*, PG_PORT, etc.)
ENV_FILE="$ROOT_DIR/docker/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
PG_PORT="${PG_PORT:-5432}"

echo "==> 3) Esperar a que la DB esté lista"
for _ in {1..60}; do
  if docker exec "$CONTAINER" pg_isready -U "${POSTGRES_USER:-itba}" -p "$PG_PORT" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-itba}" "$CONTAINER" \
  psql -U "${POSTGRES_USER:-itba}" -d "${POSTGRES_DB:-real_estate}" -c "SELECT 1;" >/dev/null

echo "==> 4) DDL (creación de tablas)"
bash "$ROOT_DIR/scripts/run_ddl.sh"

echo "==> 5) ETL (carga por URL; muestra 100k en etl/main.py)"
docker run --rm --env-file "$ROOT_DIR/docker/.env" \
  -e PGHOST=host.docker.internal \
  -e DATA_URL="$DATA_URL" \
  "$ETL_IMG"

echo "==> 6) Reporte (5 consultas)"
docker run --rm --env-file "$ROOT_DIR/docker/.env" \
  -e PGHOST=host.docker.internal \
  "$RPT_IMG"

echo "==> Pipeline end-to-end COMPLETADO ✔"
