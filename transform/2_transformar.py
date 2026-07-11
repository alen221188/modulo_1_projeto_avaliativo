"""
2_transformar.py
----------------
FASE 2 do pipeline (Transformacao Raw -> Silver).

Le as tabelas raw_* (texto), converte os tipos (texto->DECIMAL, texto->DATE),
calcula colunas derivadas e grava nas tabelas silver_* ja tipadas.
"""

import sys
from pathlib import Path
from datetime import datetime

# Dica de caminho: procurar modulos na RAIZ do projeto (uma pasta acima).
RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from config import TAMANHO_BLOCO
from database.banco import conectar, executar, inserir_em_lote

# ==========================================================================
# FUNCOES DE CONVERSAO 
# ==========================================================================

def converter_decimal(texto):
    """Converte texto com virgula decimal em float. Vazio/invalido -> 0.0."""
    if texto is None:
        return 0.0
    texto = texto.strip()
    if texto == "":
        return 0.0
    # Formato BR: ponto e separador de milhar, virgula e decimal.
    # Ex.: "1.272,97" -> remove "." -> "1272,97" -> troca "," por "." -> "1272.97"
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return 0.0


def converter_data(texto):
    """Converte 'DD/MM/AAAA' em date. Vazio/invalido -> None (NULL no banco)."""
    if texto is None:
        return None
    texto = texto.strip()
    if texto == "":
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def converter_inteiro(texto):
    """Converte texto em int. Vazio/invalido -> None."""
    if texto is None:
        return None
    texto = texto.strip()
    if texto == "":
        return None
    try:
        return int(texto)
    except ValueError:
        return None


# ==========================================================================
# MOTOR DE CARGA (le a raw em blocos e grava na silver)
# ==========================================================================

def carregar_em_blocos(sql_select, sql_insert, converter_linha):
    """
    Le o resultado de sql_select em blocos, aplica converter_linha em cada
    linha e insere na silver via sql_insert. Retorna o total de linhas.
    """
    con_leitura = conectar()   # conexão so para LER da raw
    con_escrita = conectar()   # conexão so para GRAVAR na silver

    cursor = con_leitura.cursor()
    cursor.execute(sql_select)

    total = 0
    while True:
        lote = cursor.fetchmany(TAMANHO_BLOCO)   # pega um a quantidade de linhas
        if not lote:                             # acabou -> sai do laço
            break
        convertidas = [converter_linha(linha) for linha in lote]
        inserir_em_lote(con_escrita, sql_insert, convertidas)
        total += len(convertidas)

    cursor.close()
    con_leitura.close()
    con_escrita.close()
    return total

# ==========================================================================
# SILVER_VIAGEM (a tabela "mae")
# ==========================================================================

# Pegamos so as 16 colunas que a silver_viagem usa (a raw tem outras que
# a silver nao precisa -> aqui e onde a Silver fica "enxuta").
SELECT_VIAGEM = """
    SELECT id_viagem, num_proposta, situacao, viagem_urgente,
           cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
           data_inicio, data_fim, destinos, motivo,
           valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos
    FROM raw_viagem
"""

# 18 colunas: as 16 de cima (ja convertidas) + as 2 calculadas.
INSERT_VIAGEM = """
    INSERT INTO silver_viagem
        (id_viagem, num_proposta, situacao, viagem_urgente,
         cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
         data_inicio, data_fim, destinos, motivo,
         valor_diarias, valor_passagens, valor_devolucao, valor_outros_gastos,
         valor_total, duracao_dias)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def linha_viagem(raw):
    """Converte UMA linha da raw_viagem para o formato da silver_viagem."""
    # 1. "Desempacota" a tupla que veio do banco em variaveis nomeadas.
    (id_viagem, num_proposta, situacao, viagem_urgente,
     cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
     data_inicio_txt, data_fim_txt, destinos, motivo,
     diarias_txt, passagens_txt, devolucao_txt, outros_txt) = raw

    # 2. Converte os campos de data e de valor (texto -> tipo real).
    data_inicio = converter_data(data_inicio_txt)
    data_fim = converter_data(data_fim_txt)
    valor_diarias = converter_decimal(diarias_txt)
    valor_passagens = converter_decimal(passagens_txt)
    valor_devolucao = converter_decimal(devolucao_txt)
    valor_outros = converter_decimal(outros_txt)

    # 3. Coluna calculada: custo total (gastos - devolucao).
    valor_total = valor_diarias + valor_passagens + valor_outros - valor_devolucao

    # 4. Coluna calculada: duracao em dias (so se as duas datas existirem).
    if data_inicio is not None and data_fim is not None:
        duracao_dias = (data_fim - data_inicio).days
    else:
        duracao_dias = None

    # 5. Devolve a linha pronta, na MESMA ordem do INSERT.
    return (id_viagem, num_proposta, situacao, viagem_urgente,
            cod_orgao_superior, nome_orgao_superior, nome_viajante, cargo,
            data_inicio, data_fim, destinos, motivo,
            valor_diarias, valor_passagens, valor_devolucao, valor_outros,
            valor_total, duracao_dias)


# ==========================================================================
# SILVER_PASSAGEM (filha)
# ==========================================================================

SELECT_PASSAGEM = """
    SELECT id_viagem, meio_transporte,
           pais_origem_ida, uf_origem_ida, cidade_origem_ida,
           pais_destino_ida, uf_destino_ida, cidade_destino_ida,
           valor_passagem, taxa_servico, data_emissao
    FROM raw_passagem
