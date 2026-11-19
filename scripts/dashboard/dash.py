#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dash.py — Dashboard da stack pgdbgis18lite (PG18 + PostGIS + Citus + PG-Strom + ZFS).

Um único arquivo, sem dependências externas (stdlib). Coleta o estado vivo do
cluster pgdb (5433), das 2x RTX 3060 (nvidia-smi), do pool ZFS (zpool/zfs) e
serve uma página HTML escura com atualização automática via /api (JSON).

Princípio do projeto respeitado: mostra as camadas por baixo (ZFS -> Postgres ->
PostGIS/Citus -> PG-Strom/GPU). Por padrão o dashboard espera UM citus abaixo
do PG-Strom (a única build que o cluster carrega).

Uso:
  python3 dash.py [--port 8080] [--listen 127.0.0.1] [--pgport 5433]
                  [--aspostgres] [--nosudo] [--dsn USER@HOST:PORT/DB]

  --aspostgres   roda os SELECTs como role postgres via 'sudo -n -u postgres'
                 (configuração NOPASSWD). Padrão quando o usuário é root/ia-master.
  --nosudo       não usa sudo; conecta como o usuário corrente via socket unix.
  --dsn          alternativa completa, ex.: 'postgres:secret@127.0.0.1:5433/postgres'
                 (senha também pode vir da env PGPASSWORD).
Defaults sensatos para o hub IA-MASTER; nada é modificado — apenas leitura.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE_TITLE = "pgdbgis18lite · dashboard"
REFRESH_MS = 5000


