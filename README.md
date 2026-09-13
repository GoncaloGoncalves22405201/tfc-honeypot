# TFC — Deceção Adaptativa contra Atacantes Autónomos

Honeypot com LLM resistente a fingerprinting, com classificação do
adversário em três classes (bot / agente de IA / humano) e geração
automática de notificações de incidente ao abrigo do DL 125/2025.

Licenciatura em Engenharia Informática — DEISI, Universidade Lusófona
Ano letivo 2026/2027

## Estado

- [x] Passo 1 — medição da latência de um shell Linux real
- [ ] Passo 2 — honeypot básico (Cowrie + Ollama)
- [ ] Passo 3 — cache, sistema de ficheiros virtual, regulador de latência

## Passo 1 — resultados

960 medições, 32 comandos, 7 categorias, contra um Ubuntu 22.04 em contentor.

| métrica | ms |
|---------|------|
| mediana | 1.90 |
| média | 6.80 |
| p95 | 3.99 |
| máximo | 155.19 |

Latência por categoria (mediana):

| categoria | ms |
|-----------|------|
| erro | 1.31 |
| trivial | 1.50 |
| leitura_rapida | 1.75 |
| pesquisa | 1.99 |
| sistema | 2.14 |
| rede | 2.69 |
| processos | 3.28 |

### Achados

1. O orçamento temporal para uma resposta é de 1 a 4 ms. Um LLM de 7B
   demora 1000 a 3000 ms — três ordens de grandeza acima. É esta a
   dimensão do problema que o regulador de latência tem de resolver.

2. A distribuição é trimodal: builtins do bash (~0.7 ms), binários
   externos (1.3 a 4 ms) e `top -bn1` (~154 ms). O vale entre 0.8 e
   1.3 ms é quase vazio. A separação corresponde ao custo de fork/exec.

3. Consequência de desenho: o regulador não pode devolver tudo à
   mediana global. Tem de reproduzir a distribuição, incluindo a
   separação builtin/externo e a cauda longa dos comandos com espera
   intrínseca.

## Como reproduzir

Arrancar o sistema de referência:

    docker compose -f docker-compose.lab.yml up -d --build

Preparar o ambiente Python:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Medir e analisar:

    python scripts/medir_latencia.py --repeticoes 30
    python scripts/analisar_latencia.py

Resultados em `dados/` (fora do controlo de versões).

Parar:

    docker compose -f docker-compose.lab.yml down

## Estrutura

    docker-compose.lab.yml        ambiente de laboratório
    lab-ssh-ref/Dockerfile        sistema Linux de referência
    scripts/medir_latencia.py     medição via SSH interativo
    scripts/analisar_latencia.py  estatísticas e histogramas
    dados/                        resultados gerados

## Notas de método

A medição usa uma sessão SSH interativa (`invoke_shell`) e não
`exec_command`. Um canal novo por comando mediria também o custo de o
estabelecer, enviesando os tempos. Os comandos são executados em ordem
aleatória para evitar que efeitos de cache do sistema de ficheiros se
acumulem sempre nos mesmos.

As medições foram feitas em rede local. Um adversário real acede pela
internet, com 20 a 80 ms de latência de rede por cima — o que mascara
parte da diferença e deve ser incluído no modelo.
