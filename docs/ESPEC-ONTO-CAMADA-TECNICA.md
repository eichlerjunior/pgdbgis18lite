# Camada `onto` — integração ontológica + geoespacial (ESPEC TÉCNICA)

Documento de desenho técnico da camada de integração de dados no cluster pgdb
(PostgreSQL 18 + PostGIS + Citus + PG-Strom, armazenamento na pool ZFS).

Escopo: **somente técnico**. O vocabulário de negócio vive noutro documento.
Aqui: tipos, schema, alinhamentos de coluna, índices e consultas-tipo.

---

## 1. Objetivo

Fazer o banco "entender" dados abertos de origens heterogêneas — RAIS (federal),
CNPJ (Receita), portais estaduais (SP/RS/PE/SC), malha IBGE — sem decorar nome de
coluna por fonte. Uma camada `onto` normaliza vocabulário e dá uma dimensão
geoespacial de primeira classe via PostGIS.

## 2. Schema alvo (no cluster pgdb, porta 5433)

```
onto.conceitos        -- classes (Entidade, Relação, Propriedade, Dimensão)
onto.conceito_hier     -- is-a entre conceitos (subclassificação)
onto.relacoes         -- relações binárias entre conceitos
onto.fontes           -- cada origem de dados espelhada/importada
onto.tabelas          -- tabela+coluna física por fonte (não-ontológica)
onto.mapas_colunas    -- coluna física -> (conceito, alinhamento, função)
onto.espacos          -- classes espaciais (geometria/geography de referência)
onto.municipios       -- malha IBGE municipal (geometry) + uf/ibge_id
onto.ceps             -- CEP -> geometria (ponto/área) via IBGE
onto.synonyms         -- normalização de termos (ex.: rezembro=dezembro)
```

## 3. DDL conceitual

### 3.1 Conceitos

```sql
CREATE SCHEMA IF NOT EXISTS onto;

CREATE TABLE onto.conceitos (
    id              int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            text NOT NULL UNIQUE,          -- kebab-case, ex: 'empresa'
    dominio         text CHECK (dominio IN ('entidade','relacao','propriedade','dimensao')),
    descricao       text,
    wiki                 text                       -- origem/semântica (BN/SKOS/CFC),
    criado_em       timestamptz DEFAULT now()
);

-- is-a
CREATE TABLE onto.conceito_hier (
    sub  int REFERENCES onto.conceitos(id),
    sup  int REFERENCES onto.conceitos(id),
    PRIMARY KEY (sub, sup)
);
```

### 3.2 Relações

```sql
CREATE TABLE onto.relacoes (
    id          int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome        text NOT NULL,          -- ex: 'participada_por', 'localizado_em'
    dominio     int REFERENCES onto.conceitos(id),
    contra_dom  int REFERENCES onto.conceitos(id),
    cardinalidade text,                 -- 1:1, 1:N, N:M
    UNIQUE (dominio, nome)
);
```

### 3.3 Fontes físicas (espelho local)

```sql
CREATE TABLE onto.fontes (
    id       int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cod      text UNIQUE,               -- 'rais_2023','cnpj_202611','rs_despesa'
    origem   text,                      -- 'receita-federal' | 'rais/MTE' | 'estadual:RS'
    uf       char(2),
    formato  text,                      -- 'csv' | 'csv.zip' | 'shp' | 'geojson' | 'json'
    caminho_espelho text,               -- /media/pool/media/<nome>-espelho/...
    extraido_em timestamptz DEFAULT now()
);

CREATE TABLE onto.tabelas (
    id        int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fonte_id  int REFERENCES onto.fontes(id),
    schema_t  text NOT NULL,            -- ex: 'trat', 'public', 'ontosig'
    tabela    text NOT NULL,
    coluna    text NOT NULL,
    UNIQUE (fonte_id, schema_t, tabela, coluna)
);
```

### 3.4 Mapa coluna -> significado (núcleo de "entendimento")

