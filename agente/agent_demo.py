"""
Agente em modo demonstração (sem API Anthropic).

Simula o comportamento do agente usando regras simples e respostas pré-programadas.
Útil para demonstrações, desenvolvimento e testes da interface.
"""

import random
from agente.tools import executar_ferramenta


def processar_mensagem_demo(cliente_id: int, mensagem_usuario: str, historico: list = None) -> dict:
    """
    Processa mensagem em modo demo (sem chamar API real).
    
    Simula o comportamento do agente usando detecção de palavras-chave
    e respostas pré-programadas.
    """
    if historico is None:
        historico = []
    
    # Adicionar mensagem do usuário
    historico.append({
        "role": "user",
        "content": mensagem_usuario
    })
    
    mensagem_lower = mensagem_usuario.lower()
    ferramentas_usadas = []
    
    # Detectar intenção e gerar resposta
    if any(palavra in mensagem_lower for palavra in ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite']):
        resposta = "Olá! Sou o Alex, assistente virtual do NexFood. Como posso ajudar você hoje?"
    
    elif any(palavra in mensagem_lower for palavra in ['onde', 'status', 'cadê', 'rastrear', 'acompanhar']):
        # Simular busca de pedidos
        resultado_pedidos = executar_ferramenta('buscar_pedidos_do_cliente', {}, cliente_id)
        ferramentas_usadas.append({'nome': 'buscar_pedidos_do_cliente', 'sucesso': True})
        
        if resultado_pedidos['sucesso'] and resultado_pedidos['dados']:
            pedidos = resultado_pedidos['dados']
            if len(pedidos) > 0:
                p = pedidos[0]
                resposta = f"Encontrei seus pedidos! O mais recente é do restaurante {p['restaurante']} "
                resposta += f"com status '{p['status']}'. "
                
                if p['status'] == 'preparando':
                    resposta += "Seu pedido está sendo preparado no restaurante."
                elif p['status'] == 'a_caminho':
                    resposta += "Seu pedido já saiu para entrega!"
                elif p['status'] == 'entregue':
                    resposta += "Este pedido já foi entregue."
                
                resposta += f"\n\nQuer mais detalhes sobre o pedido #{p['id']}?"
            else:
                resposta = "Você ainda não tem pedidos registrados."
        else:
            resposta = "Não consegui buscar seus pedidos. Tente novamente."
    
    elif 'detalhes' in mensagem_lower or 'detalhar' in mensagem_lower or any(f'#{i}' in mensagem_lower or f'pedido {i}' in mensagem_lower for i in range(1, 100)):
        # Tentar extrair ID do pedido
        import re
        match = re.search(r'#?(\d+)', mensagem_usuario)
        if match:
            pedido_id = int(match.group(1))
            resultado = executar_ferramenta('detalhar_pedido', {'pedido_id': pedido_id}, cliente_id)
            ferramentas_usadas.append({'nome': 'detalhar_pedido', 'sucesso': resultado['sucesso']})
            
            if resultado['sucesso']:
                p = resultado['dados']
                resposta = f"📦 Detalhes do Pedido #{p['id']}:\n\n"
                resposta += f"🍽️ Restaurante: {p['restaurante']}\n"
                resposta += f"📍 Status: {p['status']}\n"
                resposta += f"💰 Valor: R$ {p['valor_total']:.2f}\n\n"
                resposta += "🛍️ Itens:\n"
                for item in p['itens']:
                    resposta += f"  • {item['quantidade']}x {item['nome_item']} - R$ {item['preco_unitario']:.2f}\n"
            else:
                resposta = "Não consegui acessar esse pedido. Verifique se o número está correto."
        else:
            resposta = "Por favor, me diga o número do pedido que quer ver (ex: #1, pedido 2)"
    
    elif any(palavra in mensagem_lower for palavra in ['atrasado', 'atraso', 'demora', 'demorou']):
        # Consultar política de atraso
        resultado = executar_ferramenta('consultar_politica', {'topico': 'atraso'}, cliente_id)
        ferramentas_usadas.append({'nome': 'consultar_politica', 'sucesso': True})
        
        resposta = "Entendo sua preocupação com o atraso. Vou verificar suas opções.\n\n"
        resposta += "De acordo com nossa política:\n"
        resposta += "• Até 30 min de atraso: cupom de R$ 10 no próximo pedido\n"
        resposta += "• 30-60 min: reembolso parcial de R$ 20\n"
        resposta += "• Acima de 60 min: reembolso total\n\n"
        resposta += "Qual pedido está atrasado? Me diga o número para eu verificar."
    
    elif any(palavra in mensagem_lower for palavra in ['cancelar', 'cancela', 'desistir']):
        # Consultar política de cancelamento
        resultado = executar_ferramenta('consultar_politica', {'topico': 'cancelamento'}, cliente_id)
        ferramentas_usadas.append({'nome': 'consultar_politica', 'sucesso': True})
        
        resposta = "Vou verificar se é possível cancelar seu pedido.\n\n"
        resposta += "📋 Nossa política de cancelamento:\n"
        resposta += "✅ Pode cancelar: pedidos em preparo\n"
        resposta += "❌ Não pode cancelar: pedidos a caminho ou entregues\n\n"
        resposta += "Me informe o número do pedido que deseja cancelar."
    
    elif any(palavra in mensagem_lower for palavra in ['reembolso', 'reembolsar', 'devolver', 'dinheiro de volta']):
        resposta = "Entendo que você quer um reembolso. "
        resposta += "Qual o motivo? (atraso, item errado, cancelamento, outro)\n\n"
        resposta += "E qual pedido? Me informe o número."
    
    elif any(palavra in mensagem_lower for palavra in ['errado', 'faltou', 'faltando', 'diferente']):
        # Consultar política de item errado
        resultado = executar_ferramenta('consultar_politica', {'topico': 'item_errado'}, cliente_id)
        ferramentas_usadas.append({'nome': 'consultar_politica', 'sucesso': True})
        
        resposta = "Que chato que seu pedido veio errado! Vamos resolver isso.\n\n"
        resposta += "📋 Opções:\n"
        resposta += "• Item faltando: reembolso proporcional\n"
        resposta += "• Item errado: reembolso + R$ 10 de compensação\n\n"
        resposta += "Me confirme: qual pedido e o que veio errado?"
    
    elif 'sim' in mensagem_lower or 'confirmo' in mensagem_lower or 'pode' in mensagem_lower:
        resposta = "Ótimo! Estou processando sua solicitação... ⚙️\n\n"
        resposta += "[Em modo demo, a ação seria executada aqui]\n\n"
        resposta += "Há algo mais em que posso ajudar?"
    
    elif any(palavra in mensagem_lower for palavra in ['humano', 'atendente', 'pessoa', 'operador']):
        ferramentas_usadas.append({'nome': 'escalar_para_humano', 'sucesso': True})
        resposta = "Claro! Vou transferir você para um atendente humano.\n\n"
        resposta += "📞 Ticket #42 criado com sucesso!\n"
        resposta += "Um atendente entrará em contato em breve."
    
    elif any(palavra in mensagem_lower for palavra in ['obrigado', 'obrigada', 'valeu', 'thanks']):
        resposta = "Por nada! Fico feliz em ajudar. 😊\n\nSe precisar de mais alguma coisa, é só chamar!"
    
    elif any(palavra in mensagem_lower for palavra in ['tchau', 'até', 'falou']):
        resposta = "Até logo! Bom apetite! 🍔🍕"
    
    else:
        # Resposta genérica
        respostas_genericas = [
            "Desculpe, não entendi bem. Você pode reformular?\n\nPosso ajudar com:\n• Status de pedidos\n• Cancelamentos\n• Reembolsos\n• Problemas com entregas",
            "Não tenho certeza do que você precisa. Tente perguntar sobre:\n• Onde está meu pedido?\n• Quero cancelar\n• Meu pedido atrasou\n• Item veio errado",
            "Hmm, não consegui entender. Me conte: qual problema você está tendo com seu pedido?"
        ]
        resposta = random.choice(respostas_genericas)
    
    # Adicionar resposta ao histórico
    historico.append({
        "role": "assistant",
        "content": resposta
    })
    
    return {
        "resposta": resposta,
        "historico": historico,
        "ferramentas_usadas": ferramentas_usadas,
        "erro": None
    }
