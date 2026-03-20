"""
avaliador_paralelo.py
=====================
Processamento paralelo de arquivos de log utilizando o padrão Produtor-Consumidor.

Arquitetura:
  - Um PRODUTOR percorre a pasta de logs e envia caminhos para uma Queue limitada.
  - N CONSUMIDORES (workers) retiram arquivos da fila e executam processar_arquivo().
  - Os resultados parciais são armazenados em uma lista compartilhada (thread-safe).
  - Ao final, consolidar_resultados() agrega tudo — sem alteração na lógica original.

Referência de estilo: soma_paralela.py (divisão clara de worker / controle / dados).
Compatível com Python 3.10+ e Windows (guard __main__).
"""

import os
import sys
import time
import queue
import threading

# ──────────────────────────────────────────────────────────────────────────────
# Constantes de configuração
# ──────────────────────────────────────────────────────────────────────────────

# Pasta padrão com os arquivos de log.
DEFAULT_PASTA: str = "log2"

# Tamanho máximo da fila de arquivos (backpressure: o produtor bloqueia se a
# fila estiver cheia, evitando que todos os caminhos sejam carregados de uma vez).
QUEUE_MAXSIZE: int = 10

# Sentinela que sinaliza aos workers que não há mais trabalho.
_SENTINELA = None


# ──────────────────────────────────────────────────────────────────────────────
# Funções originais — NÃO MODIFICADAS
# ──────────────────────────────────────────────────────────────────────────────

def consolidar_resultados(resultados):
    """Agrega os resultados parciais de todos os workers. (Original intacta.)"""
    total_linhas = 0
    total_palavras = 0
    total_caracteres = 0

    contagem_global = {
        "erro": 0,
        "warning": 0,
        "info": 0
    }

    for r in resultados:
        total_linhas += r["linhas"]
        total_palavras += r["palavras"]
        total_caracteres += r["caracteres"]

        for chave in contagem_global:
            contagem_global[chave] += r["contagem"][chave]

    return {
        "linhas": total_linhas,
        "palavras": total_palavras,
        "caracteres": total_caracteres,
        "contagem": contagem_global
    }


def processar_arquivo(caminho):
    """Processa um único arquivo de log. (Original intacta — não alterada.)"""
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = f.readlines()

    total_linhas = len(conteudo)
    total_palavras = 0
    total_caracteres = 0

    contagem = {
        "erro": 0,
        "warning": 0,
        "info": 0
    }

    for linha in conteudo:
        palavras = linha.split()

        total_palavras += len(palavras)
        total_caracteres += len(linha)

        for p in palavras:
            if p in contagem:
                contagem[p] += 1

        # Simulação de processamento pesado (original preservada)
        for _ in range(1000):
            pass

    return {
        "linhas": total_linhas,
        "palavras": total_palavras,
        "caracteres": total_caracteres,
        "contagem": contagem
    }


# ──────────────────────────────────────────────────────────────────────────────
# Execução serial original — PRESERVADA (para fins de comparação)
# ──────────────────────────────────────────────────────────────────────────────

def executar_serial(pasta):
    """Versão serial original. Mantida para comparação de speedup."""
    resultados = []

    inicio = time.time()

    for arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, arquivo)
        resultado = processar_arquivo(caminho)
        resultados.append(resultado)

    fim = time.time()

    resumo = consolidar_resultados(resultados)

    print("\n=== EXECUÇÃO SERIAL ===")
    print(f"Arquivos processados: {len(resultados)}")
    print(f"Tempo total: {fim - inicio:.4f} segundos")

    print("\n=== RESULTADO CONSOLIDADO ===")
    print(f"Total de linhas: {resumo['linhas']}")
    print(f"Total de palavras: {resumo['palavras']}")
    print(f"Total de caracteres: {resumo['caracteres']}")
    print("\nContagem de palavras-chave:")
    for k, v in resumo["contagem"].items():
        print(f"  {k}: {v}")

    return resumo


# ──────────────────────────────────────────────────────────────────────────────
# MONITOR DE PROGRESSO — exibe barra visual no terminal
# ──────────────────────────────────────────────────────────────────────────────

