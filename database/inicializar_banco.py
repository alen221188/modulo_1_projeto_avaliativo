import os
from sqlalchemy import text
from banco import obter_engine, executar_query

# Nome do banco de dados que queremos criar para o nosso projeto
NOME_BANCO_PROJETO = "viagens_servico"

def banco_existe():
    """
    Verifica se o banco de dados do projeto já existe no PostgreSQL.
    """
    engine = obter_engine("postgres")
    query = f"SELECT 1 FROM pg_database WHERE datname = '{NOME_BANCO_PROJETO}';"
    
    with engine.connect() as conexao:
        resultado = conexao.execute(text(query)).fetchone()
        return resultado is not None

def criar_banco_de_dados():
    """
    Cria o banco de dados do projeto se ele não existir.
    """
    if banco_existe():
        print(f"O banco de dados '{NOME_BANCO_PROJETO}' já existe.")
    else:
        print(f"Criando o banco de dados '{NOME_BANCO_PROJETO}'...")
        executar_query(f"CREATE DATABASE {NOME_BANCO_PROJETO};", dbname="postgres", autocommit=True)
        print(f"Banco de dados '{NOME_BANCO_PROJETO}' criado com sucesso!")

def criar_tabelas():
    """
    Lê o arquivo '0_criar_banco.sql' local e cria as tabelas no banco de dados.
    """
    # Usamos o caminho absoluto da pasta deste script para achar o arquivo SQL local
    caminho_diretorio = os.path.dirname(os.path.abspath(__file__))
    caminho_sql = os.path.join(caminho_diretorio, "0_criar_banco.sql")
    
    if not os.path.exists(caminho_sql):
        print(f"Erro: O arquivo {caminho_sql} não foi encontrado.")
        return
        
    print(f"Lendo e executando o arquivo {caminho_sql} no banco '{NOME_BANCO_PROJETO}'...")
    
    with open(caminho_sql, "r", encoding="utf-8") as arquivo:
        script_sql = arquivo.read()
        
    engine = obter_engine(NOME_BANCO_PROJETO)
    with engine.begin() as conexao:
        conexao.execute(text(script_sql))
        
    print("Todas as tabelas (Raw e Silver) foram criadas com sucesso!")

if __name__ == "__main__":
    print("=== INICIALIZANDO O BANCO DE DADOS E TABELAS (MODULAR) ===")
    try:
        criar_banco_de_dados()
        criar_tabelas()
        print("\nPronto! Tudo configurado com sucesso no PostgreSQL local.")
    except Exception as e:
        print(f"\nErro durante a inicialização: {e}")
        print("Dica: Verifique se o serviço do PostgreSQL está rodando e se sua senha no arquivo .env está correta.")
