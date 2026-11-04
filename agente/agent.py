"""
Loop principal do agente de IA.

Gerencia a conversação com o modelo Claude e executa ferramentas.
"""

import os
from typing import Optional
from dotenv import load_dotenv
import anthropic

from agente.prompts import SYSTEM_PROMPT
from agente.tools import TOOLS_SCHEMAS, executar_ferramenta

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API
API_KEY = os.getenv('ANTHROPIC_API_KEY')
MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022')

# Limites de segurança
MAX_ITERACOES = 6
MAX_HISTORICO = 20


def processar_mensagem(
    cliente_id: int,
    mensagem_usuario: str,
    historico: Optional[list] = None
) -> dict:
    """
    Processa uma mensagem do usuário através do loop do agente.
    
    Este é o coração do sistema: gerencia a conversa com o LLM,
    executa ferramentas quando solicitado, e retorna a resposta final.
    
    Args:
        cliente_id: ID do cliente da sessão
        mensagem_usuario: Texto enviado pelo usuário
        historico: Lista de mensagens anteriores (opcional)
        
    Returns:
        {
            'resposta': str,              # Resposta final do agente
            'historico': list,            # Histórico atualizado
            'ferramentas_usadas': list,   # Tools chamadas nesta interação
            'erro': str | None            # Mensagem de erro, se houver
        }
    """
    if historico is None:
        historico = []
    
    # Limitar tamanho do histórico
    if len(historico) > MAX_HISTORICO:
        historico = historico[-MAX_HISTORICO:]
    
    # Rastrear ferramentas usadas
    ferramentas_usadas = []
    
    try:
        # Inicializar cliente Anthropic
        client = anthropic.Anthropic(api_key=API_KEY)
        
        # Adicionar mensagem do usuário ao histórico
        historico.append({
            "role": "user",
            "content": mensagem_usuario
        })
        
        # Loop do agente (até MAX_ITERACOES)
        iteracao = 0
        
        while iteracao < MAX_ITERACOES:
            iteracao += 1
            
            # Chamar API Claude
            response = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=historico,
                tools=TOOLS_SCHEMAS
            )
            
            # Adicionar resposta ao histórico
            historico.append({
                "role": "assistant",
                "content": response.content
            })
            
            # Verificar stop_reason
            if response.stop_reason == "end_turn":
                # Resposta final pronta
                resposta_texto = extrair_texto_resposta(response.content)
                
                return {
                    "resposta": resposta_texto,
                    "historico": historico,
                    "ferramentas_usadas": ferramentas_usadas,
                    "erro": None
                }
            
            elif response.stop_reason == "tool_use":
                # Modelo quer usar ferramentas
                tool_results = []
                
                for bloco in response.content:
                    if bloco.type == "tool_use":
                        # Executar ferramenta
                        tool_name = bloco.name
                        tool_input = bloco.input
                        tool_id = bloco.id
                        
                        # Executar ferramenta com validação de segurança
                        resultado = executar_ferramenta(
                            nome=tool_name,
                            argumentos=tool_input,
                            cliente_id=cliente_id
                        )
                        
                        # Registrar ferramenta usada
                        ferramentas_usadas.append({
                            "nome": tool_name,
                            "sucesso": resultado['sucesso']
                        })
                        
                        # Adicionar resultado ao histórico
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": formatar_resultado_tool(resultado)
                        })
                
                # Adicionar resultados das tools ao histórico
                if tool_results:
                    historico.append({
                        "role": "user",
                        "content": tool_results
                    })
                
                # Continuar loop para obter resposta final
                continue
            
            elif response.stop_reason == "max_tokens":
                # Resposta foi truncada
                resposta_texto = extrair_texto_resposta(response.content)
                resposta_texto += "\n\n[Resposta muito longa. Posso continuar?]"
                
                return {
                    "resposta": resposta_texto,
                    "historico": historico,
                    "ferramentas_usadas": ferramentas_usadas,
                    "erro": None
                }
            
            else:
                # Stop reason desconhecido
                break
        
        # Se chegou aqui, atingiu o limite de iterações
        return {
            "resposta": "Desculpe, estou tendo dificuldades para processar sua solicitação. Pode reformular sua pergunta?",
            "historico": historico,
            "ferramentas_usadas": ferramentas_usadas,
            "erro": "Limite de iterações atingido"
        }
    
    except anthropic.APIError as e:
        # Erro da API Anthropic
        return {
            "resposta": "Desculpe, estou com dificuldades técnicas no momento. Tente novamente em instantes.",
            "historico": historico,
            "ferramentas_usadas": ferramentas_usadas,
            "erro": f"Erro da API: {str(e)}"
        }
    
    except anthropic.RateLimitError as e:
        return {
            "resposta": "O sistema está muito ocupado no momento. Por favor, tente novamente em alguns segundos.",
            "historico": historico,
            "ferramentas_usadas": ferramentas_usadas,
            "erro": f"Rate limit: {str(e)}"
        }
    
    except Exception as e:
        # Erro inesperado
        return {
            "resposta": "Ocorreu um erro inesperado. Nossa equipe foi notificada.",
            "historico": historico,
            "ferramentas_usadas": ferramentas_usadas,
            "erro": f"Erro inesperado: {str(e)}"
        }


def extrair_texto_resposta(content: list) -> str:
    """
    Extrai o texto da resposta do modelo.
    
    Args:
        content: Lista de blocos de conteúdo da resposta
        
    Returns:
        Texto concatenado
    """
    textos = []
    for bloco in content:
        if bloco.type == "text":
            textos.append(bloco.text)
    
    return "\n".join(textos)


def formatar_resultado_tool(resultado: dict) -> str:
    """
    Formata o resultado de uma ferramenta para o modelo.
    
    Args:
        resultado: Resultado da execução da ferramenta
        
    Returns:
        String formatada para o modelo
    """
    if resultado['sucesso']:
        # Converter dados para string se necessário
        if isinstance(resultado['dados'], (dict, list)):
            import json
            return json.dumps(resultado['dados'], ensure_ascii=False, indent=2)
        return str(resultado['dados'])
    else:
        # Retornar erro
        return f"ERRO: {resultado['erro']}"
