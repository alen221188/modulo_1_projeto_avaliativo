"""
inicializar_banco.py
---------------------
Prepara o banco de dados do projeto. Rode UMA vez, antes do 1_extrair.py.

TRABALHO A: cria o banco 'transparencia' (se ainda nao existir).
TRABALHO B: cria as 8 tabelas dentro dele (rodando o 0_criar_banco.sql).
"""

import sys
from pathlib import Path

# Dica ao Python: procure modulos tambem na RAIZ do projeto (uma pasta acima
# desta). Assim conseguimos importar o config.py e o pacote database.
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import psycopg2

from config import POSTGRES_CONFIG
from database.banco import conectar, executar

# Onde esta o arquivo SQL com o CREATE das tabelas (mesma pasta deste script).
CAMINHO_SQL = Path(__file__).resolve().parent / "0_criar_banco.sql"


def criar_banco_se_nao_existir():
    """
    TRABALHO A.
    Conecta no banco administrativo 'postgres' (que sempre existe) e cria o
    banco do projeto caso ele ainda nao exista.
    """
    nome_banco = POSTGRES_CONFIG["dbname"]

    # 1. Conexao especial ao banco 'postgres' (copiamos o config trocando so o
    #    dbname), porque nao da para conectar no 'transparencia' antes de existir.
    config_admin = {**POSTGRES_CONFIG, "dbname": "postgres"}
    conexao = psycopg2.connect(**config_admin)

    # 2. Ligar o autocommit: CREATE DATABASE nao pode rodar dentro de transacao.
    conexao.autocommit = True

    cursor = conexao.cursor()

    # 3. Perguntar ao Postgres se o banco do projeto ja existe.
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (nome_banco,))
    ja_existe = cursor.fetchone() is not None

    # 4. Criar somente se ainda nao existir (idempotente).
    if ja_existe:
        print(f"Banco '{nome_banco}' ja existe. Nada a fazer.")
    else:
        cursor.execute(f'CREATE DATABASE "{nome_banco}";')
        print(f"Banco '{nome_banco}' criado com sucesso.")

    # 5. Fechar cursor e conexao.
    cursor.close()
    conexao.close()


def criar_tabelas():
    """
    TRABALHO B.
    Conecta no banco do projeto, le o 0_criar_banco.sql e executa (cria as tabelas).
    """
    # 1. Ler o conteudo do arquivo 0_criar_banco.sql (texto puro).
    script_sql = CAMINHO_SQL.read_text(encoding="utf-8")

    # 2. Conectar no banco do projeto (aqui usamos o conectar() do banco.py,
    #    que ja aponta para o 'transparencia' definido no config).
    conexao = conectar()

    # 3. Executar o script inteiro de uma vez (varios CREATE TABLE seguidos).
    executar(conexao, script_sql)

    # 4. Fechar a conexao.
    conexao.close()
    print("Tabelas (Raw e Silver) criadas/verificadas.")


if __name__ == "__main__":
    print("=== Inicializando banco e tabelas ===")
    try:
        criar_banco_se_nao_existir()  # TRABALHO A
        criar_tabelas()               # TRABALHO B
        print("Pronto! Banco e tabelas configurados com sucesso.")
    except Exception as erro:
        print(f"Erro na inicializacao: {erro}")
        print("Dica: o PostgreSQL esta rodando? A senha no .env esta correta?")
