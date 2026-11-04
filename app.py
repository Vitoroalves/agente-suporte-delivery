"""
Aplicação Flask - Agente de Suporte para Delivery.

Servidor web que fornece:
- Interface HTML do chat
- API REST para conversação
- Endpoint para listar clientes
"""

import os
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from agente.database import criar_banco, query
from agente.prompts import MENSAGEM_BOAS_VINDAS

# Tentar importar agente real, senão usar demo
try:
    API_KEY = os.getenv('ANTHROPIC_API_KEY')
    if API_KEY and API_KEY != 'sua_chave_aqui':
        from agente.agent import processar_mensagem
        MODO_DEMO = False
        print("✅ Modo: API Anthropic Real")
    else:
        from agente.agent_demo import processar_mensagem_demo as processar_mensagem
        MODO_DEMO = True
        print("🎭 Modo: DEMO (sem API) - Para testes e desenvolvimento")
except Exception:
    from agente.agent_demo import processar_mensagem_demo as processar_mensagem
    MODO_DEMO = True
    print("🎭 Modo: DEMO (sem API) - Para testes e desenvolvimento")

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Configurações
MAX_MENSAGEM_LENGTH = 2000


@app.before_request
def inicializar_banco():
    """Cria o banco de dados na primeira requisição."""
    if not hasattr(app, 'db_initialized'):
        criar_banco()
        app.db_initialized = True


@app.route('/')
def index():
    """Renderiza a página principal do chat."""
    return render_template('index.html')


@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    """
    Lista todos os clientes disponíveis.
    
    Returns:
        JSON com lista de clientes:
        {
            "clientes": [
                {"id": 1, "nome": "Maria Silva", "email": "maria@email.com"},
                ...
            ]
        }
    """
    try:
        clientes = query(
            "SELECT id, nome, email FROM clientes ORDER BY nome"
        )
        
        return jsonify({
            "clientes": clientes
        })
    
    except Exception as e:
        return jsonify({
            "erro": f"Erro ao buscar clientes: {str(e)}"
        }), 500


@app.route('/api/conversar', methods=['POST'])
def conversar():
    """
    Processa uma mensagem do usuário e retorna a resposta do agente.
    
    Request Body:
        {
            "cliente_id": int,
            "mensagem": str
        }
    
    Returns:
        JSON com resposta:
        {
            "resposta": str,
            "ferramentas_usadas": list,
            "erro": str | null
        }
    """
    try:
        # Validar requisição
        data = request.get_json()
        
        if not data:
            return jsonify({
                "erro": "Requisição inválida: JSON esperado"
            }), 400
        
        cliente_id = data.get('cliente_id')
        mensagem = data.get('mensagem')
        
        # Validar campos obrigatórios
        if not cliente_id:
            return jsonify({
                "erro": "Campo 'cliente_id' é obrigatório"
            }), 400
        
        if not mensagem:
            return jsonify({
                "erro": "Campo 'mensagem' é obrigatório"
            }), 400
        
        # Validar tipo e valor
        if not isinstance(cliente_id, int) or cliente_id <= 0:
            return jsonify({
                "erro": "Campo 'cliente_id' deve ser um inteiro positivo"
            }), 400
        
        # Limitar tamanho da mensagem
        if len(mensagem) > MAX_MENSAGEM_LENGTH:
            return jsonify({
                "erro": f"Mensagem muito longa. Máximo: {MAX_MENSAGEM_LENGTH} caracteres"
            }), 400
        
        # Recuperar ou inicializar histórico da sessão
        session_key = f'historico_{cliente_id}'
        historico = session.get(session_key, [])
        
        # Processar mensagem através do agente
        resultado = processar_mensagem(
            cliente_id=cliente_id,
            mensagem_usuario=mensagem,
            historico=historico
        )
        
        # Salvar histórico atualizado na sessão
        session[session_key] = resultado['historico']
        
        # Retornar resposta
        return jsonify({
            "resposta": resultado['resposta'],
            "ferramentas_usadas": resultado.get('ferramentas_usadas', []),
            "erro": resultado.get('erro')
        })
    
    except Exception as e:
        # Log do erro (em produção, usar logging adequado)
        print(f"Erro ao processar conversa: {str(e)}")
        
        return jsonify({
            "resposta": "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
            "ferramentas_usadas": [],
            "erro": "Erro interno do servidor"
        }), 500


@app.route('/api/limpar_historico', methods=['POST'])
def limpar_historico():
    """
    Limpa o histórico de conversa do cliente.
    
    Request Body:
        {
            "cliente_id": int
        }
    
    Returns:
        JSON com confirmação
    """
    try:
        data = request.get_json()
        cliente_id = data.get('cliente_id')
        
        if not cliente_id:
            return jsonify({
                "erro": "Campo 'cliente_id' é obrigatório"
            }), 400
        
        # Limpar histórico da sessão
        session_key = f'historico_{cliente_id}'
        if session_key in session:
            session.pop(session_key)
        
        return jsonify({
            "mensagem": "Histórico limpo com sucesso"
        })
    
    except Exception as e:
        return jsonify({
            "erro": f"Erro ao limpar histórico: {str(e)}"
        }), 500


@app.route('/api/boas_vindas', methods=['GET'])
def boas_vindas():
    """
    Retorna mensagem de boas-vindas do agente.
    
    Returns:
        JSON com mensagem de boas-vindas
    """
    return jsonify({
        "mensagem": MENSAGEM_BOAS_VINDAS
    })


if __name__ == '__main__':
    # Configurações de desenvolvimento
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print("\n" + "="*60)
    print("🚀 NexFood - Agente de Suporte para Delivery")
    print("="*60)
    if MODO_DEMO:
        print("⚠️  MODO DEMO ATIVO (sem API Anthropic)")
        print("   Configure ANTHROPIC_API_KEY no .env para modo real")
        print("-"*60)
    print(f"📍 Servidor rodando em: http://localhost:{port}")
    print(f"🔧 Modo debug: {debug_mode}")
    print("="*60 + "\n")
    
    app.run(debug=debug_mode, port=port, host='0.0.0.0')
