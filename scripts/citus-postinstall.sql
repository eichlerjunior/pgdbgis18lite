-- Instala/provisiona Citus 14.3-1 + PG-Strom 6.0 no cluster pgdb.
-- Requisito: shared_preload_libraries = 'citus,pg_strom' em postgresql.conf (já aplicado).
-- Rodar como postgres superuser:  psql -p 5433 -d postgres -f scripts/citus-postinstall.sql
CREATE EXTENSION IF NOT EXISTS postgis;      -- opcional (etapa PostGIS separada)
CREATE EXTENSION IF NOT EXISTS citus SCHEMA pg_catalog;
CREATE EXTENSION IF NOT EXISTS pg_strom;
-- Credencial de worker: Citus conecta a shards via TCP; senha do role postgres
-- deve existir (ver .pgpass de /var/lib/postgresql). Aplicar com:
--   ALTER ROLE postgres PASSWORD 'SENHA';
