import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Adiciona o diretório raiz do projeto ao sys.path para conseguir importar o config.py
# __file__ é o caminho deste arquivo (database/banco.py)
# os.path.dirname(__file__) é a pasta (database/)
# os.path.dirname(os.path.dirname(__file__)) é a pasta raiz (Projeto_analise_de_dados _postgreesql/)
diretorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if diretorio_raiz not in sys.path:
    sys.path.append(diretorio_raiz)

from config import DB_CONFIG

def obter_engine(dbname=None):
    """
    Cria e retorna uma engine do SQLAlchemy para conexão com o PostgreSQL.
    """
    usuario = DB_CONFIG["user"]
    senha = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    porta = DB_CONFIG["port"]
    
    banco = dbname if dbname else DB_CONFIG["database"]
    url_conexao = f"postgresql://{usuario}:{senha}@{host}:{porta}/{banco}"
    
    return create_engine(url_conexao)

def executar_query(query_sql, dbname=None, autocommit=False):
    """
    Executa uma instrução SQL no banco de dados.
    """
    engine = obter_engine(dbname)
    
    with engine.connect() as conexao:
        if autocommit:
            conexao = conexao.execution_options(isolation_level="AUTOCOMMIT")
        conexao.execute(text(query_sql))

def inserir_em_lote(df, nome_tabela, dbname=None, se_existir="append"):
    """
    Insere um DataFrame do Pandas em lote no banco de dados.
    """
    engine = obter_engine(dbname)
    
    df.to_sql(
        name=nome_tabela,
        con=engine,
        if_exists=se_existir,
        index=False,
        chunksize=5000
    )
