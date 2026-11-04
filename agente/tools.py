"""
Ferramentas (tools) do agente de IA.

Define as 5 ferramentas que o agente pode usar para interagir com o sistema:
1. buscar_pedidos_do_cliente: Lista pedidos recentes
2. detalhar_pedido: Detalhes completos de um pedido
3. consultar_politica: Lê políticas da empresa
4. solicitar_reembolso: Processa solicitação de reembolso
5. escalar_para_humano: Cria ticket de atendimento humano

Cada ferramenta valida autorização e entrada antes de executar.
"""

import os
from typing import Any
from agente.database import query, execute
from agente.regras import (
    pedido_pertence_ao_cliente,
    ja_tem_reembolso,
    valor_reembolso_automatico_permitido,
    calcular_valor_pedido
)


# Schemas das ferramentas para a API Anthropic
TOOLS_SCHEMAS = [
    {
        "name": "buscar_pedidos_do_cliente",
        "description": "Busca os pedidos recentes do cliente atual. Use quando o cliente perguntar sobre seus pedidos, status de entrega, ou histórico. Retorna os últimos 5 pedidos.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "detalhar_pedido",
        "description": "Obtém detalhes completos de um pedido específico incluindo status, itens, horários e valor. Use o ID do pedido obtido em buscar_pedidos_do_cliente. IMPORTANTE: Só pode acessar pedidos do cliente atual.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pedido_id": {
                    "type": "integer",
                    "description": "ID do pedido a ser detalhado"
                }
            },
            "required": ["pedido_id"]
        }
    },
    {
        "name": "consultar_politica",
        "description": "Consulta as políticas da empresa sobre atraso, cancelamento, itens errados ou reembolso. Use ANTES de tomar decisões sobre esses tópicos para garantir que você está seguindo as regras corretas.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topico": {
                    "type": "string",
                    "enum": ["atraso", "cancelamento", "item_errado", "reembolso"],
                    "description": "Tópico da política a consultar"
                }
            },
            "required": ["topico"]
        }
    },
    {
        "name": "solicitar_reembolso",
        "description": "Solicita reembolso para um pedido. IMPORTANTE: Sempre peça confirmação do cliente ANTES de usar esta ferramenta. Valores até R$ 30 são aprovados automaticamente, acima disso requerem aprovação humana.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pedido_id": {
                    "type": "integer",
                    "description": "ID do pedido a ser reembolsado"
                },
                "motivo": {
                    "type": "string",
                    "description": "Motivo detalhado do reembolso (ex: 'pedido atrasado 45 minutos', 'item errado: veio X-Bacon em vez de X-Tudo')"
                },
                "valor": {
                    "type": "number",
                    "description": "Valor do reembolso em reais (ex: 25.50)"
                }
            },
            "required": ["pedido_id", "motivo", "valor"]
        }
    },
    {
        "name": "escalar_para_humano",
        "description": "Cria um ticket para atendimento humano. Use quando: cliente pede explicitamente para falar com humano, valor de reembolso está acima do limite, situação não coberta pelas políticas, ou você não tem certeza da resposta.",
        "input_schema": {
            "type": "object",
            "properties": {
                "resumo": {
                    "type": "string",
                    "description": "Resumo detalhado da conversa e do problema do cliente"
                }
            },
            "required": ["resumo"]
        }
    }
]


def executar_ferramenta(nome: str, argumentos: dict, cliente_id: int) -> dict:
    """
    Executa uma ferramenta do agente.
    
    Args:
        nome: Nome da ferramenta
        argumentos: Argumentos da ferramenta
        cliente_id: ID do cliente da sessão (para validação de autorização)
        
    Returns:
        Dicionário com resultado:
        {
            "sucesso": bool,
            "dados": any,
            "erro": str | None
        }
    """
    try:
        if nome == "buscar_pedidos_do_cliente":
            return buscar_pedidos_do_cliente(cliente_id)
        
        elif nome == "detalhar_pedido":
            return detalhar_pedido(argumentos.get("pedido_id"), cliente_id)
        
        elif nome == "consultar_politica":
            return consultar_politica(argumentos.get("topico"))
        
        elif nome == "solicitar_reembolso":
            return solicitar_reembolso(
                argumentos.get("pedido_id"),
                argumentos.get("motivo"),
                argumentos.get("valor"),
                cliente_id
            )
        
        elif nome == "escalar_para_humano":
            return escalar_para_humano(argumentos.get("resumo"), cliente_id)
        
        else:
            return {
                "sucesso": False,
                "dados": None,
                "erro": f"Ferramenta desconhecida: {nome}"
            }
    
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao executar ferramenta: {str(e)}"
        }