def monitor_progresso(
    contador: list,          # [int] compartilhado — arquivos concluídos
    total: int,              # total de arquivos na pasta
    stop_event: threading.Event,
) -> None:
    """
    Thread dedicada à exibição do progresso.

    Acorda a cada 0,3 s e redesenha a barra no mesmo lugar usando \\r.
    Custo de CPU desprezível — a thread dorme quase todo o tempo.

    Formato da barra:
      [████████░░░░░░░░░░░░]  8/20 arquivos  (40.0%)  ⠹
    """
    # Caracteres do spinner animado
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    spin_i = 0
    BAR_WIDTH = 30  # largura interna da barra em caracteres

    def _desenhar(concluidos: int, finalizado: bool) -> None:
        pct = concluidos / total if total > 0 else 0
        preenchido = int(BAR_WIDTH * pct)
        barra = "█" * preenchido + "░" * (BAR_WIDTH - preenchido)

        if finalizado:
            sufixo = "✔ Concluído!"
        else:
            sufixo = spinner[spin_i % len(spinner)]

        linha = (
            f"\r  [{barra}] {concluidos:>{len(str(total))}}/{total} arquivos"
            f"  ({pct*100:5.1f}%)  {sufixo}   "
        )
        sys.stdout.write(linha)
        sys.stdout.flush()

    while not stop_event.is_set():
        _desenhar(contador[0], finalizado=False)
        spin_i += 1
        time.sleep(0.3)

    # Desenha o estado final (100 %) e quebra a linha
    _desenhar(contador[0], finalizado=True)
    sys.stdout.write("\n")
    sys.stdout.flush()


# ──────────────────────────────────────────────────────────────────────────────
# PRODUTOR — envia caminhos de arquivos para a fila
# ──────────────────────────────────────────────────────────────────────────────

def produtor(pasta: str, fila: queue.Queue, n_workers: int) -> None:
    """
    Percorre a pasta e coloca o caminho de cada arquivo na fila.

    Ao terminar, envia uma sentinela (None) por worker para que cada
    thread consumidora saiba quando parar — sem deadlock.

    O maxsize da fila garante backpressure: o produtor bloqueia quando
    a fila está cheia, evitando acúmulo desnecessário de caminhos.
    """
    for nome_arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, nome_arquivo)
        # put() bloqueia se a fila estiver cheia (backpressure natural)
        fila.put(caminho)

    # Envia uma sentinela para cada worker sinalizar fim de produção
    for _ in range(n_workers):
        fila.put(_SENTINELA)


# ──────────────────────────────────────────────────────────────────────────────
# CONSUMIDOR (worker) — processa arquivos da fila
# ──────────────────────────────────────────────────────────────────────────────

def worker_consumidor(
    fila: queue.Queue,
    resultados: list,
    lock: threading.Lock,
    contador: list,          # [int] — contador compartilhado de arquivos processados
) -> None:
    """
    Loop do consumidor: retira um arquivo da fila e processa.

    Sincronização:
      • `fila.get()` bloqueia até haver item disponível — sem busy-wait.
      • `lock` protege o append em `resultados` (race condition segura).
      • `contador[0]` usa incremento dentro do lock (contagem exata).
      • A sentinela None sinaliza encerramento limpo — sem deadlock.
    """
    while True:
        # Bloqueia até receber um item (ou a sentinela)
        caminho = fila.get()

        # Sentinela recebida: este worker encerra
        if caminho is _SENTINELA:
            fila.task_done()
            break

        # Processa o arquivo (lógica original — fora do lock para máximo paralelismo)
        resultado = processar_arquivo(caminho)

        # Seção crítica mínima: apenas o append e a contagem
        with lock:
            resultados.append(resultado)
            contador[0] += 1

        fila.task_done()


# ──────────────────────────────────────────────────────────────────────────────
# EXECUÇÃO PARALELA — orquestra produtor + consumidores
# ──────────────────────────────────────────────────────────────────────────────

