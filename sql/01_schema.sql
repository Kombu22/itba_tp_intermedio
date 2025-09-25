BEGIN;

-- Municipios / ciudades
CREATE TABLE IF NOT EXISTS municipalities (
  municipality_id SERIAL PRIMARY KEY,
  name            TEXT UNIQUE NOT NULL
);

-- Propiedades
CREATE TABLE IF NOT EXISTS properties (
  property_id      BIGSERIAL PRIMARY KEY,
  parcel_id        TEXT UNIQUE,
  address          TEXT,
  zip_code         TEXT,
  municipality_id  INT REFERENCES municipalities(municipality_id),
  year_built       INT,
  building_sqft    INT,
  land_sqft        INT,
  property_type    TEXT
);

-- Ventas
CREATE TABLE IF NOT EXISTS sales (
  sale_id         BIGSERIAL PRIMARY KEY,
  property_id     BIGINT NOT NULL REFERENCES properties(property_id),
  sale_date       DATE NOT NULL,
  sale_price      NUMERIC(14,2) NOT NULL,
  assessed_value  NUMERIC(14,2),
  appraised_value NUMERIC(14,2),
  deed_book       TEXT,
  deed_page       TEXT
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_sales_date   ON sales (sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_price  ON sales (sale_price);
CREATE INDEX IF NOT EXISTS idx_prop_muni    ON properties (municipality_id);

COMMIT;
