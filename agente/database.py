"""
Módulo de banco de dados SQLite.

Gerencia a conexão e schema do banco de dados do sistema de delivery.
"""

import sqlite3
import os
from typing import Any


# Caminho do banco de dados
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'delivery.db')


def get_connection() -> sqlite3.Connection:
    """
    Retorna uma conexão com o banco de dados.
    
    Configura Row factory para acessar colunas por nome.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn


def query(sql: str, params: tuple = ()) -> list[dict]:
    """
    Executa uma query SELECT e retorna resultados como lista de dicts.
    
    Args:
        sql: Query SQL a ser executada
        params: Parâmetros para a query (usa placeholders ?)
        
    Returns:
        Lista de dicionários com os resultados
        
    Raises:
        sqlite3.Error: Em caso de erro no banco
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        # Converter Rows em dicts
        rows = cursor.fetchall()
        resultado = [dict(row) for row in rows]
        
        conn.close()
        return resultado
        
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Erro ao executar query: {e}")


def execute(sql: str, params: tuple = ()) -> int:
    """
    Executa um comando INSERT, UPDATE ou DELETE.
    
    Args:
        sql: Comando SQL a ser executado
        params: Parâmetros para o comando
        
    Returns:
        ID da última linha inserida (para INSERTs) ou número de linhas afetadas
        
    Raises:
        sqlite3.Error: Em caso de erro no banco
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        
        last_id = cursor.lastrowid
        conn.close()
        
        return last_id
        
    except sqlite3.Error as e:
        raise sqlite3.Error(f"Erro ao executar comando: {e}")


def criar_banco():
    """
    Cria o schema do banco de dados se ele não existir.
    
    Define todas as tabelas necessárias para o sistema:
    - clientes: dados dos clientes
    - restaurantes: dados dos restaurantes
    - pedidos: pedidos realizados
    - itens_pedido: itens de cada pedido
    - reembolsos: solicitações de reembolso
    - tickets: escalações para atendimento humano
    """
    
    # Criar diretório data se não existir
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Se o banco já existe, não recriar
    if os.path.exists(DB_PATH):
        print(f"Banco de dados já existe: {DB_PATH}")
        return
    
    print(f"Criando banco de dados: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela: clientes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT,
            endereco TEXT NOT NULL
        )
    ''')
    
    # Tabela: restaurantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS restaurantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            endereco TEXT
        )
    ''')
    
    # Tabela: pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('preparando', 'a_caminho', 'entregue', 'cancelado')),
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            horario_previsto TIMESTAMP NOT NULL,
            horario_entrega_real TIMESTAMP,
            valor_total REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (restaurante_id) REFERENCES restaurantes(id)
        )
    ''')
    
    # Tabela: itens_pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            nome_item TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    ''')
    
    # Tabela: reembolsos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reembolsos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            valor REAL NOT NULL,
            motivo TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('aprovado', 'pendente', 'recusado')),
            data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    ''')
    
    # Tabela: tickets (para escalação)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            resumo TEXT NOT NULL,
            status TEXT DEFAULT 'aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    # Índices para performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedidos_cliente ON pedidos(cliente_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reembolsos_pedido ON reembolsos(pedido_id)')
    
    conn.commit()
    conn.close()
    
    print("✅ Banco de dados criado com sucesso!")


if __name__ == '__main__':
    # Criar banco ao executar o módulo diretamente
    criar_banco()