```sql
CREATE TABLE onto.mapas_colunas (
    tabela_id   int REFERENCES onto.tabelas(id),
    conceito_id int REFERENCES onto.conceitos(id),
    papel       text CHECK (papel IN ('identificador','atributo','medida','dimensao','geo')),
    funcao      text,                  -- função p/ transformar valor p/ canônico (ex: normalize_mes)
    confianca   real DEFAULT 0.5,      -- 0..1 confiança manual do mapeamento
    PRIMARY KEY (tabela_id, conceito_id)
);
```

### 3.5 Camada geo (PostGIS)

```sql
-- habilita PostGIS no banco de integração
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE onto.municipios (
    ibge_id  int PRIMARY KEY,
    uf       char(2) NOT NULL,
    nome     text NOT NULL,
    geog     geography(MultiPolygon, 4326) NOT NULL   -- malha IBGE
);
CREATE INDEX ON onto.municipios USING gist (geog);

CREATE TABLE onto.ceps (
    cep      text PRIMARY KEY,
    lat      float8, lon float8,
    geog     geography(Point, 4326)
);
CREATE INDEX ON onto.ceps USING gist (geog);
```

> Ponto técnico: usar `geography` (4326) para medições (ST_DWithin em km são
> corretas em geodesic), e `geometry` com SRID projetado por UF se o custo de
> ST_Intersects dominar. As malhas vêm do IBGE (geofw, shapefile/geojson).

## 4. Regras de alinhamento (exemplos já validados no projeto real)

Declaradas em `onto.synonyms` + função de normalização:

| Fonte       | Coluna física                 | Conceito            | Alinhamento                 |
|-------------|-------------------------------|---------------------|-----------------------------|
| RAIS        | `vl_rem_dezembro_nom`          | remuneração.dezembro | função fallback nominal      |
| RAIS        | `vl_rem_dezembro_sm`           | remuneração.dezembro | função fallback SM           |
| RAIS        | `vl_remun_rezembro_sm`         | remuneração.dezembro | synonym `rezembro`->`dezembro` |
| RAIS        | `cbo_94_ocupacao` / `cbo_95_ocupacao` | cbo_ocupacao | equivalência 94==95, canônico 95 |
| RAIS        | `uf` + `municipio`             | dimensao:geo         | resolve geog via `onto.municipios` |
| CNPJ        | `uf` + `municipio` + `cep`     | dimensao:geo         | cep -> ponto, municipio -> polígono |
| CNPJ        | `cnae_fiscal`                  | cnae (atividade)     | hierarquia CNAE pelos 2/4/7 dígitos |
| Estadual RS | `municipio` (texto)            | dimensao:geo         | topônimo -> via `onto.municipios` |

Função de normalização de mês (idempotente):

```sql
CREATE OR REPLACE FUNCTION onto.normalize_mes(t text) RETURNS text AS $$
  SELECT CASE
    WHEN t ILIKE '%dezembro%' OR t ILIKE '%rezembro%' THEN 'dezembro'
    WHEN t ILIKE '%janeiro%'  THEN 'janeiro'  WHEN t ILIKE '%fevereiro%' THEN 'fevereiro'
    WHEN t ILIKE '%marco%'    THEN 'marco'    WHEN t ILIKE '%abril%'    THEN 'abril'
    WHEN t ILIKE '%maio%'     THEN 'maio'     WHEN t ILIKE '%junho%'    THEN 'junho'
    WHEN t ILIKE '%julho%'    THEN 'julho'    WHEN t ILIKE '%agosto%'   THEN 'agosto'
    WHEN t ILIKE '%setembro%' THEN 'setembro' WHEN t ILIKE '%outubro%'  THEN 'outubro'
    WHEN t ILIKE '%novembro%' THEN 'novembro' ELSE t END;
$$ LANGUAGE sql IMMUTABLE;
```

## 5. Consultas-tipo (prova de conceito lógica, não otimizada)