def run(cmd, timeout=15):
    """roda um comando, devolve (ok, stdout)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout or "").strip()
        return (p.returncode == 0, out)
    except FileNotFoundError:
        return (False, "cmd not found")
    except subprocess.TimeoutExpired:
        return (False, "timeout")


class Pg:
    def __init__(self, args):
        self.args = args
        base = ["psql", "-qX", "-tA", "-p", str(args.pgport), "-d", "postgres"]
        if args.dsn:
            # --dsn user[:pass]@host:port/db
            m = re.match(r"^([^:@/]+)(?::([^@]*))?@([^:/]+):(\d+)/(\w+)$", args.dsn)
            if not m:
                raise SystemExit(f"dsn inválido: {args.dsn}")
            u, pw, h, pno, db = m.groups()
            cmd = ["psql", "-qX", "-tA", "-p", pno, "-h", h, "-U", u, "-d", db]
            self.cmd = cmd
            if pw and "PGPASSWORD" not in os.environ:
                self.env = dict(os.environ, PGPASSWORD=pw)
            else:
                self.env = os.environ
        elif args.aspostgres and os.getuid() != 0 and not args.nosudo:
            self.cmd = ["sudo", "-n", "-u", "postgres"] + base
            self.env = os.environ
        elif getattr(os, "getuid", lambda: 1)() == 0 and not args.nosudo:
            self.cmd = base
            self.env = dict(os.environ, PGUSER="postgres")
        else:
            self.cmd = base
            self.env = os.environ

    def rows(self, sql):
        ok, out = run_pg2(self.cmd, sql, self.env)
        return [line for line in out.splitlines() if line] if ok else ["ERR:" + s for s in out.splitlines()]


def run_pg2(cmd, sql, env):
    try:
        p = subprocess.run(cmd + ["-c", sql], capture_output=True, text=True, timeout=20, env=env)
        return (p.returncode == 0, (p.stdout or "").strip())
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return (False, str(e))


def pg_field(rows, sep="|", idx=0):
    """primeiro campo da primeira linha de um resultado psql."""
    if not rows:
        return None
    return rows[0].split(sep)[idx] if sep in rows[0] else rows[0]


def collect_db(pg):
    d = {}
    d["server_version"] = pg_field(pg.rows("show server_version;"))
    d["uptime"] = pg_field(pg.rows("select pg_postmaster_start_time();"), "|", 0)
    d["extensions"] = [r.split("|") for r in pg.rows(
        "select extname, extversion from pg_extension order by 1;")]
    d["citus_workers"] = pg.rows("select node_name||':'||node_port from citus_get_active_worker_nodes();")
    d["citus_shards"] = pg_field(pg.rows(
        "select count(distinct shardid) from pg_dist_shard;")) or "0"
    d["databases"] = pg.rows(
        "select datname||'|'||pg_size_pretty(pg_database_size(datname)) from pg_database "
        "where datistemplate=false order by 1;")
    d["long_queries"] = pg.rows(
        "select pid||'|'||coalesce(query,'') from pg_stat_activity "
        "where state='active' and pid<>pg_backend_pid() order by now()-query_start desc limit 6;")
    d["n_conns"] = pg_field(pg.rows("select count(*) from pg_stat_activity;"))
    return d


def collect_gpu():
    # nvidia-smi: util(%), mem_used/MiB, mem_total/MiB, temp(C), pwr(W)
    cmd = ["nvidia-smi", "--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw",
           "--format=csv,noheader,nounits"]
    ok, out = run(cmd)
    gpus = []
    if ok:
        for line in out.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) >= 7:
                gpus.append({
                    "index": p[0], "name": p[1], "util": int(float(p[2])),
                    "mem_used": float(p[3]), "mem_total": float(p[4]),
                    "temp": p[5], "power": p[6]})
    return gpus


def collect_zfs():
    z = {}
    ok, out = run(["zpool", "status", "-P"])
    if ok:
        # estado geral + capacidades totals são lidas via zfs list abaixo
        z["raw"] = out
    z["pools"] = []
    ok, out = run(["zfs", "list", "-H", "-o", "name,used,avail,refer,compressratio,mountpoint"])
    if ok:
        for line in out.splitlines():
            f = line.split("\t")
            if len(f) >= 6:
                z["pools"].append({"name": f[0], "used": f[1], "avail": f[2],
                                   "refer": f[3], "ratio": f[4], "mount": f[5]})
    return z


def collect_host():
    h = {}
    for name, cmd in [("cpu", "vmstat 1 1"), ("mem", "free -m")]:
        ok, out = run(["sh", "-c", cmd])
        h[name] = out if ok else ""
    return h


def collect(args, pg):
    data = {"generated_ts": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "generated_epoch": int(time.time())}
    data["db"] = collect_db(pg)
    data["gpu"] = collect_gpu()
    data["zfs"] = collect_zfs()
    data["host"] = collect_host()
    return data


def build_handler(args, pg, rendered):
    class H(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def _send(self, code, body, ctype):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/" or self.path == "/index.html":
                self._send(200, rendered.encode(), "text/html")
            elif self.path == "/api":
                try:
                    data = json.dumps(collect(args, pg)).encode()
                    self._send(200, data, "application/json")
                except Exception as e:  # nunca deixar o painel morrer
                    self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
            else:
                self._send(404, b"not found", "text/plain")

    return H


PAGE_HTML = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;font-family:ui-monospace,Menlo,Consolas,monospace;background:#0b0f14;color:#d6e2f0}
header{padding:14px 22px;border-bottom:1px solid #1e2a3a;display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px}
header h1{margin:0;font-size:18px;color:#7ee0ff;letter-spacing:.5px}
header .layer{font-size:11px;color:#5d7d99}
header .ts{font-size:11px;color:#8aa0b8}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px;padding:16px 22px}
.panel{background:#11161d;border:1px solid #1e2a3a;border-radius:8px;padding:12px 14px}
.panel h2{margin:0 0 10px;font-size:12px;letter-spacing:1px;color:#9fc3e0;text-transform:uppercase;border-bottom:1px solid #1e2a3a;padding-bottom:6px}
.kv{display:grid;grid-template-columns:auto 1fr;gap:3px 12px;font-size:12px}
.kv dt{color:#5d7d99}
.kv dd{margin:0;color:#e6f0fa}
.ext{margin:2px 0;font-size:12px}.ext b{color:#9fe0a0}
.gpu-card{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #16202c;font-size:12px}
.gpu-card:last-child{border:0}
.gpu-card .n{color:#9fc3e0}
.bar{height:6px;background:#16202c;border-radius:3px;margin-top:3px;overflow:hidden}
.bar i{display:block;height:100%;background:linear-gradient(90deg,#22c55e,#7ee0ff);}
.warn{color:#fecaca}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{text-align:left;padding:4px 6px;border-bottom:1px solid #16202c}
th{color:#5d7d99;font-weight:600}
.qmono{font-family:ui-monospace,monospace;font-size:11px;color:#c9d6e8;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
footer{font-size:11px;color:#5d7d99;padding:10px 22px;border-top:1px solid #1e2a3a}
.err{color:#fecaca;font-size:12px}
</style></head><body>
<header>
  <h1>__TITLE__</h1>
  <div class="layer">ZFS &#8594; PostgreSQL &#8594; PostGIS · Citus &#8594; PG-Strom/GPU · <span id="one">um citus abaixo do strom</span></div>
  <div class="ts" id="ts">carregando…</div>
</header>
<main>
  <section class="panel"><h2>PostgreSQL · cluster pgdb</h2>
    <dl class="kv"><dt>versão</dt><dd id="ver">…</dd><dt>desde</dt><dd id="up">…</dd><dt>conns ativas</dt><dd id="nconn">…</dd></dl>
  </section>
  <section class="panel"><h2>Extensões</h2><div id="ext"></div></section>
  <section class="panel"><h2>GPU · PG-Strom</h2><div id="gpu">sem nvidia-smi</div></section>
  <section class="panel"><h2>ZFS · media-pool</h2><div id="zfs"></div></section>
  <section class="panel"><h2>Citus</h2><dl class="kv"><dt>workers</dt><dd id="cw">…</dd><dt>shards</dt><dd id="cs">…</dd></dl></section>
  <section class="panel"><h2>Bancos</h2><div id="dbs"></div></section>
  <section class="panel"><h2>Queries ativas</h2><table><thead><tr><th>pid</th><th>query</th></tr></thead><tbody id="qact"></tbody></table></section>
  <section class="panel"><h2>Host</h2><pre id="host" style="font-size:11px;color:#8aa0b8;margin:0"></pre></section>
</main>
<footer>leitura apenas · <a href="/api" style="color:#7ee0ff">/api</a> · atualiza a cada 5s · hora: <span id="cts"></span></footer>
<script>
const FMT = n => (typeof n==='number' ? n.toLocaleString('pt-BR') : n);
function gpuid(g){ return `GPU ${g.index} · ${g.name}<div class="bar"><i style="width:${g.util}%"></i></div>util ${g.util}% · mem ${g.mem_used}/${g.mem_total} GiB · ${g.temp}°C · ${g.power}W`; }
$id=id=>document.getElementById(id);
const MISS=['server_version','extensions'];
async function load(){
  try{
    const r=await fetch('/api'); const d=await r.json();
    const db=d.db||{}, z=d.zfs||{}, g=d.gpu||[];
    $id('ts').textContent='atualizado '+d.generated_ts;
    $id('cts').textContent=d.generated_ts;
    $id('ver').textContent=db.server_version||'—'; $id('up').textContent=db.uptime||'—';
    $id('nconn').textContent=FMT(db.n_conns)||'—';
    $id('ext').innerHTML=(db.extensions||[]).map(e=>`<div class="ext"><b>${e[0]}</b> v${e[1]}</div>`).join('')||'<div class="err">nenhuma</div>';
    $id('cw').textContent=(db.citus_workers&&db.citus_workers.length?db.citus_workers.map(w=>w.replace(/ERR:.*/,'!'+w)).join(', '):'0 ativos')+(db.citus_workers&&db.citus_workers.length? '':' <span class="warn">(sem worker configurado)</span>');
    $id('cs').textContent=db.citus_shards;
    $id('gpu').innerHTML=g.length?g.map(x=>`<div class="gpu-card"><span class="n">GPU ${x.index}</span>${x.name}</div><div class="bar"><i style="width:${x.util}%"></i></div><div>util ${x.util}% · mem ${(x.mem_used/1024).toFixed(1)}/${(x.mem_total/1024).toFixed(1)} GiB · ${x.temp}°C · ${x.power}W</div>`).join(''):'sem nvidia-smi';
    $id('zfs').innerHTML=(z.pools||[]).map(p=>`<div class="kv"><dt>${p.name}</dt><dd>${p.used} usados · ${p.avail} livres · ${p.ratio}</dd></div>`).join('')||'—';
    $id('dbs').innerHTML=(db.databases||[]).map(x=>{const[f,s]=x.split('|');return `<div class="kv"><dt>${f}</dt><dd>${s}</dd></div>`}).join('')||'—';
    $id('qact').innerHTML=(db.long_queries||[]).map(q=>{const[pid,...rest]=q.split('|');return `<tr><td>${pid||'?'}</td><td class="qmono" title="${(rest.join('|')||'').replace(/"/g,'&quot;')}">${(rest.join('|')||'…').slice(0,140)}</td></tr>`}).join('')||'<tr><td colspan=2>—</td></tr>';
    $id('host').textContent=(d.host&&(d.host.cpu+'\\n'+d.host.mem))||'';
  }catch(e){ $id('ts').textContent='erro: '+e.message; }
}
setInterval(load, __REFRESH__); load();
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser(description="dashboard pgdbgis18lite")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--listen", default="127.0.0.1")
    ap.add_argument("--pgport", type=int, default=5433)
    ap.add_argument("--aspostgres", action="store_true",
                    help="usar 'sudo -n -u postgres' para ler o cluster (NOPASSWD)")
    ap.add_argument("--nosudo", action="store_true", help="conectar como usuário corrente")
    ap.add_argument("--dsn", default=os.environ.get("POSTGRES_DSN", ""),
                    help="user[:pass]@host:port/db")
    a = ap.parse_args()

    # quando rodamos como usuário comum do hub, o padrão é virar postgres via sudo
    if not a.dsn and not a.nosudo and getattr(os, "getuid", lambda: 1)() != 0 and not a.aspostgres:
        a.aspostgres = True

    try:
        pg = Pg(a)
    except SystemExit as e:
        print(e); sys.exit(1)

    # sanity check: página HTML válida + um SELECT de preflight
    ok, out = run(pg.cmd + ["-c", "select version();"])
    if not ok:
        print("⚠ não consegui ler o cluster. Use --aspostgres / --dsn:")
        print("  python3 dash.py --aspostgres")
        print("  python3 dash.py --dsn postgres:SENHA@127.0.0.1:5433/postgres")
        sys.exit(1)

    html = (PAGE_HTML.replace("__TITLE__", PAGE_TITLE)
                     .replace("__REFRESH__", str(REFRESH_MS)))
    srv = ThreadingHTTPServer((a.listen, a.port), build_handler(a, pg, html))
    print(f"dashboard em  http://{a.listen}:{a.port}  (cluster PG {a.pgport}, um citus abaixo do strom)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nparou.")


if __name__ == "__main__":
    main()
