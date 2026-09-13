#!/usr/bin/env python3
"""Analise das medicoes de latencia do sistema de referencia.

Produz as estatisticas por categoria e por comando, e os histogramas
que servem de alvo ao regulador de latencia do honeypot.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")          # sem interface grafica, funciona no WSL
import matplotlib.pyplot as plt
import pandas as pd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--entrada", default="dados/latencia_referencia.json")
    ap.add_argument("--saida", default="dados")
    a = ap.parse_args()

    caminho = Path(a.entrada)
    if not caminho.exists():
        raise SystemExit(f"Nao encontrei {caminho}. Corre primeiro medir_latencia.py")

    df = pd.DataFrame(json.loads(caminho.read_text(encoding="utf-8")))
    saida = Path(a.saida); saida.mkdir(parents=True, exist_ok=True)

    por_categoria = (df.groupby("categoria")["duracao_ms"]
        .agg(n="count", media="mean", mediana="median", desvio="std",
             p05=lambda s: s.quantile(0.05), p95=lambda s: s.quantile(0.95),
             maximo="max")
        .round(2).sort_values("mediana"))

    por_comando = (df.groupby("comando")["duracao_ms"]
        .agg(n="count", mediana="median", p95=lambda s: s.quantile(0.95))
        .round(2).sort_values("mediana"))

    print("\n=== Latencia por categoria (ms) ===")
    print(por_categoria.to_string())
    print("\n=== 12 comandos mais rapidos (candidatos a cache) ===")
    print(por_comando.head(12).to_string())
    print("\n=== 8 comandos mais lentos ===")
    print(por_comando.tail(8).to_string())

    por_categoria.to_csv(saida / "latencia_por_categoria.csv")
    por_comando.to_csv(saida / "latencia_por_comando.csv")

    categorias = sorted(df["categoria"].unique())
    n = len(categorias); linhas = (n + 2) // 3
    fig, eixos = plt.subplots(linhas, 3, figsize=(14, 3.4 * linhas))
    eixos = eixos.flatten()
    for eixo, cat in zip(eixos, categorias):
        s = df[df["categoria"] == cat]["duracao_ms"]
        eixo.hist(s, bins=30, color="#2f7fae", edgecolor="white", linewidth=0.4)
        eixo.axvline(s.median(), color="#c0392b", linestyle="--", linewidth=1.2,
                     label=f"mediana {s.median():.2f} ms")
        eixo.set_title(cat, fontsize=11)
        eixo.set_xlabel("ms"); eixo.set_ylabel("ocorrencias")
        eixo.legend(fontsize=8)
    for eixo in eixos[n:]:
        eixo.axis("off")
    fig.suptitle("Latencia de um shell Linux real, por categoria de comando", fontsize=13)
    fig.tight_layout()
    fig.savefig(saida / "histograma_latencia.png", dpi=150)

    fig2, e2 = plt.subplots(figsize=(9, 4.5))
    import numpy as np
    bins = np.logspace(np.log10(df["duracao_ms"].min()),
                       np.log10(df["duracao_ms"].max()), 60)
    e2.hist(df["duracao_ms"], bins=bins, color="#0d1b2a", edgecolor="white", linewidth=0.3)
    e2.set_xscale("log")
    e2.set_xlabel("latencia (ms, escala logaritmica)")
    e2.set_ylabel("ocorrencias")
    e2.set_title("Distribuicao global - sistema de referencia")
    fig2.tight_layout()
    fig2.savefig(saida / "histograma_global.png", dpi=150)

    print(f"\nGraficos em {saida}/histograma_latencia.png e histograma_global.png")

    limiar = por_comando["mediana"].median()
    rapidos = por_comando[por_comando["mediana"] < limiar]
    print(f"\n{len(rapidos)} comandos abaixo da mediana global ({limiar:.2f} ms).")
    print("Sao os candidatos naturais a resposta por cache deterministica.")


if __name__ == "__main__":
    main()
