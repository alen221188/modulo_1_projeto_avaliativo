# Módulo 1 - Projeto Avaliativo: Análise de Dados com Python e PostgreSQL

Pipeline de dados local que extrai informações de viagens a serviço do Portal da Transparência do Governo Federal, realiza o tratamento e armazenamento em um banco de dados PostgreSQL utilizando a Arquitetura Medallion (Raw → Silver → Gold).

---

## Arquitetura do Projeto

```
Raw (CSV/API brutos) → Silver (dados limpos e tipados) → Gold (análises e relatórios)
```

## Estrutura de Pastas

```
.
├── .env.example              # Modelo de variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
├── config.py                 # Carrega as variáveis de ambiente
├── requirements.txt          # Dependências Python do projeto
├── database/
│   ├── 0_criar_banco.sql     # Definição das tabelas Raw e Silver
│   ├── banco.py              # Funções reutilizáveis de conexão (SQLAlchemy)
│   └── inicializar_banco.py  # Script de setup do banco de dados
```

## Pré-requisitos

- Python 3.10+
- PostgreSQL instalado e rodando localmente

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
Copie o arquivo de exemplo e preencha com suas credenciais locais:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com os dados do seu PostgreSQL local.

### 5. Inicialize o banco de dados
```bash
python database/inicializar_banco.py
```
Esse script criará automaticamente o banco de dados `viagens_servico` e todas as tabelas das camadas Raw e Silver.

## Tecnologias Utilizadas

- **Python 3.14** — Linguagem principal
- **Pandas** — Leitura e transformação de dados
- **SQLAlchemy** — Abstração de conexão com o banco de dados
- **psycopg2** — Driver PostgreSQL para Python
- **python-dotenv** — Gerenciamento seguro de credenciais
- **PostgreSQL** — Banco de dados relacional local