"""

INSERT_PASSAGEM = """
    INSERT INTO silver_passagem
        (id_viagem, meio_transporte,
         pais_origem_ida, uf_origem_ida, cidade_origem_ida,
         pais_destino_ida, uf_destino_ida, cidade_destino_ida,
         valor_passagem, taxa_servico, data_emissao)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def linha_passagem(raw):
    """Converte UMA linha da raw_passagem para o formato da silver_passagem."""
    (id_viagem, meio_transporte,
     pais_origem_ida, uf_origem_ida, cidade_origem_ida,
     pais_destino_ida, uf_destino_ida, cidade_destino_ida,
     valor_passagem_txt, taxa_servico_txt, data_emissao_txt) = raw

    return (id_viagem, meio_transporte,
            pais_origem_ida, uf_origem_ida, cidade_origem_ida,
            pais_destino_ida, uf_destino_ida, cidade_destino_ida,
            converter_decimal(valor_passagem_txt),
            converter_decimal(taxa_servico_txt),
            converter_data(data_emissao_txt))


# ==========================================================================
# SILVER_PAGAMENTO
# ==========================================================================

SELECT_PAGAMENTO = """
    SELECT id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
           tipo_pagamento, valor
    FROM raw_pagamento
"""

INSERT_PAGAMENTO = """
    INSERT INTO silver_pagamento
        (id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
         tipo_pagamento, valor)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

def linha_pagamento(raw):
    (id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
    tipo_pagamento, valor) = raw

    return (id_viagem, num_proposta, nome_orgao_pagador, nome_ug_pagadora,
            tipo_pagamento, 
            converter_decimal(valor))
    

# ==========================================================================
# SILVER_TRECHO
# ==========================================================================
 
SELECT_TRECHO = """
    SELECT id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
           destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias
    FROM raw_trecho
"""

INSERT_TRECHO = """
    INSERT INTO silver_trecho
        (id_viagem, sequencia_trecho, origem_data, origem_uf, origem_cidade,
         destino_data, destino_uf, destino_cidade, meio_transporte, numero_diarias)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""
def linha_trecho(raw):
    (id_viagem, sequencia_trecho_txt, origem_data_txt, origem_uf, origem_cidade,
     destino_data_txt, destino_uf, destino_cidade, meio_transporte, numero_diarias_txt) = raw

    return (id_viagem,
            converter_inteiro(sequencia_trecho_txt),
            converter_data(origem_data_txt),
            origem_uf, origem_cidade,
            converter_data(destino_data_txt),
            destino_uf, destino_cidade, meio_transporte,
            converter_decimal(numero_diarias_txt))

# ==========================================================================
# MAESTRO (temporario - por enquanto so a silver_viagem)
# ==========================================================================

if __name__ == "__main__":
    print("Limpando as tabelas silver...")
    con = conectar()
    executar(con, "TRUNCATE silver_viagem, silver_passagem, silver_pagamento, "
                  "silver_trecho RESTART IDENTITY CASCADE;")
    con.close()

    print("Carregando silver_viagem...")
    n = carregar_em_blocos(SELECT_VIAGEM, INSERT_VIAGEM, linha_viagem)
    print(f"silver_viagem: {n} linhas carregadas.")

    print("Carregando silver_passagem...")
    n = carregar_em_blocos(SELECT_PASSAGEM, INSERT_PASSAGEM, linha_passagem)
    print(f"silver_passagem: {n} linhas carregadas.")

    print("Carregando silver_pagamento...")
    n = carregar_em_blocos(SELECT_PAGAMENTO, INSERT_PAGAMENTO, linha_pagamento)
    print(f"silver_pagamento: {n} linhas carregadas.")

    print("Carregando silver_trecho...")
    n = carregar_em_blocos(SELECT_TRECHO, INSERT_TRECHO, linha_trecho)
    print(f"silver_trecho: {n} linhas carregadas.")