# pgdbgis18lite — NOSSA VERSÃO

## Escopo (decidido 19/11/2026)
Distribuição própria de PostgreSQL 18 com extensões, compilada dos fontes
oficiais (sem forks). Stack:

| Componente | Versão | Status |
|------------|--------|--------|
| ZFS (pool)  | media-pool 8,03 TiB | ✅ pronta |
| PostgreSQL  | 18.7 (fonte oficial no repo postgresql/) | ✅ fonte + base PGDG instalada |
| PostGIS     | 3.5.2 (fonte no repo postgis-3.5.2/) | ✅ fonte presente |
| PG-Strom    | — (fonte oficial a baixar) | ⏳ adicionar |
| Citus Data  | — (fonte oficial a baixar) | ⏳ adicionar |

## Características-chave
- Geoespacial (PostGIS)
- Aceleração GPU (PG-Strom, 2x RTX 3060 / CUDA 13.5 / driver 620.70.06)
- Distribuído (Citus)
- Dados na pool ZFS: /media/pool/media

## Regra do projeto
- Sempre código-fonte local (nunca só pacote binário)
- Compilar dos fontes oficiais da origem, sem forks
- Repositório base: eichlerjunior/pgdbgis18lite

## PRINCÍPIO ARQUITETURAL (decidido 19/11/2026)
**Padronize as camadas de SOFTWARE, não as de tecnologia volátil.**
- Camadas voláteis (mudam com a tecnologia, NÃO padronizam): CUDA/GPU, PG-Strom,
  PG-Strom, rede/P2P (CUDA hoje, mas pode virar ROCm/SYCL amanhã).
- Camadas de software estáveis (ESTAS são o padrão, valem em qualquer hardware):
  ZFS (pool, recordsize=8k, lz4, datasets dados/WAL) e PostgreSQL (config,
  modelo de dados, replicação lógica).
- Consequência: a base do projeto = ZFS + Postgres bem configurados e idênticos
  em qualquer máquina; as camadas GPU/P2P ficam plugáveis ACIMA, sem travar o
  padrão. O que puder evoluir (CUDA→outro backend) não exige redesenho da base.

## Estado por etapa (uma por vez)
- [x] Repositório PGDG configurado (trixie-pgdg + deb-src)
- [x] PostgreSQL 18.7 PGDG instalado (base) + headers dev
- [x] Fonte PG 18.7 no repo
- [x] PG-Strom 6.1: fonte oficial baixado, compilado (CUDA 13.5 + Arrow 25, c++20) e instalado (extensao v6.0)
- [ ] Citus: baixar fonte oficial, compilar contra headers PGDG
- [x] Cluster 'pgdb' validado na pool ZFS: PGDATA em media-pool/media/pgdata
      (recordsize=8k, lz4, primarycache=all), WAL em media-pool/media/pgwal
      (primarycache=metadata), porta 5433, PostgreSQL 18.7 respondendo

## Cluster padrão na pool (camada de software)
- Cluster: `18 pgdb`, porta 5433, dono postgres
- PGDATA = /media/pool/media/pgdata  |  WAL = /media/pool/media/pgwal
- Criado: `pg_createcluster 18 pgdb -d .../pgdata -- --waldir=.../pgwal
  --auth-local=peer --auth-host=scram-sha-256`
- Receita ZFS: pgdata(8k,lz4,cache=all,atime=off) + pgwal(8k,lz4,cache=metadata)
- Validação: PostgreSQL 18.7 responde na 5433; WAL gravando no dataset pgwal