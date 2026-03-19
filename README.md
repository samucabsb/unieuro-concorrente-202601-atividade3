# unieuro-concorrente-202601-atividade3
Paralelizar avaliador de arquivos de log.

## Passo-a-passo

1) Implemente a solução paralela que possa ser executada com 2, 4, 8, 12 processos
2) Execute o experimento para medir os tempos em paralelo
3) Construa um relatório de análise dos resultados (MODELO DO RELATÓRIO RELATORIO_MODELO.MD - SALVAR COMO README.MD)
4) Crie um repositório público no GitHub incluindo os programas python e o README.MD no formato de relatório.
5) Responda o questionário no AVA

## Problema

Uma empresa precisa processar grandes volumes de arquivos texto contendo logs operacionais. Cada arquivo deve ser analisado para extrair informações relevantes que serão utilizadas em relatórios gerenciais.

Atualmente, o sistema realiza esse processamento de forma sequencial (serial), o que gera um tempo elevado de execução quando há muitos arquivos.

Para melhorar o desempenho, deseja-se evoluir o sistema para uma versão paralela, utilizando o modelo produtor-consumidor com buffer limitado.
