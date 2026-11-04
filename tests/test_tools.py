"""
Testes das ferramentas do agente.

Valida que todas as 5 ferramentas funcionam corretamente,
incluindo validações de segurança e regras de negócio.
"""

import pytest
from unittest.mock import patch, mock_open
from agente import tools


class TestBuscarPedidosDoCliente:
    """Testes da ferramenta buscar_pedidos_do_cliente."""
    
    def test_buscar_pedidos_sucesso(self):
        """Deve retornar lista de pedidos do cliente."""
        pedidos_mock = [
            {'id': 1, 'restaurante': 'Pizzaria', 'status': 'entregue', 'valor_total': 50.0},
            {'id': 2, 'restaurante': 'Sushi', 'status': 'a_caminho', 'valor_total': 80.0}
        ]
        
        with patch('agente.tools.query') as mock_query:
            mock_query.return_value = pedidos_mock
            
            resultado = tools.buscar_pedidos_do_cliente(cliente_id=1)
            
            assert resultado['sucesso'] is True
            assert len(resultado['dados']) == 2
            assert resultado['erro'] is None
    
    def test_buscar_pedidos_vazio(self):
        """Deve retornar lista vazia se cliente não tem pedidos."""
        with patch('agente.tools.query') as mock_query:
            mock_query.return_value = []
            
            resultado = tools.buscar_pedidos_do_cliente(cliente_id=999)
            
            assert resultado['sucesso'] is True
            assert resultado['dados'] == []


class TestDetalharPedido:
    """Testes da ferramenta detalhar_pedido."""
    
    def test_detalhar_pedido_autorizado(self):
        """Deve retornar detalhes quando pedido pertence ao cliente."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = True
            
            with patch('agente.tools.query') as mock_query:
                mock_query.side_effect = [
                    [{'id': 1, 'status': 'entregue', 'valor_total': 50.0}],  # pedido
                    [{'nome_item': 'Pizza', 'quantidade': 1, 'preco_unitario': 50.0}]  # itens
                ]
                
                resultado = tools.detalhar_pedido(pedido_id=1, cliente_id=1)
                
                assert resultado['sucesso'] is True
                assert resultado['dados']['id'] == 1
                assert 'itens' in resultado['dados']
    
    def test_detalhar_pedido_nao_autorizado(self):
        """Deve bloquear acesso a pedido de outro cliente."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = False
            
            resultado = tools.detalhar_pedido(pedido_id=999, cliente_id=1)
            
            assert resultado['sucesso'] is False
            assert 'permissão' in resultado['erro'].lower()
    
    def test_detalhar_pedido_id_invalido(self):
        """Deve rejeitar ID inválido."""
        resultado = tools.detalhar_pedido(pedido_id=-1, cliente_id=1)
        
        assert resultado['sucesso'] is False
        assert 'inválido' in resultado['erro'].lower()


class TestConsultarPolitica:
    """Testes da ferramenta consultar_politica."""
    
    def test_consultar_politica_atraso(self):
        """Deve retornar política de atraso."""
        conteudo_mock = """
# Políticas

## Atraso

Pedidos atrasados recebem compensação.

## Cancelamento

Pode cancelar em preparo.
"""
        
        with patch('builtins.open', mock_open(read_data=conteudo_mock)):
            resultado = tools.consultar_politica(topico='atraso')
            
            assert resultado['sucesso'] is True
            assert 'Atraso' in resultado['dados']
            assert 'compensação' in resultado['dados']
    
    def test_consultar_politica_topico_invalido(self):
        """Deve rejeitar tópico inválido."""
        resultado = tools.consultar_politica(topico='invalido')
        
        assert resultado['sucesso'] is False
        assert 'inválido' in resultado['erro'].lower()
    
    @pytest.mark.parametrize("topico", ["atraso", "cancelamento", "item_errado", "reembolso"])
    def test_consultar_politica_todos_topicos_validos(self, topico):
        """Deve aceitar todos os tópicos válidos."""
        conteudo_mock = f"""
## {topico.replace('_', ' ').title()}

Conteúdo da política.

## Outra Seção

Outro conteúdo.
"""
        
        with patch('builtins.open', mock_open(read_data=conteudo_mock)):
            resultado = tools.consultar_politica(topico=topico)
            
            assert resultado['sucesso'] is True


