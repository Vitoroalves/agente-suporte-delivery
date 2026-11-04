"""
Testes do loop do agente.

Testa o comportamento do agente em diferentes cenários,
usando mock da API Anthropic (não faz chamadas reais).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from agente import agent


class MockTextBlock:
    """Mock de um bloco de texto da resposta."""
    def __init__(self, text):
        self.type = "text"
        self.text = text


class MockToolUseBlock:
    """Mock de um bloco de tool_use da resposta."""
    def __init__(self, tool_id, tool_name, tool_input):
        self.type = "tool_use"
        self.id = tool_id
        self.name = tool_name
        self.input = tool_input


class MockResponse:
    """Mock de uma resposta da API Anthropic."""
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason


class TestProcessarMensagem:
    """Testes da função processar_mensagem."""
    
    @patch('agente.agent.anthropic.Anthropic')
    def test_resposta_simples_sem_tools(self, mock_anthropic_class):
        """Deve processar resposta simples sem usar ferramentas."""
        # Mock do cliente e resposta
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MockResponse(
            content=[MockTextBlock("Olá! Como posso ajudar você hoje?")],
            stop_reason="end_turn"
        )
        mock_client.messages.create.return_value = mock_response
        
        # Executar
        resultado = agent.processar_mensagem(
            cliente_id=1,
            mensagem_usuario="Olá",
            historico=[]
        )
        
        # Verificar
        assert resultado['resposta'] == "Olá! Como posso ajudar você hoje?"
        assert resultado['erro'] is None
        assert len(resultado['ferramentas_usadas']) == 0
    
    @patch('agente.agent.anthropic.Anthropic')
    @patch('agente.agent.executar_ferramenta')
    def test_resposta_com_uma_tool(self, mock_exec_tool, mock_anthropic_class):
        """Deve executar uma ferramenta e retornar resposta."""
        # Mock do cliente
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Mock: primeira resposta usa tool, segunda é final
        mock_response_tool = MockResponse(
            content=[
                MockTextBlock("Vou buscar seus pedidos."),
                MockToolUseBlock("tool_1", "buscar_pedidos_do_cliente", {})
            ],
            stop_reason="tool_use"
        )
        
        mock_response_final = MockResponse(
            content=[MockTextBlock("Você tem 2 pedidos: Pedido #1 e Pedido #2")],
            stop_reason="end_turn"
        )
        
        mock_client.messages.create.side_effect = [mock_response_tool, mock_response_final]
        
        # Mock da ferramenta
        mock_exec_tool.return_value = {
            'sucesso': True,
            'dados': [{'id': 1}, {'id': 2}],
            'erro': None
        }
        
        # Executar
        resultado = agent.processar_mensagem(
            cliente_id=1,
            mensagem_usuario="Quais são meus pedidos?",
            historico=[]
        )
        
        # Verificar
        assert "Pedido #1" in resultado['resposta']
        assert resultado['erro'] is None
        assert len(resultado['ferramentas_usadas']) == 1
        assert resultado['ferramentas_usadas'][0]['nome'] == 'buscar_pedidos_do_cliente'
    
    @patch('agente.agent.anthropic.Anthropic')
    def test_limite_de_iteracoes(self, mock_anthropic_class):
        """Deve parar após MAX_ITERACOES."""
        # Mock do cliente que sempre retorna tool_use
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        mock_response = MockResponse(
            content=[MockToolUseBlock("tool_1", "buscar_pedidos_do_cliente", {})],
            stop_reason="tool_use"
        )
        
        # Sempre retornar tool_use (loop infinito)
        mock_client.messages.create.return_value = mock_response
        
        # Executar
        with patch('agente.agent.executar_ferramenta') as mock_exec:
            mock_exec.return_value = {'sucesso': True, 'dados': [], 'erro': None}
            
            resultado = agent.processar_mensagem(
                cliente_id=1,
                mensagem_usuario="Teste",
                historico=[]
            )
        
        # Deve ter parado no limite
        assert resultado['erro'] == "Limite de iterações atingido"
        assert "dificuldades" in resultado['resposta'].lower()
    
    @patch('agente.agent.anthropic.Anthropic')
    def test_erro_api_anthropic(self, mock_anthropic_class):
        """Deve tratar erro da API Anthropic."""
        # Mock que lança erro
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Simular erro genérico
        mock_client.messages.create.side_effect = Exception("Erro de API simulado")
        
        # Executar
        resultado = agent.processar_mensagem(
            cliente_id=1,
            mensagem_usuario="Teste",
            historico=[]
        )
        
        # Deve retornar mensagem amigável
        assert resultado['resposta'] is not None
        assert resultado['erro'] is not None
    
    @patch('agente.agent.anthropic.Anthropic')
    def test_erro_generico(self, mock_anthropic_class):
        """Deve tratar qualquer erro inesperado."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        
        # Simular erro inesperado
        mock_client.messages.create.side_effect = ValueError("Erro inesperado")
        
        # Executar
        resultado = agent.processar_mensagem(
            cliente_id=1,
            mensagem_usuario="Teste",
            historico=[]
        )
        
        # Deve retornar mensagem sobre erro
        assert resultado['resposta'] is not None
        assert resultado['erro'] is not None
    
    def test_limitar_historico(self):
        """Deve limitar tamanho do histórico."""
        # Criar histórico gigante (30 mensagens)
        historico_grande = []
        for i in range(30):
            historico_grande.append({"role": "user", "content": f"Mensagem {i}"})
            historico_grande.append({"role": "assistant", "content": f"Resposta {i}"})
        
        with patch('agente.agent.anthropic.Anthropic') as mock_anthropic_class:
            mock_client = MagicMock()
            mock_anthropic_class.return_value = mock_client
            
            mock_response = MockResponse(
                content=[MockTextBlock("Ok")],
                stop_reason="end_turn"
            )
            mock_client.messages.create.return_value = mock_response
            
            # Executar
            resultado = agent.processar_mensagem(
                cliente_id=1,
                mensagem_usuario="Nova mensagem",
                historico=historico_grande
            )
            
            # Histórico deve ter sido limitado
            # MAX_HISTORICO = 20, mais a nova mensagem e resposta = 22
            assert len(resultado['historico']) <= 22


