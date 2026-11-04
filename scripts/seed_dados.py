"""
Script para popular o banco de dados com dados fictícios.

Cria clientes, restaurantes, pedidos e itens para testes.
Inclui cenários variados: pedidos atrasados, entregues, em andamento, etc.
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agente.database import criar_banco, execute, get_connection


def limpar_dados():
    """Remove todos os dados do banco (mantém o schema)."""
    print("🧹 Limpando dados existentes...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Ordem importa por causa das foreign keys
    cursor.execute("DELETE FROM tickets")
    cursor.execute("DELETE FROM reembolsos")
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM restaurantes")
    cursor.execute("DELETE FROM clientes")
    
    conn.commit()
    conn.close()
    
    print("✅ Dados limpos!")


def seed_clientes():
    """Cria clientes fictícios."""
    print("👥 Criando clientes...")
    
    clientes = [
        ("Maria Silva", "maria.silva@email.com", "(11) 98765-4321", "Rua das Flores, 123 - São Paulo, SP"),
        ("João Santos", "joao.santos@email.com", "(21) 99876-5432", "Av. Atlântica, 456 - Rio de Janeiro, RJ"),
        ("Ana Costa", "ana.costa@email.com", "(85) 97654-3210", "Rua do Sol, 789 - Fortaleza, CE"),
        ("Pedro Oliveira", "pedro.oliveira@email.com", "(11) 96543-2109", "Alameda Santos, 321 - São Paulo, SP"),
    ]
    
    for nome, email, telefone, endereco in clientes:
        execute(
            "INSERT INTO clientes (nome, email, telefone, endereco) VALUES (?, ?, ?, ?)",
            (nome, email, telefone, endereco)
        )
    
    print(f"✅ {len(clientes)} clientes criados!")


def seed_restaurantes():
    """Cria restaurantes fictícios."""
    print("🍽️  Criando restaurantes...")
    
    restaurantes = [
        ("Pizzaria Bella Napoli", "Italiana", "Rua Giuseppe Verdi, 100"),
        ("Sushi Master", "Japonesa", "Av. Japão, 250"),
        ("Burger House", "Hamburgueria", "Rua dos Lanches, 50"),
        ("Cantina da Nonna", "Italiana", "Rua Roma, 80"),
        ("Taco Loco", "Mexicana", "Av. México, 150"),
        ("Saudável & Cia", "Saudável", "Rua Fitness, 200"),
        ("Churrascaria Gaúcha", "Churrascaria", "Av. Pampa, 300"),
    ]
    
    for nome, categoria, endereco in restaurantes:
        execute(
            "INSERT INTO restaurantes (nome, categoria, endereco) VALUES (?, ?, ?)",
            (nome, categoria, endereco)
        )
    
    print(f"✅ {len(restaurantes)} restaurantes criados!")


def seed_pedidos():
    """Cria pedidos fictícios com cenários variados."""
    print("📦 Criando pedidos...")
    
    agora = datetime.now()
    
    # Pedidos de diferentes clientes e com diferentes status
    pedidos = [
        # Pedidos da Maria (cliente_id=1)
        {
            "cliente_id": 1,
            "restaurante_id": 1,
            "status": "entregue",
            "data_pedido": agora - timedelta(hours=3),
            "horario_previsto": agora - timedelta(hours=2, minutes=30),
            "horario_entrega_real": agora - timedelta(hours=2, minutes=20),
            "valor_total": 65.90,
            "itens": [
                ("Pizza Margherita", 1, 45.90),
                ("Refrigerante 2L", 1, 12.00),
                ("Tiramisu", 1, 8.00),
            ]
        },
        {
            "cliente_id": 1,
            "restaurante_id": 2,
            "status": "a_caminho",
            "data_pedido": agora - timedelta(minutes=50),
            "horario_previsto": agora - timedelta(minutes=20),  # ATRASADO!
            "horario_entrega_real": None,
            "valor_total": 89.50,
            "itens": [
                ("Combo Sushi 20 peças", 1, 75.00),
                ("Harumaki", 1, 14.50),
            ]
        },
        {
            "cliente_id": 1,
            "restaurante_id": 3,
            "status": "preparando",
            "data_pedido": agora - timedelta(minutes=15),
            "horario_previsto": agora + timedelta(minutes=25),
            "horario_entrega_real": None,
            "valor_total": 42.00,
            "itens": [
                ("X-Bacon", 1, 28.00),
                ("Batata Frita Grande", 1, 14.00),
            ]
        },
        
        # Pedidos do João (cliente_id=2)
        {
            "cliente_id": 2,
            "restaurante_id": 4,
            "status": "entregue",
            "data_pedido": agora - timedelta(days=1),
            "horario_previsto": agora - timedelta(days=1) + timedelta(minutes=40),
            "horario_entrega_real": agora - timedelta(days=1) + timedelta(minutes=38),
            "valor_total": 78.50,
            "itens": [
                ("Lasanha Bolonhesa", 1, 42.00),
                ("Salada Caesar", 1, 24.50),
                ("Coca-Cola Lata", 1, 6.00),
                ("Brownie", 1, 6.00),
            ]
        },
        {
            "cliente_id": 2,
            "restaurante_id": 5,
            "status": "a_caminho",
            "data_pedido": agora - timedelta(hours=1, minutes=20),
            "horario_previsto": agora - timedelta(minutes=30),  # ATRASADO!
            "horario_entrega_real": None,
            "valor_total": 54.90,
            "itens": [
                ("Burrito Especial", 2, 22.00),
                ("Nachos com Guacamole", 1, 10.90),
            ]
        },
        {
            "cliente_id": 2,
            "restaurante_id": 6,
            "status": "cancelado",
            "data_pedido": agora - timedelta(hours=2),
            "horario_previsto": agora - timedelta(hours=1, minutes=30),
            "horario_entrega_real": None,
            "valor_total": 35.00,
            "itens": [
                ("Salada Completa", 1, 28.00),
                ("Suco Natural", 1, 7.00),
            ]
        },
        
        # Pedidos da Ana (cliente_id=3)
        {
            "cliente_id": 3,
            "restaurante_id": 1,
            "status": "entregue",
            "data_pedido": agora - timedelta(hours=5),
            "horario_previsto": agora - timedelta(hours=4, minutes=20),
            "horario_entrega_real": agora - timedelta(hours=4, minutes=15),
            "valor_total": 95.80,
            "itens": [
                ("Pizza Quatro Queijos", 1, 52.00),
                ("Pizza Calabresa", 1, 43.80),
            ]
        },
        {
            "cliente_id": 3,
            "restaurante_id": 7,
            "status": "a_caminho",
            "data_pedido": agora - timedelta(minutes=45),
            "horario_previsto": agora + timedelta(minutes=5),  # No prazo
            "horario_entrega_real": None,
            "valor_total": 125.00,
            "itens": [
                ("Picanha 500g", 1, 95.00),
                ("Farofa", 1, 12.00),
                ("Vinagrete", 1, 8.00),
                ("Refrigerante 2L", 1, 10.00),
            ]
        },
        {
            "cliente_id": 3,
            "restaurante_id": 2,
            "status": "preparando",
            "data_pedido": agora - timedelta(minutes=10),
            "horario_previsto": agora + timedelta(minutes=30),
            "horario_entrega_real": None,
            "valor_total": 58.00,
            "itens": [
                ("Temaki Salmão", 2, 24.00),
                ("Hot Roll", 1, 10.00),
            ]
        },
        
        # Pedidos do Pedro (cliente_id=4)
        {
            "cliente_id": 4,
            "restaurante_id": 3,
            "status": "entregue",
            "data_pedido": agora - timedelta(days=2),
            "horario_previsto": agora - timedelta(days=2) + timedelta(minutes=35),
            "horario_entrega_real": agora - timedelta(days=2) + timedelta(minutes=32),
            "valor_total": 38.50,
            "itens": [
                ("X-Tudo", 1, 32.00),
                ("Onion Rings", 1, 6.50),
            ]
        },
        {
            "cliente_id": 4,
            "restaurante_id": 5,
            "status": "preparando",
            "data_pedido": agora - timedelta(minutes=8),
            "horario_previsto": agora + timedelta(minutes=32),
            "horario_entrega_real": None,
            "valor_total": 67.80,
            "itens": [
                ("Quesadilla", 2, 18.00),
                ("Tacos", 3, 8.00),
                ("Guacamole", 1, 7.80),
            ]
        },
        {
            "cliente_id": 4,
            "restaurante_id": 6,
            "status": "a_caminho",
            "data_pedido": agora - timedelta(minutes=35),
            "horario_previsto": agora + timedelta(minutes=5),
            "horario_entrega_real": None,
            "valor_total": 45.00,
            "itens": [
                ("Poke Bowl", 1, 38.00),
                ("Água de Coco", 1, 7.00),
            ]
        },
        
        # Mais alguns pedidos antigos entregues
        {
            "cliente_id": 1,
            "restaurante_id": 7,
            "status": "entregue",
            "data_pedido": agora - timedelta(days=3),
            "horario_previsto": agora - timedelta(days=3) + timedelta(minutes=50),
            "horario_entrega_real": agora - timedelta(days=3) + timedelta(minutes=48),
            "valor_total": 180.00,
            "itens": [
                ("Rodízio de Carnes", 2, 85.00),
                ("Refrigerante 2L", 1, 10.00),
            ]
        },
        {
            "cliente_id": 2,
            "restaurante_id": 1,
            "status": "entregue",
            "data_pedido": agora - timedelta(days=5),
            "horario_previsto": agora - timedelta(days=5) + timedelta(minutes=40),
            "horario_entrega_real": agora - timedelta(days=5) + timedelta(minutes=35),
            "valor_total": 51.90,
            "itens": [
                ("Pizza Portuguesa", 1, 47.90),
                ("Guaraná Lata", 1, 4.00),
            ]
        },
        {
            "cliente_id": 3,
            "restaurante_id": 3,
            "status": "entregue",
            "data_pedido": agora - timedelta(days=7),
            "horario_previsto": agora - timedelta(days=7) + timedelta(minutes=30),
            "horario_entrega_real": agora - timedelta(days=7) + timedelta(minutes=28),
            "valor_total": 56.00,
            "itens": [
                ("Combo Burger Duplo", 1, 45.00),
                ("Milkshake", 1, 11.00),
            ]
        },
    ]
    
    for pedido_data in pedidos:
        # Inserir pedido
        pedido_id = execute(
            """INSERT INTO pedidos 
               (cliente_id, restaurante_id, status, data_pedido, horario_previsto, horario_entrega_real, valor_total)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                pedido_data["cliente_id"],
                pedido_data["restaurante_id"],
                pedido_data["status"],
                pedido_data["data_pedido"],
                pedido_data["horario_previsto"],
                pedido_data["horario_entrega_real"],
                pedido_data["valor_total"],
            )
        )
        
        # Inserir itens do pedido
        for nome_item, quantidade, preco in pedido_data["itens"]:
            execute(
                "INSERT INTO itens_pedido (pedido_id, nome_item, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, nome_item, quantidade, preco)
            )
    
    print(f"✅ {len(pedidos)} pedidos criados com seus itens!")


def main():
    """Executa o seed completo."""
    print("\n🌱 Iniciando seed do banco de dados...\n")
    
    # Criar banco se não existir
    criar_banco()
    
    # Limpar dados existentes
    limpar_dados()
    
    # Popular tabelas
    seed_clientes()
    seed_restaurantes()
    seed_pedidos()
    
    print("\n✅ Seed concluído com sucesso! 🎉\n")
    print("📊 Resumo:")
    print("   - 4 clientes")
    print("   - 7 restaurantes")
    print("   - 15 pedidos (com status variados)")
    print("   - 2 pedidos atrasados para testes")
    print("   - Múltiplos itens por pedido")
    print("\n💡 Agora você pode iniciar a aplicação!\n")


if __name__ == '__main__':
    main()
