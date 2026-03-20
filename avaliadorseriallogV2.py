import os
import sys
import time
import mmap
import threading
import multiprocessing
from multiprocessing import Pool

DEFAULT_PASTA = "log2"

# ── Processamento de Alta Performance ───────────────────────────────────────

def processar_arquivo_ultra(caminho):
    """Processa o arquivo em nível de bytes para máxima performance e compatibilidade."""
    try:
        tamanho = os.path.getsize(caminho)
        if tamanho == 0:
            return (0, 0, 0, [0, 0, 0])

        with open(caminho, "rb") as f:
            # Mapeia o arquivo. Se o arquivo for muito pequeno, o read() direto é melhor,
            # mas o mmap ajuda muito no cache do Sistema Operacional.
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                # Lemos o conteúdo do mmap para um objeto de bytes (conteudo agora tem o método .count)
                conteudo = mm.read()
                
                # 1. Contagem de Linhas
                linhas = conteudo.count(b'\n')
                
                # 2. Contagem de Caracteres (tamanho bruto em bytes)
                caracteres = tamanho
                
                # 3. Contagem de Palavras 
                # .split() sem argumentos remove qualquer espaço em branco, abas e quebras de linha
                total_palavras = len(conteudo.split())
                
                # 4. Palavras-chave (Busca binária direta em C)
                # IMPORTANTE: Usamos b"termo" para buscar nos bytes sem decodificar texto
                c_erro = conteudo.count(b"erro")
                c_warn = conteudo.count(b"warning")
                c_info = conteudo.count(b"info")

        return (linhas, total_palavras, caracteres, [c_erro, c_warn, c_info])
    except Exception as e:
        # Se falhar, retorna zerado para não quebrar a soma global
        return (0, 0, 0, [0, 0, 0])

def consolidar_resultados_ultra(resultados):
    t_linhas = 0
    t_palavras = 0
    t_caracteres = 0
    c_erros, c_warns, c_infos = 0, 0, 0

    for r in resultados:
        t_linhas     += r[0]
        t_palavras   += r[1]
        t_caracteres += r[2]
        c_erros      += r[3][0]
        c_warns      += r[3][1]
        c_infos      += r[3][2]

    return {
        "linhas": t_linhas,
        "palavras": t_palavras,
        "caracteres": t_caracteres,
        "contagem": {"erro": c_erros, "warning": c_warns, "info": c_infos},
    }

# ── Execução ────────────────────────────────────────────────────────────────

def executar(pasta: str, n_workers: int) -> None:
    # Coletar arquivos
    arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta)
                if os.path.isfile(os.path.join(pasta, f))]
    total = len(arquivos)

    if total == 0:
        print("\n  [!] Nenhum arquivo encontrado.")
        return

    # Ordenar por tamanho (descendente) para otimizar o escalonamento dos cores
    arquivos.sort(key=os.path.getsize, reverse=True)

    print(f"\n  {'='*50}")
    print(f"  EXECUTANDO EM {n_workers} CORES")
    print(f"  {'='*50}")
    
    contador = [0]
    stop_event = threading.Event()
    t_mon = threading.Thread(target=_monitor, args=(contador, total, stop_event), daemon=True)

    t0 = time.perf_counter()
    t_mon.start()

    # Processamento paralelo
    with Pool(processes=n_workers) as pool:
        # Ajustamos o chunksize para que cada worker pegue um lote de arquivos por vez
        chunksize = max(1, total // (n_workers * 4))
        resultados = []
        for res in pool.imap_unordered(processar_arquivo_ultra, arquivos, chunksize=chunksize):
            resultados.append(res)
            contador[0] += 1

    tempo = time.perf_counter() - t0
    stop_event.set()
    t_mon.join()

    resumo = consolidar_resultados_ultra(resultados)
    
    # Formatação de saída conforme solicitado
    print(f"\n\n  === RESULTADO CONSOLIDADO ===")
    print(f"  Total de linhas: {resumo['linhas']}")
    print(f"  Total de palavras: {resumo['palavras']}")
    print(f"  Total de caracteres: {resumo['caracteres']}")
    print(f"  Contagem de palavras-chave:")
    print(f"  erro: {resumo['contagem']['erro']}")
    print(f"  warning: {resumo['contagem']['warning']}")
    print(f"  info: {resumo['contagem']['info']}")
    print(f"  ----------------------------------------------")
    print(f"  Tempo total: {tempo:.4f} segundos")

def _monitor(contador, total, stop_event):
    while not stop_event.is_set():
        n = contador[0]
        pct = (n / total) * 100 if total > 0 else 0
        sys.stdout.write(f"\r  [PROGRESSO] {n}/{total} ({pct:.1f}%)")
        sys.stdout.flush()
        time.sleep(0.05)

if __name__ == "__main__":
    multiprocessing.freeze_support()
    cpus = os.cpu_count() or 1
    
    pasta = input(f"  Pasta de logs [{DEFAULT_PASTA}]: ").strip() or DEFAULT_PASTA
    try:
        workers = int(input(f"  Quantidade de workers (Sugerido {cpus}): ") or cpus)
    except: workers = cpus
    
    executar(pasta, workers)