def buscar_pedidos_do_cliente(cliente_id: int) -> dict:
    """
    Busca os últimos 5 pedidos do cliente.
    
    Args:
        cliente_id: ID do cliente (da sessão)
        
    Returns:
        Resultado com lista de pedidos
    """
    try:
        pedidos = query("""
            SELECT 
                p.id,
                r.nome as restaurante,
                p.status,
                p.data_pedido,
                p.horario_previsto,
                p.valor_total
            FROM pedidos p
            JOIN restaurantes r ON p.restaurante_id = r.id
            WHERE p.cliente_id = ?
            ORDER BY p.data_pedido DESC
            LIMIT 5
        """, (cliente_id,))
        
        return {
            "sucesso": True,
            "dados": pedidos,
            "erro": None
        }
    
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao buscar pedidos: {str(e)}"
        }


def detalhar_pedido(pedido_id: int, cliente_id: int) -> dict:
    """
    Retorna detalhes completos de um pedido.
    
    VALIDAÇÃO DE SEGURANÇA: Verifica que o pedido pertence ao cliente.
    
    Args:
        pedido_id: ID do pedido
        cliente_id: ID do cliente da sessão
        
    Returns:
        Resultado com detalhes do pedido
    """
    # Validação de entrada
    if not isinstance(pedido_id, int) or pedido_id <= 0:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "ID do pedido inválido"
        }
    
    # VALIDAÇÃO DE AUTORIZAÇÃO
    if not pedido_pertence_ao_cliente(pedido_id, cliente_id):
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Pedido não encontrado ou você não tem permissão para acessá-lo"
        }
    
    try:
        # Buscar dados do pedido
        pedido_info = query("""
            SELECT 
                p.id,
                p.status,
                p.data_pedido,
                p.horario_previsto,
                p.horario_entrega_real,
                p.valor_total,
                r.nome as restaurante,
                r.categoria,
                r.endereco as endereco_restaurante,
                c.endereco as endereco_entrega
            FROM pedidos p
            JOIN restaurantes r ON p.restaurante_id = r.id
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.id = ?
        """, (pedido_id,))
        
        if not pedido_info:
            return {
                "sucesso": False,
                "dados": None,
                "erro": "Pedido não encontrado"
            }
        
        # Buscar itens do pedido
        itens = query("""
            SELECT nome_item, quantidade, preco_unitario
            FROM itens_pedido
            WHERE pedido_id = ?
        """, (pedido_id,))
        
        # Montar resultado
        resultado = pedido_info[0]
        resultado['itens'] = itens
        
        return {
            "sucesso": True,
            "dados": resultado,
            "erro": None
        }
    
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao detalhar pedido: {str(e)}"
        }


def consultar_politica(topico: str) -> dict:
    """
    Busca a política relevante no arquivo data/politicas.md.
    
    Args:
        topico: Tópico a consultar (atraso, cancelamento, item_errado, reembolso)
        
    Returns:
        Resultado com texto da política
    """
    # Validação de entrada
    topicos_validos = ["atraso", "cancelamento", "item_errado", "reembolso"]
    if topico not in topicos_validos:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Tópico inválido. Use um dos seguintes: {', '.join(topicos_validos)}"
        }
    
    try:
        # Caminho do arquivo de políticas
        politicas_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data',
            'politicas.md'
        )
        
        with open(politicas_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Mapear tópico para seção no Markdown
        secoes = {
            "atraso": "## Atraso",
            "cancelamento": "## Cancelamento",
            "item_errado": "## Item Errado",
            "reembolso": "## Reembolso"
        }
        
        # Extrair seção relevante
        inicio_secao = conteudo.find(secoes[topico])
        if inicio_secao == -1:
            return {
                "sucesso": False,
                "dados": None,
                "erro": f"Seção '{topico}' não encontrada no arquivo de políticas"
            }
        
        # Encontrar próxima seção (##) ou fim do arquivo
        proxima_secao = conteudo.find("\n## ", inicio_secao + 1)
        if proxima_secao == -1:
            # Última seção do arquivo
            texto_politica = conteudo[inicio_secao:]
        else:
            texto_politica = conteudo[inicio_secao:proxima_secao]
        
        return {
            "sucesso": True,
            "dados": texto_politica.strip(),
            "erro": None
        }
    
    except FileNotFoundError:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Arquivo de políticas não encontrado"
        }
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao consultar política: {str(e)}"
        }


