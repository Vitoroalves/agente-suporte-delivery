"""
Configurações e fixtures do pytest.

Define fixtures reutilizáveis para os testes, incluindo
banco de dados de teste e dados fictícios.
"""

import pytest
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agente.database import DB_PATH


@pytest.fixture
def db_test():
    """
    Fixture que cria um banco de dados de teste em memória.
    
    Cada teste recebe um banco limpo e isolado.
    """
    # Usar banco em memória para testes
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Criar schema
    cursor.execute('''
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            telefone TEXT,
            endereco TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE restaurantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            endereco TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            horario_previsto TIMESTAMP NOT NULL,
            horario_entrega_real TIMESTAMP,
            valor_total REAL NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (restaurante_id) REFERENCES restaurantes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            nome_item TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE reembolsos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            valor REAL NOT NULL,
            motivo TEXT NOT NULL,
            status TEXT NOT NULL,
            data_solicitacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            resumo TEXT NOT NULL,
            status TEXT DEFAULT 'aberto',
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    # Inserir dados de teste básicos
    cursor.execute("INSERT INTO clientes (nome, email, telefone, endereco) VALUES (?, ?, ?, ?)",
                   ("Cliente Teste", "teste@email.com", "11999999999", "Rua Teste, 123"))
    
    cursor.execute("INSERT INTO restaurantes (nome, categoria, endereco) VALUES (?, ?, ?)",
                   ("Restaurante Teste", "Brasileira", "Av. Teste, 456"))
    
    conn.commit()
    
    yield conn
    
    conn.close()


@pytest.fixture
def pedido_preparando(db_test):
    """Fixture que cria um pedido em preparo."""
    cursor = db_test.cursor()
    agora = datetime.now()
    
    cursor.execute(
        """INSERT INTO pedidos (cliente_id, restaurante_id, status, horario_previsto, valor_total)
           VALUES (?, ?, ?, ?, ?)""",
        (1, 1, 'preparando', agora + timedelta(minutes=30), 50.00)
    )
    db_test.commit()
    
    return cursor.lastrowid


@pytest.fixture
def pedido_a_caminho(db_test):
    """Fixture que cria um pedido a caminho."""
    cursor = db_test.cursor()
    agora = datetime.now()
    
    cursor.execute(
        """INSERT INTO pedidos (cliente_id, restaurante_id, status, horario_previsto, valor_total)
           VALUES (?, ?, ?, ?, ?)""",
        (1, 1, 'a_caminho', agora + timedelta(minutes=10), 75.00)
    )
    db_test.commit()
    
    return cursor.lastrowid


@pytest.fixture
def pedido_atrasado(db_test):
    """Fixture que cria um pedido atrasado."""
    cursor = db_test.cursor()
    agora = datetime.now()
    
    cursor.execute(
        """INSERT INTO pedidos (cliente_id, restaurante_id, status, horario_previsto, valor_total)
           VALUES (?, ?, ?, ?, ?)""",
        (1, 1, 'a_caminho', agora - timedelta(minutes=45), 100.00)  # Atrasado 45 min
    )
    db_test.commit()
    
    return cursor.lastrowid


@pytest.fixture
def pedido_entregue(db_test):
    """Fixture que cria um pedido entregue."""
    cursor = db_test.cursor()
    agora = datetime.now()
    
    cursor.execute(
        """INSERT INTO pedidos (cliente_id, restaurante_id, status, horario_previsto, horario_entrega_real, valor_total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (1, 1, 'entregue', agora - timedelta(hours=1), agora - timedelta(minutes=50), 65.00)
    )
    db_test.commit()
    
    return cursor.lastrowid
