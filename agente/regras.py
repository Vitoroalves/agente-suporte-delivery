"""
Módulo de regras de negócio do sistema.

Centraliza a lógica de validação e cálculos relacionados a pedidos,
reembolsos e cancelamentos. Estas funções são usadas pelas ferramentas
do agente para garantir que as regras sejam aplicadas corretamente.
"""

from datetime import datetime
from agente.database import query


def pedido_pertence_ao_cliente(pedido_id: int, cliente_id: int) -> bool:
    """
    Verifica se um pedido pertence a um cliente específico.
    
    Esta é uma validação crítica de segurança que deve ser feita
    antes de qualquer operação sobre um pedido.
    
    Args:
        pedido_id: ID do pedido a verificar
        cliente_id: ID do cliente da sessão
        
    Returns:
        True se o pedido pertence ao cliente, False caso contrário
    """
    resultado = query(
        "SELECT id FROM pedidos WHERE id = ? AND cliente_id = ?",
        (pedido_id, cliente_id)
    )
    return len(resultado) > 0


def pedido_esta_atrasado(pedido_id: int) -> bool:
    """
    Verifica se um pedido está atrasado.
    
    Um pedido é considerado atrasado quando:
    - Ainda não foi entregue (horario_entrega_real é NULL)
    - O horário previsto já passou
    
    Args:
        pedido_id: ID do pedido a verificar
        
    Returns:
        True se o pedido está atrasado, False caso contrário
    """
    resultado = query(
        "SELECT horario_previsto, horario_entrega_real FROM pedidos WHERE id = ?",
        (pedido_id,)
    )
    
    if not resultado:
        return False
    
    pedido = resultado[0]
    
    # Se já foi entregue, não está atrasado
    if pedido['horario_entrega_real']:
        return False
    
    # Comparar horário previsto com horário atual
    horario_previsto = datetime.fromisoformat(pedido['horario_previsto'])
    agora = datetime.now()
    
    return agora > horario_previsto


def pode_cancelar_pedido(pedido_id: int) -> tuple[bool, str]:
    """
    Verifica se um pedido pode ser cancelado.
    
    Regras de cancelamento (conforme políticas):
    - Pedido em status "preparando": pode cancelar
    - Pedidos "a_caminho", "entregue" ou "cancelado": não pode cancelar
    
    Args:
        pedido_id: ID do pedido a verificar
        
    Returns:
        Tupla (pode_cancelar, motivo)
        - pode_cancelar: True se pode cancelar, False caso contrário
        - motivo: Explicação do resultado
    """
    resultado = query(
        "SELECT status FROM pedidos WHERE id = ?",
        (pedido_id,)
    )
    
    if not resultado:
        return False, "Pedido não encontrado"
    
    status = resultado[0]['status']
    
    if status == 'preparando':
        return True, "Pedido pode ser cancelado pois ainda está em preparo"
    elif status == 'a_caminho':
        return False, "Pedido já saiu para entrega e não pode ser cancelado"
    elif status == 'entregue':
        return False, "Pedido já foi entregue e não pode ser cancelado"
    elif status == 'cancelado':
        return False, "Pedido já foi cancelado anteriormente"
    else:
        return False, f"Status desconhecido: {status}"


def ja_tem_reembolso(pedido_id: int) -> bool:
    """
    Verifica se já existe um reembolso solicitado para um pedido.
    
    Evita reembolsos duplicados para o mesmo pedido.
    
    Args:
        pedido_id: ID do pedido a verificar
        
    Returns:
        True se já existe reembolso, False caso contrário
    """
    resultado = query(
        "SELECT id FROM reembolsos WHERE pedido_id = ?",
        (pedido_id,)
    )
    return len(resultado) > 0


def calcular_valor_pedido(pedido_id: int) -> float:
    """
    Calcula o valor total de um pedido.
    
    Útil para validar valores de reembolso e garantir que não excedam
    o valor do pedido.
    
    Args:
        pedido_id: ID do pedido
        
    Returns:
        Valor total do pedido, ou 0.0 se não encontrado
    """
    resultado = query(
        "SELECT valor_total FROM pedidos WHERE id = ?",
        (pedido_id,)
    )
    
    if not resultado:
        return 0.0
    
    return float(resultado[0]['valor_total'])


def calcular_minutos_atraso(pedido_id: int) -> int:
    """
    Calcula quantos minutos um pedido está atrasado.
    
    Útil para determinar compensação baseada no tempo de atraso.
    
    Args:
        pedido_id: ID do pedido
        
    Returns:
        Número de minutos de atraso, ou 0 se não está atrasado
    """
    resultado = query(
        "SELECT horario_previsto, horario_entrega_real FROM pedidos WHERE id = ?",
        (pedido_id,)
    )
    
    if not resultado:
        return 0
    
    pedido = resultado[0]
    
    # Se já foi entregue, não está atrasado
    if pedido['horario_entrega_real']:
        return 0
    
    horario_previsto = datetime.fromisoformat(pedido['horario_previsto'])
    agora = datetime.now()
    
    if agora <= horario_previsto:
        return 0  # Não está atrasado
    
    diferenca = agora - horario_previsto
    return int(diferenca.total_seconds() / 60)


def valor_reembolso_automatico_permitido() -> float:
    """
    Retorna o valor máximo para aprovação automática de reembolso.
    
    REGRA CRÍTICA: Reembolsos até este valor são aprovados automaticamente.
    Acima deste valor, requerem aprovação humana.
    
    Returns:
        Valor máximo para aprovação automática (R$ 30.00)
    """
    return 30.0
