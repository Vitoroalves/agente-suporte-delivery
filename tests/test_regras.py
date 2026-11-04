"""
Testes das regras de negócio.

Valida que as regras de autorização, cancelamento, atrasos
e reembolsos estão funcionando corretamente.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from agente import regras


class TestPedidoPertenceAoCliente:
    """Testes da função pedido_pertence_ao_cliente."""
    
    def test_pedido_pertence_ao_cliente_correto(self):
        """Deve retornar True quando o pedido pertence ao cliente."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'id': 1}]
            
            resultado = regras.pedido_pertence_ao_cliente(pedido_id=1, cliente_id=1)
            
            assert resultado is True
            mock_query.assert_called_once()
    
    def test_pedido_nao_pertence_ao_cliente(self):
        """Deve retornar False quando o pedido não pertence ao cliente."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []  # Nenhum resultado
            
            resultado = regras.pedido_pertence_ao_cliente(pedido_id=999, cliente_id=1)
            
            assert resultado is False
    
    def test_pedido_inexistente(self):
        """Deve retornar False quando o pedido não existe."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []
            
            resultado = regras.pedido_pertence_ao_cliente(pedido_id=9999, cliente_id=1)
            
            assert resultado is False


class TestPedidoEstaAtrasado:
    """Testes da função pedido_esta_atrasado."""
    
    def test_pedido_atrasado(self):
        """Deve retornar True quando o pedido está atrasado."""
        agora = datetime.now()
        horario_previsto = agora - timedelta(minutes=30)  # 30 min atrás
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': horario_previsto.isoformat(),
                'horario_entrega_real': None
            }]
            
            resultado = regras.pedido_esta_atrasado(pedido_id=1)
            
            assert resultado is True
    
    def test_pedido_no_prazo(self):
        """Deve retornar False quando o pedido está no prazo."""
        agora = datetime.now()
        horario_previsto = agora + timedelta(minutes=15)  # Ainda faltam 15 min
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': horario_previsto.isoformat(),
                'horario_entrega_real': None
            }]
            
            resultado = regras.pedido_esta_atrasado(pedido_id=1)
            
            assert resultado is False
    
    def test_pedido_ja_entregue_nao_esta_atrasado(self):
        """Deve retornar False quando o pedido já foi entregue."""
        agora = datetime.now()
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': agora - timedelta(hours=1),
                'horario_entrega_real': agora - timedelta(minutes=50)
            }]
            
            resultado = regras.pedido_esta_atrasado(pedido_id=1)
            
            assert resultado is False
    
    def test_pedido_inexistente(self):
        """Deve retornar False quando o pedido não existe."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []
            
            resultado = regras.pedido_esta_atrasado(pedido_id=9999)
            
            assert resultado is False


class TestPodeCancelarPedido:
    """Testes da função pode_cancelar_pedido."""
    
    def test_pode_cancelar_preparando(self):
        """Deve permitir cancelamento de pedido em preparo."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'status': 'preparando'}]
            
            pode, motivo = regras.pode_cancelar_pedido(pedido_id=1)
            
            assert pode is True
            assert 'preparo' in motivo.lower()
    
    def test_nao_pode_cancelar_a_caminho(self):
        """Não deve permitir cancelamento de pedido a caminho."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'status': 'a_caminho'}]
            
            pode, motivo = regras.pode_cancelar_pedido(pedido_id=1)
            
            assert pode is False
            assert 'entrega' in motivo.lower()
    
    def test_nao_pode_cancelar_entregue(self):
        """Não deve permitir cancelamento de pedido entregue."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'status': 'entregue'}]
            
            pode, motivo = regras.pode_cancelar_pedido(pedido_id=1)
            
            assert pode is False
            assert 'entregue' in motivo.lower()
    
    def test_nao_pode_cancelar_ja_cancelado(self):
        """Não deve permitir cancelamento de pedido já cancelado."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'status': 'cancelado'}]
            
            pode, motivo = regras.pode_cancelar_pedido(pedido_id=1)
            
            assert pode is False
            assert 'cancelado' in motivo.lower()
    
    def test_pedido_inexistente(self):
        """Não deve permitir cancelamento de pedido inexistente."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []
            
            pode, motivo = regras.pode_cancelar_pedido(pedido_id=9999)
            
            assert pode is False
            assert 'não encontrado' in motivo.lower()


class TestJaTemReembolso:
    """Testes da função ja_tem_reembolso."""
    
    def test_ja_tem_reembolso(self):
        """Deve retornar True quando já existe reembolso."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'id': 1}]
            
            resultado = regras.ja_tem_reembolso(pedido_id=1)
            
            assert resultado is True
    
    def test_nao_tem_reembolso(self):
        """Deve retornar False quando não existe reembolso."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []
            
            resultado = regras.ja_tem_reembolso(pedido_id=1)
            
            assert resultado is False


class TestCalcularValorPedido:
    """Testes da função calcular_valor_pedido."""
    
    def test_calcular_valor_existente(self):
        """Deve retornar o valor correto do pedido."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{'valor_total': 125.50}]
            
            valor = regras.calcular_valor_pedido(pedido_id=1)
            
            assert valor == 125.50
    
    def test_pedido_inexistente(self):
        """Deve retornar 0.0 quando o pedido não existe."""
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = []
            
            valor = regras.calcular_valor_pedido(pedido_id=9999)
            
            assert valor == 0.0


class TestCalcularMinutosAtraso:
    """Testes da função calcular_minutos_atraso."""
    
    def test_pedido_atrasado_30_minutos(self):
        """Deve calcular corretamente atraso de 30 minutos."""
        agora = datetime.now()
        horario_previsto = agora - timedelta(minutes=30)
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': horario_previsto.isoformat(),
                'horario_entrega_real': None
            }]
            
            minutos = regras.calcular_minutos_atraso(pedido_id=1)
            
            assert 29 <= minutos <= 31  # Pequena margem por causa do tempo de execução
    
    def test_pedido_no_prazo(self):
        """Deve retornar 0 quando o pedido não está atrasado."""
        agora = datetime.now()
        horario_previsto = agora + timedelta(minutes=20)
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': horario_previsto.isoformat(),
                'horario_entrega_real': None
            }]
            
            minutos = regras.calcular_minutos_atraso(pedido_id=1)
            
            assert minutos == 0
    
    def test_pedido_entregue(self):
        """Deve retornar 0 quando o pedido já foi entregue."""
        agora = datetime.now()
        
        with patch('agente.regras.query') as mock_query:
            mock_query.return_value = [{
                'horario_previsto': agora - timedelta(hours=1),
                'horario_entrega_real': agora - timedelta(minutes=50)
            }]
            
            minutos = regras.calcular_minutos_atraso(pedido_id=1)
            
            assert minutos == 0


class TestValorReembolsoAutomaticoPermitido:
    """Testes da função valor_reembolso_automatico_permitido."""
    
    def test_valor_limite_correto(self):
        """Deve retornar o valor limite de R$ 30.00."""
        valor = regras.valor_reembolso_automatico_permitido()
        
        assert valor == 30.0
