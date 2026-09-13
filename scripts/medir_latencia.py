#!/usr/bin/env python3
"""Medicao da latencia de um shell Linux real.

Abre uma sessao SSH interativa contra o sistema de referencia, executa
comandos em ordem aleatoria e mede o tempo entre o envio e a chegada da
resposta completa. O resultado e a distribuicao que o regulador de
latencia do honeypot tera de reproduzir.
"""
from __future__ import annotations
import argparse, json, random, statistics, time
from datetime import datetime, timezone
from pathlib import Path
import paramiko

COMANDOS = {
    "trivial":        ["pwd", "whoami", "id", "echo ola", "hostname", "date"],
    "leitura_rapida": ["ls", "ls -la", "ls /etc", "cat /etc/hostname",
                       "cat /etc/passwd", "cat /etc/os-release", "head -5 /etc/passwd"],
    "sistema":        ["uname -a", "uptime", "free -m", "df -h", "w"],
    "processos":      ["ps aux", "ps -ef", "top -bn1 | head -20"],
    "rede":           ["ip a", "ip route", "netstat -tuln", "ss -tuln"],
    "pesquisa":       ["find /home -type f", "find /etc -name '*.conf'",
                       "grep -r root /etc/passwd", "du -sh /home"],
    "erro":           ["comandoinexistente", "cat /nao/existe", "cd /root"],
}
MARCADOR = "___FIM___"


def abrir_shell(host, porta, utilizador, password):
    """Shell interativo, nao exec_command: e o que o atacante ve, e evita
    medir o custo de abrir um canal novo a cada comando."""
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, port=porta, username=utilizador, password=password,
              look_for_keys=False, allow_agent=False)
    canal = c.invoke_shell(width=200, height=50)
    canal.settimeout(30.0)
    time.sleep(1.0)
    while canal.recv_ready():
        canal.recv(65535)
    canal.send("export PS1='$ ' TERM=dumb\n")
    time.sleep(0.5)
    while canal.recv_ready():
        canal.recv(65535)
    return c, canal


def executar(canal, comando):
    """Devolve (duracao_ms, bytes). O marcador aparece duas vezes: no eco
    do comando e na saida do echo. So a segunda marca o fim real."""
    while canal.recv_ready():
        canal.recv(65535)
    inicio = time.perf_counter()
    canal.send(f"{comando}; echo {MARCADOR}\n")
    buffer, total = "", 0
    while buffer.count(MARCADOR) < 2:
        pedaco = canal.recv(65535)
        if not pedaco:
            break
        total += len(pedaco)
        buffer += pedaco.decode("utf-8", errors="replace")
    return (time.perf_counter() - inicio) * 1000, total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--porta", type=int, default=2222)
    ap.add_argument("--utilizador", default="referencia")
    ap.add_argument("--password", default="referencia")
    ap.add_argument("--repeticoes", type=int, default=20)
    ap.add_argument("--saida", default="dados/latencia_referencia.json")
    a = ap.parse_args()

    plano = []
    for cat, cmds in COMANDOS.items():
        for cmd in cmds:
            plano.extend([(cat, cmd)] * a.repeticoes)
    random.shuffle(plano)

    print(f"A ligar a {a.host}:{a.porta} ...")
    cli, canal = abrir_shell(a.host, a.porta, a.utilizador, a.password)
    print(f"Ligado. {len(plano)} medicoes.\n")

    medicoes = []
    try:
        for i, (cat, cmd) in enumerate(plano, 1):
            try:
                dur, n = executar(canal, cmd)
            except Exception as e:
                print(f"  ! {cmd}: {e}")
                continue
            medicoes.append({"comando": cmd, "categoria": cat,
                             "duracao_ms": round(dur, 3), "bytes_resposta": n,
                             "instante": datetime.now(timezone.utc).isoformat()})
            if i % 50 == 0 or i == len(plano):
                print(f"  {i}/{len(plano)}")
    finally:
        canal.close(); cli.close()

    p = Path(a.saida); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(medicoes, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nGuardado em {p}  ({len(medicoes)} medicoes)")

    d = sorted(m["duracao_ms"] for m in medicoes)
    if d:
        print(f"  mediana : {statistics.median(d):8.2f} ms")
        print(f"  media   : {statistics.mean(d):8.2f} ms")
        print(f"  p95     : {d[int(len(d)*0.95)]:8.2f} ms")
        print(f"  maximo  : {max(d):8.2f} ms")


if __name__ == "__main__":
    main()