def solicitar_reembolso(pedido_id: int, motivo: str, valor: float, cliente_id: int) -> dict:
    """
    Solicita reembolso para um pedido.
    
    REGRAS DE NEGÓCIO (aplicadas no código):
    - Valor <= R$ 30: aprovação automática
    - Valor > R$ 30: requer aprovação humana
    - Pedido deve pertencer ao cliente
    - Não permite reembolso duplicado
    
    Args:
        pedido_id: ID do pedido
        motivo: Motivo do reembolso
        valor: Valor do reembolso
        cliente_id: ID do cliente da sessão
        
    Returns:
        Resultado com status da solicitação
    """
    # Validação de entrada
    if not isinstance(pedido_id, int) or pedido_id <= 0:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "ID do pedido inválido"
        }
    
    if not isinstance(valor, (int, float)) or valor <= 0:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Valor do reembolso deve ser maior que zero"
        }
    
    if not motivo or len(motivo) < 10:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Motivo do reembolso deve ter pelo menos 10 caracteres"
        }
    
    # VALIDAÇÃO DE AUTORIZAÇÃO
    if not pedido_pertence_ao_cliente(pedido_id, cliente_id):
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Pedido não encontrado ou você não tem permissão"
        }
    
    # Verificar se já tem reembolso
    if ja_tem_reembolso(pedido_id):
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Este pedido já possui uma solicitação de reembolso"
        }
    
    # Validar valor não excede o pedido
    valor_pedido = calcular_valor_pedido(pedido_id)
    if valor > valor_pedido:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Valor do reembolso (R$ {valor:.2f}) não pode ser maior que o valor do pedido (R$ {valor_pedido:.2f})"
        }
    
    try:
        # REGRA DE NEGÓCIO CRÍTICA
        limite_automatico = valor_reembolso_automatico_permitido()
        
        if valor <= limite_automatico:
            # Aprovação automática
            status = 'aprovado'
            execute(
                """INSERT INTO reembolsos (pedido_id, valor, motivo, status)
                   VALUES (?, ?, ?, ?)""",
                (pedido_id, valor, motivo, status)
            )
            
            return {
                "sucesso": True,
                "dados": {
                    "status": "aprovado",
                    "mensagem": f"Reembolso de R$ {valor:.2f} aprovado automaticamente. O valor será creditado em até 1 dia útil."
                },
                "erro": None
            }
        else:
            # Requer aprovação manual
            status = 'pendente'
            execute(
                """INSERT INTO reembolsos (pedido_id, valor, motivo, status)
                   VALUES (?, ?, ?, ?)""",
                (pedido_id, valor, motivo, status)
            )
            
            return {
                "sucesso": True,
                "dados": {
                    "status": "pendente",
                    "mensagem": f"Reembolso de R$ {valor:.2f} foi registrado e requer aprovação de um supervisor. Você receberá uma resposta em até 3 dias úteis."
                },
                "erro": None
            }
    
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao processar reembolso: {str(e)}"
        }


def escalar_para_humano(resumo: str, cliente_id: int) -> dict:
    """
    Cria um ticket de atendimento humano.
    
    Args:
        resumo: Resumo da conversa e problema
        cliente_id: ID do cliente da sessão
        
    Returns:
        Resultado com número do ticket
    """
    # Validação de entrada
    if not resumo or len(resumo) < 20:
        return {
            "sucesso": False,
            "dados": None,
            "erro": "Resumo deve ter pelo menos 20 caracteres"
        }
    
    try:
        ticket_id = execute(
            """INSERT INTO tickets (cliente_id, resumo, status)
               VALUES (?, ?, 'aberto')""",
            (cliente_id, resumo)
        )
        
        return {
            "sucesso": True,
            "dados": {
                "ticket_id": ticket_id,
                "mensagem": f"Ticket #{ticket_id} criado com sucesso. Um atendente entrará em contato em breve."
            },
            "erro": None
        }
    
    except Exception as e:
        return {
            "sucesso": False,
            "dados": None,
            "erro": f"Erro ao criar ticket: {str(e)}"
        }
