/**
 * Chat Interface - NexFood
 * 
 * Gerencia a interface de chat e comunicação com a API.
 */

// Estado da aplicação
const state = {
    clienteAtual: null,
    aguardandoResposta: false
};

// Elementos DOM
const elements = {
    clienteSelect: null,
    mensagensContainer: null,
    mensagemInput: null,
    enviarBtn: null,
    typingIndicator: null,
    charCount: null
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Capturar elementos
    elements.clienteSelect = document.getElementById('cliente-select');
    elements.mensagensContainer = document.getElementById('mensagens');
    elements.mensagemInput = document.getElementById('mensagem-input');
    elements.enviarBtn = document.getElementById('enviar-btn');
    elements.typingIndicator = document.getElementById('typing-indicator');
    elements.charCount = document.getElementById('char-count');

    // Configurar event listeners
    setupEventListeners();

    // Carregar lista de clientes
    carregarClientes();
});

/**
 * Configura todos os event listeners
 */
function setupEventListeners() {
    // Seleção de cliente
    elements.clienteSelect.addEventListener('change', handleClienteChange);

    // Envio de mensagem
    elements.enviarBtn.addEventListener('click', handleEnviarMensagem);
    elements.mensagemInput.addEventListener('keydown', (e) => {
        // Enviar com Enter (Shift+Enter para nova linha)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleEnviarMensagem();
        }
    });

    // Contador de caracteres
    elements.mensagemInput.addEventListener('input', handleInputChange);

    // Auto-resize do textarea
    elements.mensagemInput.addEventListener('input', autoResizeTextarea);
}

/**
 * Carrega lista de clientes do servidor
 */
async function carregarClientes() {
    try {
        const response = await fetch('/api/clientes');
        const data = await response.json();

        if (data.erro) {
            console.error('Erro ao carregar clientes:', data.erro);
            return;
        }

        // Popular select
        data.clientes.forEach(cliente => {
            const option = document.createElement('option');
            option.value = cliente.id;
            option.textContent = `${cliente.nome} (${cliente.email})`;
            elements.clienteSelect.appendChild(option);
        });
    } catch (erro) {
        console.error('Erro ao carregar clientes:', erro);
    }
}

/**
 * Handler para mudança de cliente
 */
async function handleClienteChange(e) {
    const clienteId = parseInt(e.target.value);

    if (!clienteId) {
        // Desabilitar chat
        elements.mensagemInput.disabled = true;
        elements.enviarBtn.disabled = true;
        state.clienteAtual = null;
        return;
    }

    // Atualizar estado
    state.clienteAtual = clienteId;

    // Limpar chat
    elements.mensagensContainer.innerHTML = '';

    // Habilitar input
    elements.mensagemInput.disabled = false;
    elements.enviarBtn.disabled = false;
    elements.mensagemInput.focus();

    // Limpar histórico no servidor
    try {
        await fetch('/api/limpar_historico', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cliente_id: clienteId })
        });
    } catch (erro) {
        console.error('Erro ao limpar histórico:', erro);
    }

    // Buscar mensagem de boas-vindas
    try {
        const response = await fetch('/api/boas_vindas');
        const data = await response.json();
        
        if (data.mensagem) {
            adicionarMensagemAgente(data.mensagem, []);
        }
    } catch (erro) {
        console.error('Erro ao buscar boas-vindas:', erro);
    }
}

/**
 * Handler para input de mensagem
 */
function handleInputChange(e) {
    const length = e.target.value.length;
    elements.charCount.textContent = `${length} / 2000`;
    
    // Mudar cor se ultrapassar o limite
    if (length > 2000) {
        elements.charCount.style.color = '#dc3545';
    } else {
        elements.charCount.style.color = '#6c757d';
    }
}

/**
 * Auto-resize do textarea
 */
function autoResizeTextarea(e) {
    e.target.style.height = 'auto';
    e.target.style.height = e.target.scrollHeight + 'px';
}

/**
 * Handler para envio de mensagem
 */
