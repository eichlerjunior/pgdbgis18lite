# pgdbgis18lite

Um fork/montagem do PostgreSQL que junta, em fonte original e compilável, as quatro camadas que um banco precisa para não se limitar:

| Camada    | O que é                                  | Dimensão que abre            |
|-----------|------------------------------------------|------------------------------|
| `postgresql`    | PostgreSQL 18 core                 | o banco relacional em si |
| `postgis-3.5.2` | PostGIS 3.5                        | dados espaciais / geográficos |
| `citus-14.3.0`  | Citus 14.3                          | escala horizontal + colunar |
| `pgstrom-6.1`   | PG-Strom 6.1 / Arrow + GPU          | computação acelerada em GPU |

## O que foi feito

Não é um wrapper: é a **reunião em uma só árvore** das fontes que, juntas, fazem um
único banco capaz de suportar mais limites e mais dimensões do que o relacional
puro. Cada pasta é código original, compilável, sem forks intermediários —
"fontes oficiais: PG-Strom 6.1 + Citus 14.3.0 (compilados local, sem forks)".

## A tese

> Um banco não nasce grande — nasce na dimensão certa para o que carrega.

- **PostGIS** abre a dimensão espacial.
- **Citus** abre a dimensão da escala (mais dados do que um nó cabe).
- **PG-Strom** abre a dimensão da computação (processa na GPU, não na CPU).
- **ZFS** (fora desta árvore) dá o chão persistente por baixo.

## Build / uso

Estrutura de diretórios para compilar as extensões contra o PostgreSQL 18:

```
postgresql/   -> fonte do servidor PG18
postgis-3.5.2/ -> ./configure --with-pgconfig=postgresql/pg_config ...
citus-14.3.0/  -> make && make install (PG >= 18)
pgstrom-6.1/   -> make PG_CONFIG=postgresql/pg_config
```

Cada extensão segue o fluxo de build padrão do upstream.

## Licença

Cada subárvore conserva a licença do seu projeto de origem
(PostgreSQL License, PostGIS GPLv2, Citus AGPLv3, PG-Strom GPLv3).

---

*Espírito replicável, corpo privado. O código fala por si.*
