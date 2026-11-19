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

## Dashboard de monitoramento

Em `scripts/dashboard/dash.py` há um painel em um único arquivo (sem dependências
externas) que lê o estado vivo da stack e serve uma página HTML escura com
atualização automática a cada 5 s:

- **PostgreSQL** (cluster pgdb): versão, uptime, conexões, bancos.
- **Extensões**: o que está de fato criado (citus, pg_strom, postgis…).
- **GPU / PG-Strom**: as 2x RTX 3060 (uso, memória, temperatura, potência).
- **ZFS**: datasets `media-pool/*` (usado, livre, compressão).
- **Citus**: workers ativos e shards.
- **Queries ativas** e estado do host.

```sh
# como usuário comum do hub (usa sudo NOPASSWD p/ ler o cluster):
python3 scripts/dashboard/dash.py --aspostgres --port 8080

# ou com usuário/senha via TCP:
python3 scripts/dashboard/dash.py --dsn postgres:SENHA@127.0.0.1:5433/postgres

# para servir na LAN (porta 80/443 liberada na ACL):
sudo python3 scripts/dashboard/dash.py --listen 0.0.0.0 --port 80
```

Abra `http://127.0.0.1:8080/` (o JSON cru fica em `/api`). É leitura apenas,
não modifica nada. O rodapé do painel insiste na regra do projeto: *um citus
abaixo do strom* — a única build que o cluster carrega.

## Licença

Cada subárvore conserva a licença do seu projeto de origem
(PostgreSQL License, PostGIS GPLv2, Citus AGPLv3, PG-Strom GPLv3).

---

*Espírito replicável, corpo privado. O código fala por si.*
