"""
1_extrair.py
------------
FASE 1 do pipeline (Extracao -> camada Raw).

Baixa o .zip do Google Drive, extrai os 4 CSVs e carrega cada um na sua
tabela raw_* SEM tratar o conteudo. O processo e idempotente (TRUNCATE antes
de carregar) e resiliente (try/except no maestro).
"""

import sys
import zipfile
from pathlib import Path

# Dica ao Python: procure modulos tambem na RAIZ do projeto (uma pasta acima),
# para conseguirmos importar o config.py e o pacote database.
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import gdown
import pandas as pd

from config import (
    DRIVE_FILE_ID,
    PASTA_DADOS,
    ARQUIVOS,
    TAMANHO_BLOCO,
    CSV_SEPARADOR,
    CSV_ENCODING,
)
from database.banco import conectar, executar, inserir_em_lote

# Caminho do .zip que sera baixado (fica dentro da pasta data/).
CAMINHO_ZIP = PASTA_DADOS / "viagens.zip"


def baixar_zip():
    """BLOCO 2: baixa o .zip do Google Drive para a pasta data/."""
    # 1. Garantir que a pasta data/ existe (cria se preciso, sem erro se ja existe).
    PASTA_DADOS.mkdir(exist_ok=True)

    # Se o zip ja foi baixado antes, nao baixa de novo (economiza tempo/banda).
    if CAMINHO_ZIP.exists():
        print(f"Zip ja existe em {CAMINHO_ZIP} -> pulando download.")
        return

    # 2. Montar a URL de download a partir do ID do arquivo no Drive.
    url = f"https://drive.google.com/uc?id={DRIVE_FILE_ID}"

    # 3. Baixar com gdown (quiet=False mostra a barra de progresso).
    print("Baixando o .zip do Google Drive...")
    gdown.download(url, str(CAMINHO_ZIP), quiet=False)
    print(f"Download concluido: {CAMINHO_ZIP}")


def extrair_zip():
    """BLOCO 3: descompacta os 4 CSVs de dentro do .zip."""
    # 1. Abrir o arquivo .zip em modo leitura.
    print("Extraindo os CSVs do .zip...")
    with zipfile.ZipFile(CAMINHO_ZIP, "r") as zip_ref:
        # 2. Extrair todo o conteudo para a pasta data/.
        zip_ref.extractall(PASTA_DADOS)
    print("Extracao concluida.")


def obter_colunas(conexao, tabela):
    """Auxiliar: devolve os nomes das colunas da tabela, na ordem do banco."""
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = %s ORDER BY ordinal_position;",
        (tabela,),
    )
    colunas = [linha[0] for linha in cursor.fetchall()]
    cursor.close()
    return colunas


def carregar_csv_na_raw(conexao, caminho_csv, tabela_raw, colunas):
    """BLOCO 4: le um CSV em blocos e insere na tabela raw (TRUNCATE antes)."""
    # 1. Limpar a tabela antes de carregar -> garante idempotencia (rodar 2x
    #    nao duplica: sempre zera e recarrega).
    executar(conexao, f"TRUNCATE TABLE {tabela_raw};")

    # 2. Montar o INSERT dinamicamente, com um %s para cada coluna.
    #    Ex.: INSERT INTO raw_viagem (id_viagem, ...) VALUES (%s, %s, ...)
    lista_colunas = ", ".join(colunas)
    marcadores = ", ".join(["%s"] * len(colunas))
    sql_insert = f"INSERT INTO {tabela_raw} ({lista_colunas}) VALUES ({marcadores})"

    # 3. Ler o CSV EM BLOCOS (nunca tudo de uma vez -> economiza memoria).
    leitor = pd.read_csv(
        caminho_csv,
        sep=CSV_SEPARADOR,        # ";"
        encoding=CSV_ENCODING,    # "latin-1"
        dtype=str,                # tudo como TEXTO (camada Raw = sem tratar)
        keep_default_na=False,    # celula vazia vira "" (e nao NaN)
        header=0,                 # a 1a linha do CSV e o cabecalho original...
        names=colunas,            # ...que trocamos pelos NOSSOS nomes snake_case
        chunksize=TAMANHO_BLOCO,  # tamanho de cada bloco
    )

    total = 0
    for bloco in leitor:
        # Converte o bloco (DataFrame) em lista de tuplas, formato que o
        # inserir_em_lote (executemany) espera.
        linhas = list(bloco.itertuples(index=False, name=None))
        inserir_em_lote(conexao, sql_insert, linhas)
        total += len(linhas)

    print(f"  {tabela_raw}: {total} linhas carregadas.")


if __name__ == "__main__":
    print("=" * 50)
    print("  FASE 1 - EXTRACAO -> CAMADA RAW")
    print("=" * 50)
    try:
        # Passo a passo: baixar -> descompactar -> carregar cada CSV.
        baixar_zip()
        extrair_zip()

        conexao = conectar()
        try:
            # ARQUIVOS (do config) mapeia cada CSV para sua tabela raw_*.
            for chave, info in ARQUIVOS.items():
                caminho_csv = PASTA_DADOS / info["csv"]
                tabela = info["tabela_raw"]
                print(f"\nCarregando {info['csv']} -> {tabela}")
                colunas = obter_colunas(conexao, tabela)
                carregar_csv_na_raw(conexao, caminho_csv, tabela, colunas)
        finally:
            # Fecha a conexao mesmo se algo falhar no meio do laco.
            conexao.close()

        print("\nFase 1 concluida! Dados brutos carregados na camada Raw.")
    except Exception as erro:
        print(f"\nErro na extracao: {erro}")
        print("Dica: o PostgreSQL esta rodando? O .env e o DRIVE_FILE_ID estao corretos?")