### 5.1 Cruzar 2 fontes por Município (sem lat/lon, via PostGIS)

```sql
-- municípios do RS onde há ESTABELECIMENTO ativo (CNPJ) E vínculo RAIS 2023,
-- ordenado pelo nº de estabelecimentos dentro de 50km da capital
WITH base AS (
  SELECT e.ibge_id, e.nome, e.uf
  FROM onto.municipios e WHERE e.uf = 'RS'
)
SELECT b.uf, b.nome,
       count(distinct cnpj.cnpj)       AS estabelecimentos,
       count(distinct rais.pis)        AS vinculos_rais
FROM base b
LEFT JOIN cnpj.estabelecimentos cnpj
  ON onto.ponto_municipio(cnpj) = b.ibge_id
LEFT JOIN rais.vinculo_2023 rais
  ON onto.ponto_municipio(rais) = b.ibge_id
GROUP BY 1,2
ORDER BY estabelecimentos DESC;
```

### 5.2 Banda de distância (PostGIS geography)

```sql
-- PAIRES de municípios do RS a menos de 50km, só os de fronteira (uf≠RS na borda)
SELECT m1.nome, m2.nome, ST_Distance(m1.geog, m2.geog)/1000.0 AS km
FROM onto.municipios m1, onto.municipios m2
WHERE m1.uf='RS' AND m2.uf <> 'RS'
  AND ST_DWithin(m1.geog, m2.geog, 50000);
```

### 5.3 Hierarquia CNAE is-a

```sql
SELECT id.level1, nm1.descricao AS secao,
       count(*) FILTER (WHERE c.nao_ativo) AS ativos
FROM cnpj.estabelecimentos c
JOIN onto.cnae nm1 ON onto.cnae_secao(c.cnae_fiscal) = nm1.cod
GROUP BY 1,2;
```

## 6. Estratégia de carga reconendada (idempotente)

1. Criar schema/tabelas `onto` (DDL acima) no cluster pgdb — uma vez.
2. Carregar malha IBGE (`ST_GeomFromGeoJSON` / `shp2pgsql`) e CEPs em
   `onto.municipios` / `onto.ceps` — incremental, upsert por `ibge_id`/`cep`.
3. Importar cada fonte num schema próprio (`rais`, `cnpj`), carga via `COPY`
   com `set -euo pipefail` e `.pgpass` (nunca senha no Git).
4. Alimentar `onto.mapas_colunas` — manual, revisado pelo operador (fato),
   não inferido por padrão (hipótese).
5. Views/consultas de integração por cima.

## 7. Restrições técnicas (lições já registradas)

- **Idempotência e retomada** antes de paralelismo (espelho correto primeiro).
- **Origem COBOL/fita**: header/footer, posição e PIC importam mais que o nome CSV
  moderno. Não assumir nayra de coluna. `vl_remun_rezembro_sm` é typo VERDADEIRO,
  não novo fato — synonym faz.
- **Nunca `QUOTE ''`** no COPY (delimitador de um byte). Usar COPY sem quote vazio.
- **`set -euo pipefail`** em pipeline de carga (senão grava parcial silencioso).
- **Autenticação Postgres** via `~/.pgpass` / `PGPASSWORD`, nunca senha no repo.
- **Um Citus abaixo do PG-Strom** (regra do projeto; uma única build carregada).
- **ANALYZE após carga grande**; table UNLOGGED para carga, depois SET LOGGED.
- **Índices GiST sobre colunas `geography`** exigem PostGIS (e EXTENSION primeira).

## 8. Próximo passo técnico mínimo

Fechar o fato de cada fonte no banco (ex. `SELECT count(*) FROM rais.vinculo_2023`)
ANTES de usar a camada `onto` em produção. Camada de integração só sobre fato
confirmado — a mesma disciplina "primeiro fato, depois ação" do RAIS.

---

*Espírito replicável, corpo privado. O código fala por si.*