class TestSolicitarReembolso:
    """Testes da ferramenta solicitar_reembolso."""
    
    def test_reembolso_ate_30_aprovado_automaticamente(self):
        """Reembolso até R$ 30 deve ser aprovado automaticamente."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = True
            
            with patch('agente.tools.ja_tem_reembolso') as mock_tem:
                mock_tem.return_value = False
                
                with patch('agente.tools.calcular_valor_pedido') as mock_valor:
                    mock_valor.return_value = 50.0
                    
                    with patch('agente.tools.execute') as mock_execute:
                        mock_execute.return_value = 1
                        
                        resultado = tools.solicitar_reembolso(
                            pedido_id=1,
                            motivo="Pedido atrasou 40 minutos",
                            valor=20.0,
                            cliente_id=1
                        )
                        
                        assert resultado['sucesso'] is True
                        assert resultado['dados']['status'] == 'aprovado'
                        assert 'automaticamente' in resultado['dados']['mensagem']
    
    def test_reembolso_acima_30_requer_aprovacao(self):
        """Reembolso acima de R$ 30 deve requerer aprovação."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = True
            
            with patch('agente.tools.ja_tem_reembolso') as mock_tem:
                mock_tem.return_value = False
                
                with patch('agente.tools.calcular_valor_pedido') as mock_valor:
                    mock_valor.return_value = 100.0
                    
                    with patch('agente.tools.execute') as mock_execute:
                        mock_execute.return_value = 1
                        
                        resultado = tools.solicitar_reembolso(
                            pedido_id=1,
                            motivo="Pedido veio todo errado",
                            valor=50.0,
                            cliente_id=1
                        )
                        
                        assert resultado['sucesso'] is True
                        assert resultado['dados']['status'] == 'pendente'
                        assert 'aprovação' in resultado['dados']['mensagem'].lower()
    
    def test_reembolso_pedido_nao_autorizado(self):
        """Deve bloquear reembolso de pedido de outro cliente."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = False
            
            resultado = tools.solicitar_reembolso(
                pedido_id=999,
                motivo="Tentando burlar o sistema",
                valor=100.0,
                cliente_id=1
            )
            
            assert resultado['sucesso'] is False
            assert 'permissão' in resultado['erro'].lower()
    
    def test_reembolso_duplicado_bloqueado(self):
        """Deve bloquear reembolso duplicado."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = True
            
            with patch('agente.tools.ja_tem_reembolso') as mock_tem:
                mock_tem.return_value = True  # Já tem reembolso
                
                resultado = tools.solicitar_reembolso(
                    pedido_id=1,
                    motivo="Segundo reembolso",
                    valor=10.0,
                    cliente_id=1
                )
                
                assert resultado['sucesso'] is False
                assert 'já possui' in resultado['erro'].lower()
    
    def test_reembolso_valor_invalido(self):
        """Deve rejeitar valor negativo ou zero."""
        resultado = tools.solicitar_reembolso(
            pedido_id=1,
            motivo="Teste valor inválido",
            valor=-10.0,
            cliente_id=1
        )
        
        assert resultado['sucesso'] is False
        assert 'maior que zero' in resultado['erro'].lower()
    
    def test_reembolso_motivo_muito_curto(self):
        """Deve rejeitar motivo muito curto."""
        resultado = tools.solicitar_reembolso(
            pedido_id=1,
            motivo="Curto",
            valor=10.0,
            cliente_id=1
        )
        
        assert resultado['sucesso'] is False
        assert '10 caracteres' in resultado['erro'].lower()
    
    def test_reembolso_valor_maior_que_pedido(self):
        """Deve rejeitar reembolso maior que valor do pedido."""
        with patch('agente.tools.pedido_pertence_ao_cliente') as mock_pertence:
            mock_pertence.return_value = True
            
            with patch('agente.tools.ja_tem_reembolso') as mock_tem:
                mock_tem.return_value = False
                
                with patch('agente.tools.calcular_valor_pedido') as mock_valor:
                    mock_valor.return_value = 50.0
                    
                    resultado = tools.solicitar_reembolso(
                        pedido_id=1,
                        motivo="Tentando reembolso maior",
                        valor=100.0,
                        cliente_id=1
                    )
                    
                    assert resultado['sucesso'] is False
                    assert 'não pode ser maior' in resultado['erro'].lower()


class TestEscalarParaHumano:
    """Testes da ferramenta escalar_para_humano."""
    
    def test_escalar_sucesso(self):
        """Deve criar ticket com sucesso."""
        with patch('agente.tools.execute') as mock_execute:
            mock_execute.return_value = 42  # ticket_id
            
            resultado = tools.escalar_para_humano(
                resumo="Cliente insatisfeito com múltiplos atrasos. Pedidos #1, #2 e #3 atrasaram.",
                cliente_id=1
            )
            
            assert resultado['sucesso'] is True
            assert resultado['dados']['ticket_id'] == 42
            assert '#42' in resultado['dados']['mensagem']
    
    def test_escalar_resumo_muito_curto(self):
        """Deve rejeitar resumo muito curto."""
        resultado = tools.escalar_para_humano(
            resumo="Muito curto",
            cliente_id=1
        )
        
        assert resultado['sucesso'] is False
        assert '20 caracteres' in resultado['erro'].lower()


class TestExecutarFerramenta:
    """Testes da função executar_ferramenta."""
    
    def test_executar_ferramenta_desconhecida(self):
        """Deve retornar erro para ferramenta desconhecida."""
        resultado = tools.executar_ferramenta(
            nome="ferramenta_inexistente",
            argumentos={},
            cliente_id=1
        )
        
        assert resultado['sucesso'] is False
        assert 'desconhecida' in resultado['erro'].lower()
    
    def test_executar_todas_ferramentas_existem(self):
        """Deve ter todas as 5 ferramentas nos schemas."""
        ferramentas = [schema['name'] for schema in tools.TOOLS_SCHEMAS]
        
        assert 'buscar_pedidos_do_cliente' in ferramentas
        assert 'detalhar_pedido' in ferramentas
        assert 'consultar_politica' in ferramentas
        assert 'solicitar_reembolso' in ferramentas
        assert 'escalar_para_humano' in ferramentas
        assert len(ferramentas) == 5
