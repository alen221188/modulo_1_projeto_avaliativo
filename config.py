import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env localizado na raiz do projeto
load_dotenv()

# Dicionário de configuração de conexão com o banco de dados PostgreSQL
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASS")
}

# Identificador do arquivo no Google Drive para download do ZIP
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID")