async function handleEnviarMensagem() {
    // Validações
    if (!state.clienteAtual) {
        alert('Selecione um cliente primeiro');
        return;
    }

    if (state.aguardandoResposta) {
        return;
    }

    const mensagem = elements.mensagemInput.value.trim();
    
    if (!mensagem) {
        return;
    }

    if (mensagem.length > 2000) {
        alert('Mensagem muito longa. Máximo: 2000 caracteres');
        return;
    }

    // Limpar input
    elements.mensagemInput.value = '';
    elements.mensagemInput.style.height = 'auto';
    handleInputChange({ target: elements.mensagemInput });

    // Adicionar mensagem do usuário
    adicionarMensagemUsuario(mensagem);

    // Desabilitar input
    state.aguardandoResposta = true;
    elements.mensagemInput.disabled = true;
    elements.enviarBtn.disabled = true;

    // Mostrar indicador de digitação
    mostrarIndicadorDigitacao();

    try {
        // Enviar para API
        const response = await fetch('/api/conversar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                cliente_id: state.clienteAtual,
                mensagem: mensagem
            })
        });

        const data = await response.json();

        // Esconder indicador
        esconderIndicadorDigitacao();

        if (!response.ok) {
            throw new Error(data.erro || 'Erro ao processar mensagem');
        }

        // Adicionar resposta do agente
        adicionarMensagemAgente(data.resposta, data.ferramentas_usadas || []);

        // Se houver erro do agente, mostrar
        if (data.erro) {
            console.warn('Aviso do agente:', data.erro);
        }

    } catch (erro) {
        esconderIndicadorDigitacao();
        console.error('Erro ao enviar mensagem:', erro);
        
        adicionarMensagemAgente(
            'Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente.',
            []
        );
    } finally {
        // Reabilitar input
        state.aguardandoResposta = false;
        elements.mensagemInput.disabled = false;
        elements.enviarBtn.disabled = false;
        elements.mensagemInput.focus();
    }
}

/**
 * Adiciona mensagem do usuário ao chat
 */
function adicionarMensagemUsuario(texto) {
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = 'mensagem usuario';
    
    mensagemDiv.innerHTML = `
        <div class="mensagem-avatar">👤</div>
        <div class="mensagem-conteudo">
            <div class="mensagem-bubble">${escapeHtml(texto)}</div>
        </div>
    `;
    
    elements.mensagensContainer.appendChild(mensagemDiv);
    scrollParaUltimaMensagem();
}

/**
 * Adiciona mensagem do agente ao chat
 */
function adicionarMensagemAgente(texto, ferramentasUsadas) {
    const mensagemDiv = document.createElement('div');
    mensagemDiv.className = 'mensagem agente';
    
    // Criar HTML das ferramentas
    let toolsHtml = '';
    if (ferramentasUsadas && ferramentasUsadas.length > 0) {
        const badges = ferramentasUsadas.map(tool => {
            const classe = tool.sucesso ? 'sucesso' : 'erro';
            const icone = tool.sucesso ? '✓' : '✗';
            return `<span class="tool-badge ${classe}">${icone} ${formatarNomeTool(tool.nome)}</span>`;
        }).join('');
        
        toolsHtml = `<div class="mensagem-tools">${badges}</div>`;
    }
    
    mensagemDiv.innerHTML = `
        <div class="mensagem-avatar">🤖</div>
        <div class="mensagem-conteudo">
            <div class="mensagem-bubble">${escapeHtml(texto)}</div>
            ${toolsHtml}
        </div>
    `;
    
    elements.mensagensContainer.appendChild(mensagemDiv);
    scrollParaUltimaMensagem();
}

/**
 * Mostra indicador de digitação
 */
function mostrarIndicadorDigitacao() {
    elements.typingIndicator.style.display = 'flex';
    scrollParaUltimaMensagem();
}

/**
 * Esconde indicador de digitação
 */
function esconderIndicadorDigitacao() {
    elements.typingIndicator.style.display = 'none';
}

/**
 * Scroll automático para última mensagem
 */
function scrollParaUltimaMensagem() {
    setTimeout(() => {
        const container = document.getElementById('chat-container');
        container.scrollTop = container.scrollHeight;
    }, 100);
}

/**
 * Formata nome da ferramenta para exibição
 */
function formatarNomeTool(nome) {
    const nomes = {
        'buscar_pedidos_do_cliente': 'Buscar Pedidos',
        'detalhar_pedido': 'Detalhar Pedido',
        'consultar_politica': 'Consultar Política',
        'solicitar_reembolso': 'Reembolso',
        'escalar_para_humano': 'Escalar'
    };
    
    return nomes[nome] || nome;
}

/**
 * Escape HTML para prevenir XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
