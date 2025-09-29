import os, io, re, sys
from datetime import datetime
import pandas as pd
import requests
import psycopg2
from psycopg2.extras import execute_values

# --- helpers de entorno ---
def env(name, default=None, required=False):
    """Lee variables de entorno. Si required=True y falta, aborta."""
    v = os.environ.get(name, default)
    if required and (v is None or v == ""):
        print(f"[ERROR] Missing env: {name}", file=sys.stderr)
        sys.exit(1)
    return v

# --- normalización de nombres de columnas ---
def normalize_cols(cols):
    """minúsculas, sin caracteres raros, separadas por _"""
    def norm(s):
        s = s.strip().lower()
        s = re.sub(r"[^\w\s]", "_", s)
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"_+", "_", s)
        return s.strip("_")
    return [norm(c) for c in cols]

# --- lectura del dataset por archivo o URL ---
def read_df():
    data_path = os.environ.get("DATA_PATH")
    data_url  = os.environ.get("DATA_URL")
    row_limit = 100000

    if data_path:
        df = pd.read_csv(
            data_path,
            low_memory=False,
            nrows=row_limit if row_limit > 0 else None  
        )
    elif data_url:
        r = requests.get(data_url, timeout=60)
        r.raise_for_status()
        df = pd.read_csv(
            io.BytesIO(r.content),
            low_memory=False,
            nrows=row_limit if row_limit > 0 else None  
        )
    else:
        print("[ERROR] provide DATA_PATH or DATA_URL", file=sys.stderr)
        sys.exit(1)

    df.columns = normalize_cols(df.columns)
    print(f"[INFO] columnas detectadas: {len(df.columns)}; filas leídas: {len(df)}")  
    return df

# --- escoger la mejor columna disponible entre varias opciones ---
def pick(df, names):
    for n in names:
        if n in df.columns:
            return df[n]
    return pd.Series([None]*len(df))

# --- parseos básicos ---
def to_number(s):
    if pd.isna(s): return None
    if isinstance(s, (int, float)): return float(s)
    s = str(s).strip().replace("$", "").replace(",", "")
    try: return float(s)
    except Exception: return None

def to_date(s):
    if pd.isna(s): return None
    try: return pd.to_datetime(s, errors="coerce").date()
    except Exception: return None

def main():
    # Conexión a Postgres (desde el contenedor ETL hacia el host)
    pg_host = env("PGHOST", required=True)         # usaremos host.docker.internal
    pg_port = int(env("PGPORT", "5432"))
    pg_db   = env("POSTGRES_DB", required=True)
    pg_user = env("POSTGRES_USER", required=True)
    pg_pwd  = env("POSTGRES_PASSWORD", required=True)

    print("[INFO] leyendo dataset...")
    df = read_df()

    # Mapea nombres típicos del dataset a columnas "canónicas"
    towns   = pick(df, ["town", "municipality", "city"])
    address = pick(df, ["address", "property_address", "site_address", "location"])
    sprice  = pick(df, ["sale_amount", "sales_price", "sale_price", "amount"])
    sdate   = pick(df, ["date_recorded", "sale_date", "date"])
    assess  = pick(df, ["assessed_value", "assessment", "assessed"])
    ptype   = pick(df, ["property_type", "residential_type", "type"])

    # Construye un DataFrame limpio y tipado
    clean = pd.DataFrame({
        "town": (towns.astype(str).str.strip().str.title() if towns is not None else None),
        "address": address.astype(str).str.strip(),
        "sale_price": sprice.map(to_number),
        "sale_date": sdate.map(to_date),
        "assessed_value": assess.map(to_number),
        "property_type": ptype.astype(str).str.strip()
    })

    # Filtrado básico: necesitamos fecha y precio + town/address
    before = len(clean)
    clean = clean.dropna(subset=["sale_price", "sale_date"])
    clean = clean[(clean["address"] != "") & (clean["town"] != "")]
    print(f"[INFO] filas totales: {before} -> a cargar: {len(clean)}")

    if len(clean) == 0:
        print("[WARN] no hay filas válidas.")
        return

    # Conexión psycopg2
    conn = psycopg2.connect(
        host=pg_host, port=pg_port, dbname=pg_db, user=pg_user, password=pg_pwd
    )
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # 1) MUNICIPALITIES (UPSERT por nombre)
        towns_unique = sorted({t for t in clean["town"].tolist() if t})
        execute_values(
            cur,
            "INSERT INTO municipalities(name) VALUES %s ON CONFLICT (name) DO NOTHING",
            [(t,) for t in towns_unique]
        )
        cur.execute(
            "SELECT municipality_id, name FROM municipalities WHERE name = ANY(%s)",
            (towns_unique,)
        )
        muni_map = {name: mid for (mid, name) in cur.fetchall()}

        # 2) PROPERTIES (dedupe por (municipio,address))
        prop_keys = list({(muni_map.get(t), a) for t, a in zip(clean["town"], clean["address"]) if muni_map.get(t) and a})
        existing = {}
        BATCH = 1000
        for i in range(0, len(prop_keys), BATCH):
            mids  = [k[0] for k in prop_keys[i:i+BATCH]]
            addrs = [k[1] for k in prop_keys[i:i+BATCH]]
            cur.execute(
                """
                SELECT property_id, municipality_id, address
                FROM properties
                WHERE municipality_id = ANY(%s) AND address = ANY(%s)
                """,
                (mids, addrs)
            )
            for pid, mid, addr in cur.fetchall():
                existing[(mid, addr)] = pid

        to_insert = [(addr, mid) for (mid, addr) in prop_keys if (mid, addr) not in existing]
        if to_insert:
            execute_values(
                cur,
                """
                INSERT INTO properties(address, municipality_id)
                VALUES %s
                RETURNING property_id, municipality_id, address
                """,
                to_insert,
                fetch=True
            )
            for pid, mid, addr in cur.fetchall():
                existing[(mid, addr)] = pid

        # 3) SALES
        sale_rows = []
        for _, row in clean.iterrows():
            mid = muni_map.get(row["town"])
            if not mid:
                continue
            addr = row["address"]
            pid = existing.get((mid, addr))
            if not pid:
                cur.execute(
                    "INSERT INTO properties(address, municipality_id) VALUES (%s, %s) RETURNING property_id",
                    (addr, mid)
                )
                pid = cur.fetchone()[0]
                existing[(mid, addr)] = pid

            sale_rows.append((
                int(pid),
                row["sale_date"],
                float(row["sale_price"]),
                None if pd.isna(row["assessed_value"]) else float(row["assessed_value"]),
                None  
            ))

        execute_values(
            cur,
            """
            INSERT INTO sales(property_id, sale_date, sale_price, assessed_value, deed_book)
            VALUES %s
            """,
            sale_rows
        )

        conn.commit()
        print("[OK] carga completada.")
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] {e}", file=sys.stderr)
        raise
    finally:
        cur.close(); conn.close()

if __name__ == "__main__":
    main()