def executar_paralelo(pasta: str, n_threads: int) -> dict:
    """
    Coordena a execução paralela com o padrão Produtor-Consumidor.

    Fluxo:
      1. Cria a fila limitada e as estruturas compartilhadas.
      2. Inicia N threads consumidoras.
      3. Inicia 1 thread produtora (não bloqueia a thread principal).
      4. Aguarda término de todas as threads.
      5. Consolida e exibe os resultados.

    Parâmetros:
      pasta     — caminho da pasta com os arquivos de log.
      n_threads — número de threads consumidoras (workers).
    """

    # ── Contagem total de arquivos (para a barra de progresso) ──────────────
    total_arquivos = sum(1 for _ in os.listdir(pasta))

    # ── Estruturas compartilhadas ────────────────────────────────────────────
    # Fila com backpressure: produtor não antecipa mais do que maxsize arquivos
    fila: queue.Queue = queue.Queue(maxsize=QUEUE_MAXSIZE)

    # Lista de resultados — protegida por lock nos appends
    resultados: list = []

    # Lock exclusivo para seção crítica de escrita em `resultados`
    lock = threading.Lock()

    # Contador de arquivos processados (dentro do lock, portanto exato)
    contador: list = [0]

    # Evento para sinalizar ao monitor que os workers terminaram
    stop_event = threading.Event()

    # ── Criação das threads consumidoras (workers) ───────────────────────────
    workers: list[threading.Thread] = []
    for i in range(n_threads):
        t = threading.Thread(
            target=worker_consumidor,
            args=(fila, resultados, lock, contador),
            daemon=True,
            name=f"worker-{i}",
        )
        workers.append(t)

    # ── Thread produtora ─────────────────────────────────────────────────────
    # Rodar em thread separada evita bloquear a thread principal durante put()
    t_produtor = threading.Thread(
        target=produtor,
        args=(pasta, fila, n_threads),
        daemon=True,
        name="produtor",
    )

    # ── Thread do monitor de progresso ──────────────────────────────────────
    t_monitor = threading.Thread(
        target=monitor_progresso,
        args=(contador, total_arquivos, stop_event),
        daemon=True,
        name="monitor",
    )

    # ── Execução e medição ───────────────────────────────────────────────────
    t_inicio = time.perf_counter()

    # Inicia workers antes do produtor para que já estejam prontos ao receber itens
    for t in workers:
        t.start()

    t_produtor.start()
    t_monitor.start()

    # Aguarda o produtor terminar de enfileirar tudo
    t_produtor.join()

    # Aguarda cada worker finalizar (eles param ao receber a sentinela)
    for t in workers:
        t.join()

    # Sinaliza ao monitor para exibir 100% e encerrar
    stop_event.set()
    t_monitor.join()

    t_fim = time.perf_counter()
    tempo_total = t_fim - t_inicio

    # ── Consolidação e saída ─────────────────────────────────────────────────
    resumo = consolidar_resultados(resultados)

    print(f"\n{'='*45}")
    print("  EXECUÇÃO PARALELA — Produtor-Consumidor")
    print(f"{'='*45}")
    print(f"Threads utilizadas : {n_threads}")
    print(f"Arquivos processados: {contador[0]}")
    print(f"Tempo total        : {tempo_total:.6f} segundos")

    print(f"\n{'='*45}")
    print("  RESULTADO CONSOLIDADO")
    print(f"{'='*45}")
    print(f"Total de linhas    : {resumo['linhas']}")
    print(f"Total de palavras  : {resumo['palavras']}")
    print(f"Total de caracteres: {resumo['caracteres']}")
    print("\nContagem de palavras-chave:")
    for k, v in resumo["contagem"].items():
        print(f"  {k}: {v}")

    return resumo


# ──────────────────────────────────────────────────────────────────────────────
# Entry point — compatível com Windows
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 45)
    print("  Avaliador Paralelo de Logs")
    print("=" * 45)

    pasta = input(f"\nPasta de logs [{DEFAULT_PASTA}]: ").strip() or DEFAULT_PASTA

    if not os.path.isdir(pasta):
        print(f"\n[ERRO] Pasta '{pasta}' não encontrada.")
        raise SystemExit(1)

    while True:
        try:
            n = int(input("Quantas threads deseja usar? [2/4/8/12]: ").strip())
            if n < 1:
                raise ValueError
            break
        except ValueError:
            print("  → Digite um inteiro positivo.")

    executar_paralelo(pasta, n)
