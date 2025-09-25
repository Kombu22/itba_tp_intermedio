#!/usr/bin/env bash
set -euo pipefail

# rutas
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SQL_DIR="$ROOT_DIR/sql"
ENV_FILE="$ROOT_DIR/docker/.env"

# contenedor del Ej2
CONTAINER="itba-postgres-12"

# leer credenciales desde docker/.env si existe, si no usar defaults del ejemplo
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
DB_USER="${POSTGRES_USER:-itba}"
DB_NAME="${POSTGRES_DB:-real_estate}"

# check contenedor corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "Error: el contenedor '${CONTAINER}' no está corriendo."
  echo "Levantalo con: (cd docker && docker compose up -d)"
  exit 1
fi

# buscar y ejecutar todos los .sql (ordenados por nombre)
shopt -s nullglob
mapfile -t FILES < <(ls -1 "$SQL_DIR"/*.sql 2>/dev/null | sort)
if (( ${#FILES[@]} == 0 )); then
  echo "No se encontraron archivos .sql en $SQL_DIR"
  exit 1
fi

for f in "${FILES[@]}"; do
	echo ">> Ejecutando $(basename "$f")"
  docker exec -i "$CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -f - < "$f"
done

echo "DDL aplicado correctamente."
