import os
import time
import random
import string


# ===============================
# Geração de arquivos de teste
# ===============================

def gerar_arquivos(pasta, qtd_arquivos=50, linhas_por_arquivo=200):
    os.makedirs(pasta, exist_ok=True)

    palavras = ["erro", "warning", "info", "processo", "dados", "sistema"]

    for i in range(qtd_arquivos):
        with open(os.path.join(pasta, f"arquivo_{i}.txt"), "w", encoding="utf-8") as f:
            for _ in range(linhas_por_arquivo):
                linha = " ".join(random.choices(palavras, k=20))
                f.write(linha + "\n")


# ===============================
# Processamento de arquivo
# ===============================

def processar_arquivo(caminho):
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

        # Simulação de processamento pesado
        for _ in range(1000):
            pass

    return {
        "linhas": total_linhas,
        "palavras": total_palavras,
        "caracteres": total_caracteres,
        "contagem": contagem
    }


# ===============================
# Execução serial
# ===============================

def executar_serial(pasta):
    resultados = []

    inicio = time.time()

    for arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, arquivo)

        resultado = processar_arquivo(caminho)
        resultados.append(resultado)

    fim = time.time()

    print("=== EXECUÇÃO SERIAL ===")
    print(f"Arquivos processados: {len(resultados)}")
    print(f"Tempo total: {fim - inicio:.4f} segundos")

    return resultados


# ===============================
# Main
# ===============================

if __name__ == "__main__":
    pasta = "dados"

    print("Gerando arquivos de teste...")
    gerar_arquivos(pasta, qtd_arquivos=100, linhas_por_arquivo=300)

    print("Executando versão serial...")
    executar_serial(pasta)
