import os
import sys
import pandas as pd
import psycopg2

def env(name, default=None, required=False):
  v = os.environ.get(name, default)
  if required and (v is None or v == ""):
    print(f"[ERROR] Falta variable de entorno: {name}", file=sys.stderr)
    sys.exit(1)
  return v

def get_conn():
  return psycopg2.connect(
    host=env("PGHOST", required=True),
    port=int(env("PGPORT", "5432")),
    dbname=env("POSTGRES_DB", required=True),
    user=env("POSTGRES_USER", required=True),
    password=env("POSTGRES_PASSWORD", required=True),
  )

def run_query(cur, sql):
  cur.execute(sql)
  cols = [d.name for d in cur.description]
  rows = cur.fetchall()
  return pd.DataFrame(rows, columns=cols)

def print_section(title, df, max_rows=None):
  print("\n" + "="*len(title))
  print(title)
  print("="*len(title))
  if df.empty:
    print("(sin resultados)")
  else:
    if max_rows:
      print(df.head(max_rows).to_string(index=False))
      if len(df) > max_rows:
        print(f"... ({len(df)-max_rows} filas más)")
    else:
      print(df.to_string(index=False))

def main():
  pd.set_option("display.max_columns", 50)
  pd.set_option("display.width", 160)

  with get_conn() as conn:
    cur = conn.cursor()

    # 1) Tendencia anual (conteo, promedio, mediana, p90)
    q1 = """
    SELECT
      EXTRACT(YEAR FROM sale_date)::int AS year,
      COUNT(*)                          AS sales,
      ROUND(AVG(sale_price))::bigint    AS avg_price,
      ROUND(PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY sale_price))::bigint AS median_price,
      ROUND(PERCENTILE_DISC(0.9) WITHIN GROUP (ORDER BY sale_price))::bigint AS p90_price
    FROM sales
    GROUP BY 1
    ORDER BY 1;
    """
    df1 = run_query(cur, q1)
    print_section("1) Tendencia anual de precios y volumen", df1)

    # 2) Top 10 municipios por precio promedio (con umbral mínimo de ventas)
    q2 = """
    SELECT
      m.name                               AS municipality,
      COUNT(*)                              AS sales,
      ROUND(AVG(sale_price))::bigint        AS avg_price,
      ROUND(PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY sale_price))::bigint AS median_price
    FROM sales s
    JOIN properties p ON p.property_id = s.property_id
    JOIN municipalities m ON m.municipality_id = p.municipality_id
    GROUP BY 1
    HAVING COUNT(*) >= 100
    ORDER BY avg_price DESC
    LIMIT 10;
    """
    df2 = run_query(cur, q2)
    print_section("2) Top 10 municipios por precio promedio (>=100 ventas)", df2)

    # 3) Años con mayor actividad (top 5 por cantidad de ventas)
    q3 = """
    SELECT
      EXTRACT(YEAR FROM sale_date)::int AS year,
      COUNT(*) AS sales
    FROM sales
    GROUP BY 1
    ORDER BY sales DESC
    LIMIT 5;
    """
    df3 = run_query(cur, q3)
    print_section("3) Años con mayor actividad (ventas)", df3)

    # 4) Relación de valuación: mediana de (sale_price / assessed_value) por municipio
    #    (solo donde hay valuación > 0). Útil para ver sobre/sub-valuación fiscal.
    q4 = """
    WITH base AS (
      SELECT
        m.name AS municipality,
        (s.sale_price / NULLIF(s.assessed_value, 0))::numeric AS ratio
      FROM sales s
      JOIN properties p ON p.property_id = s.property_id
      JOIN municipalities m ON m.municipality_id = p.municipality_id
      WHERE s.assessed_value IS NOT NULL AND s.assessed_value > 0
    )
    SELECT
      municipality,
      ROUND(PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY ratio), 2) AS median_ratio,
      COUNT(*) AS n
    FROM base
    GROUP BY 1
    HAVING COUNT(*) >= 50
    ORDER BY median_ratio DESC
    LIMIT 10;
    """
    df4 = run_query(cur, q4)
    print_section("4) Mediana de (precio/valuación) por municipio (>=50 registros)", df4)

    # 5) Outliers: ventas en el percentil 99+ del precio (top 20)
    q5 = """
    WITH pctl AS (
      SELECT PERCENTILE_DISC(0.99) WITHIN GROUP (ORDER BY sale_price) AS p99
      FROM sales
    )
    SELECT
      s.sale_date::date AS sale_date,
      m.name            AS municipality,
      p.address         AS address,
			s.sale_price      AS sale_price
    FROM sales s
    JOIN properties p ON p.property_id = s.property_id
    JOIN municipalities m ON m.municipality_id = p.municipality_id
    CROSS JOIN pctl
    WHERE s.sale_price >= pctl.p99
    ORDER BY s.sale_price DESC
    LIMIT 20;
    """
    df5 = run_query(cur, q5)
    print_section("5) Outliers (>= P99 del precio, top 20)", df5)

if __name__ == "__main__":
  main()
