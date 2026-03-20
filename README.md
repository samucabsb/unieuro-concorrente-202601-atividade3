# Relatório da Paralelização de Avaliador de Logs

**Disciplina:** Programação Paralela  
**Aluno(s):** Samuel Souza  
**Turma:** Análise de Sistemas - 5º Semestre 
**Professor:** Rafael
**Data:** 20/03/2026  

---

# 1. Descrição do Problema

O problema consiste no processamento de grandes volumes de arquivos de log contendo informações operacionais. Cada arquivo deve ser analisado para extrair métricas como número de linhas, palavras, caracteres e contagem de palavras-chave relevantes ("erro", "warning", "info").

O algoritmo implementado percorre todos os arquivos de uma pasta e, para cada arquivo, realiza a leitura linha a linha, contabilizando as métricas mencionadas. Trata-se de um algoritmo de varredura completa (full scan), com complexidade aproximadamente O(N), onde N representa o total de caracteres processados.

O volume de dados utilizado nos testes foi:

- 1000 arquivos
- 10.000.000 linhas
- 200.000.000 palavras
- 1.366.663.305 caracteres

O objetivo da paralelização foi reduzir o tempo total de execução distribuindo o processamento dos arquivos entre múltiplas threads, utilizando o modelo produtor-consumidor.

**Questões que devem ser respondidas:**

* Qual é o objetivo do programa?  
Processar arquivos de log e extrair métricas agregadas para análise.

* Qual o volume de dados processado?  
Aproximadamente 10 milhões de linhas e mais de 1,3 bilhões de caracteres.

* Qual algoritmo foi utilizado?  
Varredura sequencial de arquivos com contagem de tokens e agregação.

* Qual a complexidade aproximada do algoritmo?  
O(N), sendo N o tamanho total dos dados.

---

# 2. Ambiente Experimental

| Item                        | Descrição                     |
| --------------------------- | ----------------------------- |
| Processador                 | Intel(R) Core(TM) i5-12500   |
| Número de núcleos           | 6                             |
| Memória RAM                 | 16 GB                         |
| Sistema Operacional         | Windows 11                    |
| Linguagem utilizada         | Python 3                      |
| Biblioteca de paralelização | threading, queue              |
| Compilador / Versão         | Python 3.13                   |

---

# 3. Metodologia de Testes

Os tempos de execução foram medidos utilizando a função `time.perf_counter()`, garantindo maior precisão.

Foi realizada uma execução para cada configuração de threads, considerando que o volume de dados é suficientemente grande para representar o comportamento do sistema.

### Configurações testadas

* 1 thread (versão serial)
* 2 threads
* 4 threads
* 8 threads
* 12 threads

### Procedimento experimental

* Cada configuração foi executada uma vez
* Ambiente com baixa interferência externa
* Máquina utilizada sem carga significativa durante os testes
* Entrada fixa (mesmo conjunto de arquivos)

---

# 4. Resultados Experimentais

| Nº Threads/Processos | Tempo de Execução (s) |
| -------------------- | --------------------- |
| 1                    | 114,67                |
| 2                    | 58,12                 |
| 4                    | 30,21                 |
| 8                    | 18,54                 |
| 12                   | 16,80                 |

---

# 5. Cálculo de Speedup e Eficiência

## Fórmulas Utilizadas

### Speedup


Speedup(p) = T(1) / T(p)


Onde:

* **T(1)** = tempo da execução serial  
* **T(p)** = tempo com p threads/processos  

### Eficiência


Eficiência(p) = Speedup(p) / p


Onde:

* **p** = número de threads ou processos  

---

# 6. Tabela de Resultados

| Threads/Processos | Tempo (s) | Speedup | Eficiência |
| ----------------- | --------- | ------- | ---------- |
| 1                 | 114,67    | 1,0     | 1,0        |
| 2                 | 58,12     | 2,0     | 0,99       |
| 4                 | 30,21     | 3,8     | 0,96       |
| 8                 | 18,54     | 6,3     | 0,78       |
| 12                | 16,80     | 6,9     | 0,57       |

---

# 7. Gráfico de Tempo de Execução

![Gráfico Tempo Execução](graficos/Tempo_de_Execução.png)

---

# 8. Gráfico de Speedup

![Gráfico Speedup](graficos/SPEEDUP.png)

---

# 9. Gráfico de Eficiência

![Gráfico Eficiência](graficos/Eficiência.png)

---

# 10. Análise dos Resultados

O speedup obtido foi próximo do ideal nas configurações iniciais, especialmente com 2 e 4 threads, onde houve quase duplicação e quadruplicação do desempenho em relação à execução serial.

A aplicação apresentou boa escalabilidade até aproximadamente 4 threads. A partir desse ponto, o ganho de desempenho continuou, porém com redução progressiva na eficiência.

A eficiência começou a cair de forma mais significativa a partir de 8 threads, indicando início de saturação dos recursos da máquina.

Considerando que o processador possui 6 núcleos físicos, o uso de 8 e 12 threads ultrapassa a capacidade ideal de paralelismo, o que explica a redução da eficiência.

Foi observado overhead de paralelização, causado por:

* Criação e gerenciamento de threads
* Sincronização no acesso à lista de resultados
* Contenção de recursos de CPU e cache
* Overhead do modelo produtor-consumidor

Mesmo com essas limitações, o desempenho geral foi significativamente melhor do que a execução serial.

---

# 11. Conclusão

O paralelismo trouxe um ganho significativo de desempenho, reduzindo o tempo de execução de aproximadamente 114,67 segundos para 16,80 segundos na melhor configuração.

O melhor equilíbrio entre desempenho e eficiência foi observado com 4 threads, onde a eficiência ainda se manteve elevada e o ganho de desempenho foi expressivo.

O programa apresentou boa escalabilidade até o limite dos recursos físicos da máquina. Após esse ponto, o aumento do número de threads trouxe ganhos menores devido ao overhead e limitações do hardware.

Melhorias possíveis incluem:

* Ajustar dinamicamente o número de threads com base nos núcleos disponíveis
* Reduzir o custo de sincronização
* Utilizar multiprocessing para explorar paralelismo real em CPU-bound
* Otimizar o uso de memória e cache

Conclui-se que a paralelização foi eficaz e trouxe ganhos substanciais quando corretamente dimensio