class TestExtrairTextoResposta:
    """Testes da função extrair_texto_resposta."""
    
    def test_extrair_texto_unico(self):
        """Deve extrair texto de um único bloco."""
        content = [MockTextBlock("Olá, tudo bem?")]
        
        texto = agent.extrair_texto_resposta(content)
        
        assert texto == "Olá, tudo bem?"
    
    def test_extrair_multiplos_textos(self):
        """Deve concatenar múltiplos blocos de texto."""
        content = [
            MockTextBlock("Primeira parte."),
            MockTextBlock("Segunda parte.")
        ]
        
        texto = agent.extrair_texto_resposta(content)
        
        assert "Primeira parte" in texto
        assert "Segunda parte" in texto
    
    def test_ignorar_tool_use_blocks(self):
        """Deve ignorar blocos de tool_use ao extrair texto."""
        content = [
            MockTextBlock("Vou verificar."),
            MockToolUseBlock("tool_1", "buscar_pedidos", {}),
            MockTextBlock("Encontrei seus pedidos.")
        ]
        
        texto = agent.extrair_texto_resposta(content)
        
        assert "Vou verificar" in texto
        assert "Encontrei" in texto
        assert "tool_1" not in texto


class TestFormatarResultadoTool:
    """Testes da função formatar_resultado_tool."""
    
    def test_formatar_resultado_sucesso_dict(self):
        """Deve formatar dicionário como JSON."""
        resultado = {
            'sucesso': True,
            'dados': {'nome': 'Teste', 'valor': 123},
            'erro': None
        }
        
        formatado = agent.formatar_resultado_tool(resultado)
        
        assert '"nome"' in formatado
        assert 'Teste' in formatado
    
    def test_formatar_resultado_sucesso_lista(self):
        """Deve formatar lista como JSON."""
        resultado = {
            'sucesso': True,
            'dados': [1, 2, 3],
            'erro': None
        }
        
        formatado = agent.formatar_resultado_tool(resultado)
        
        assert '[' in formatado
        assert '1' in formatado
    
    def test_formatar_resultado_erro(self):
        """Deve formatar erro."""
        resultado = {
            'sucesso': False,
            'dados': None,
            'erro': 'Pedido não encontrado'
        }
        
        formatado = agent.formatar_resultado_tool(resultado)
        
        assert 'ERRO' in formatado
        assert 'não encontrado' in formatado
