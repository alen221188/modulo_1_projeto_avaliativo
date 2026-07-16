# Módulo 1 - Projeto Avaliativo: Análise de Dados com Python e PostgreSQL

Pipeline de dados que extrai informações de viagens a serviço do Portal da Transparência do Governo Federal (base de 6 meses de 2025), trata e organiza os dados em um banco de dados PostgreSQL utilizando a Arquitetura Medallion (Raw → Silver → Gold), e responde perguntas de negócio com consultas SQL e gráficos.

---

## O problema que este projeto resolve

Os dados de viagens a serviço são publicados pelo governo em sua forma bruta, desorganizada e sem tipagem — o que dificulta qualquer análise confiável. Este projeto constrói um pipeline de ponta a ponta que baixa os dados automaticamente, preserva o histórico original para fins de auditoria, limpa e tipa a estrutura, e transforma o resultado em métricas e gráficos que apoiam a tomada de decisão.

## Arquitetura do Projeto

```
Raw (CSVs brutos) → Silver (dados limpos e tipados) → Gold (métricas agregadas e gráficos)
```

- **Raw**: cópia fiel dos 4 CSVs de origem, com colunas renomeadas para snake_case mas sem qualquer tratamento de conteúdo (tudo `VARCHAR`).
- **Silver**: dados convertidos para os tipos corretos (`DATE`, `DECIMAL`, `INT`), com chaves primárias, chaves estrangeiras e constraints de integridade.
- **Gold**: tabelas agregadas (`gold_orgao`, `gold_destino`), construídas com `JOIN` + `GROUP BY`, que respondem às perguntas de negócio do projeto.

## Estrutura de Pastas

```
.
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Ignora .env, .zip, .csv, data/, .venv/
├── config.py                 # Carrega variáveis de ambiente e parâmetros do pipeline
├── requirements.txt          # Dependências Python do projeto
├── database/
│   ├── 0_criar_banco.sql     # Criação das 8 tabelas (4 Raw + 4 Silver) com PK, FK e constraints
│   ├── banco.py              # Funções de conexão e execução no PostgreSQL (psycopg2)
│   └── inicializar_banco.py  # Cria o banco de dados e roda o 0_criar_banco.sql
├── extract/
│   └── 1_extrair.py          # Fase 1: baixa o .zip do Google Drive e carrega a camada Raw
├── transform/
│   └── 2_transformar.py      # Fase 2: converte tipos e carrega a camada Silver
└── analysis/
    └── 3_analise.ipynb       # Fase 3: camada Gold, perguntas de negócio e gráficos
```

## Pré-requisitos

- Python 3.10+
- PostgreSQL instalado e rodando localmente
- Jupyter/VSCode com suporte a notebooks (para a Fase 3)

## Como Configurar e Executar

### 1. Clone o repositório
```bash
git clone https://github.com/alen221188/modulo_1_projeto_avaliativo.git
cd modulo_1_projeto_avaliativo
```

### 2. Crie e ative o ambiente virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente
Copie o arquivo de exemplo e preencha com as credenciais do seu PostgreSQL local:
```bash
cp .env.example .env
```

### 5. Crie o banco de dados e as tabelas
```bash
python database/inicializar_banco.py
```
Cria o banco `transparencia` (se ainda não existir) e as 8 tabelas (4 Raw + 4 Silver), com PK, FK e constraints.

### 6. Extraia os dados para a camada Raw
```bash
python extract/1_extrair.py
```
Baixa o `.zip` do Google Drive, extrai os 4 CSVs e carrega cada um em sua tabela Raw. Processo idempotente (pode ser executado várias vezes sem duplicar dados) e resiliente a falhas.

### 7. Transforme os dados para a camada Silver
```bash
python transform/2_transformar.py
```
Converte os campos de texto para `DATE`/`DECIMAL`/`INT`, calcula `valor_total` e `duracao_dias`, e carrega as 4 tabelas Silver respeitando a integridade referencial.

### 8. Explore a camada Gold e as análises
Abra `analysis/3_analise.ipynb` no VSCode ou Jupyter (selecionando o kernel do `.venv`) e execute as células. O notebook cria as tabelas `gold_orgao` e `gold_destino` (cada uma também como VIEW) e responde às 7 perguntas de negócio com tabelas e gráficos.

## Perguntas de negócio respondidas

1. Os 5 órgãos com maior custo total
2. Os 3 destinos com maior custo médio por viagem
3. A viagem de maior duração e seu custo total
4. O tipo de pagamento com maior valor médio
5. O meio de transporte mais usado nos trechos
6. A UF de destino que aparece em mais trechos
7. O órgão que pagou mais no total

## Tecnologias Utilizadas

- **Python** — linguagem principal do pipeline
- **pandas** — leitura dos CSVs em blocos e manipulação de dados para os gráficos
- **psycopg2** — driver PostgreSQL puro (conexão, execução de SQL e inserção em lote)
- **gdown** — download automatizado de arquivos do Google Drive
- **matplotlib** — geração dos gráficos (título, eixos nomeados e legenda em todos)
- **Jupyter/ipykernel** — execução da camada Gold e das análises em notebook
- **PostgreSQL** — banco de dados relacional

As credenciais ficam exclusivamente no arquivo `.env` (fora do controle de versão); `.gitignore` cobre dados baixados (`.zip`, `.csv`, `data/`) e ambiente virtual.

## Melhorias possíveis

- Adicionar testes automatizados para as funções de conversão (`converter_decimal`, `converter_data`, `converter_inteiro`) e para o pipeline de carga.
- Parametrizar o período de referência (`ANO`) para permitir reprocessar outros recortes de dados sem alterar código.
- Adicionar tratamento explícito para os valores "Inválido" encontrados em `meio_transporte` e `destino_uf`, hoje apenas documentados na análise.
- Automatizar a execução das 3 fases via um único script/orquestrador (ou uma ferramenta como Airflow), em vez de rodar cada arquivo manualmente.
- Adicionar um mecanismo de log estruturado (hoje o acompanhamento é via `print`).

## Conclusões e Insights

- O **Ministério da Justiça e Segurança Pública** concentra o maior custo total e o maior valor pago em viagens, mais de 3x o segundo colocado — tanto o custo calculado na Silver quanto o valor efetivamente pago (Gold) convergem, o que valida a consistência entre as camadas.
- Há uma dissociação entre **volume** e **custo médio** por destino: São Paulo e Distrito Federal concentram o maior número de trechos, mas os destinos com maior custo médio por viagem são estados do Norte (Roraima, Acre, Rondônia), refletindo menor oferta de voos e maior distância dos grandes centros.
- **Veículo Oficial** é o meio de transporte predominante nos trechos (50,6%), à frente do transporte aéreo (30,5%); **Diárias** é o tipo de pagamento com maior valor médio.
- O pipeline preserva fielmente inconsistências do dado bruto (ex.: 5,4% das viagens com custo zero, categorias "Inválido" em alguns campos) em vez de escondê-las — a camada Raw garante rastreabilidade total, e essas inconsistências ficam documentadas na análise da camada Gold.
- A construção da camada Gold exigiu tratamento cuidadoso de **fan-out** (duplicação de valores ao agregar tabelas em relação um-para-muitos), resolvido agregando os dados por viagem antes de qualquer `JOIN` final.
