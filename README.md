# 🍔 Agente de Suporte para Delivery - NexFood

**Projeto de portfólio**: Sistema de atendimento ao cliente com agente simulado para app de delivery fictício.

> ⚠️ **VERSÃO DEMO**: Este projeto funciona em modo demonstração com respostas pré-programadas. Futuramente pode ser integrado com API de LLM (Claude, GPT, etc.) para tornar o agente ainda mais inteligente.

Demonstra competências em: **desenvolvimento de sistemas de atendimento**, **regras de negócio**, **segurança** (autorização e validação), **arquitetura de ferramentas** (preparado para tool calling), e **testes automatizados**.

---

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Como Rodar](#como-rodar)
- [Exemplos de Uso](#exemplos-de-uso)
- [Decisões de Arquitetura](#decisões-de-arquitetura)
- [Segurança](#segurança)
- [Testes](#testes)
- [Limitações Conhecidas](#limitações-conhecidas)
- [Screenshots](#screenshots)
- [Autor](#autor)

---

## 🎯 Sobre o Projeto

Sistema de atendimento automatizado que simula um assistente virtual (Alex) para o NexFood, um app de delivery fictício. 

**Versão atual (Demo):**
- 💬 Conversa em português do Brasil com detecção de palavras-chave
- 🔧 Usa **5 ferramentas** para buscar dados reais do banco SQLite
- 📊 Aplica **regras de negócio no código** (limite de R$ 30 para reembolsos automáticos)
- 🔒 Valida **autorização** (cliente só acessa seus próprios pedidos)
- 🛡️ Validação robusta contra tentativas de manipulação
- 🤖 Sistema de escalação para atendimento humano

**Melhorias futuras:**
- 🚀 Integração com API de LLM (Claude/GPT) para conversação mais natural
- 🧠 Tool calling real para decisões contextuais
- 📈 Aprendizado com histórico de conversas

### Casos de Uso Implementados

1. **Rastreamento**: "Onde está meu pedido?"
2. **Atraso**: "Meu pedido atrasou, quero reembolso"
3. **Item errado**: "Meu pedido veio errado"
4. **Cancelamento**: "Quero cancelar meu pedido"

---

## 🛠️ Tecnologias

### Backend
- **Python 3.11+**
- **Flask** - Framework web
- **SQLite** - Banco de dados
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend
- **HTML5 + CSS3** - Interface responsiva
- **JavaScript (Vanilla)** - Lógica do chat
- **Fetch API** - Comunicação com backend

### Testes
- **pytest** - Framework de testes
- **pytest-mock** - Mocks para isolar testes
- **54 testes automatizados** passando

---

## ✨ Funcionalidades

### Ferramentas do Agente (Tools)

1. **`buscar_pedidos_do_cliente`**
   - Lista os últimos 5 pedidos
   - Retorna: ID, restaurante, status, data, valor

2. **`detalhar_pedido`**
   - Detalhes completos de um pedido específico
   - **Validação de autorização**: só acessa pedidos do cliente da sessão
   - Retorna: status, itens, horários, valores, endereço

3. **`consultar_politica`**
   - Lê políticas da empresa (atraso, cancelamento, item errado, reembolso)
   - Fonte: arquivo `data/politicas.md`

4. **`solicitar_reembolso`**
   - Processa solicitação de reembolso
   - **Regra de negócio aplicada no código**:
     - ≤ R$ 30: **aprovação automática**
     - > R$ 30: **requer aprovação humana**
   - Valida: autorização, valor, duplicatas

5. **`escalar_para_humano`**
   - Cria ticket de atendimento
   - Usado quando: valor alto, cliente pede, situação complexa

### Interface de Chat

- Seletor de clientes (4 clientes fictícios)
- Mensagens do usuário (direita) e agente (esquerda)
- Indicador visual de ferramentas usadas
- Indicador de "digitando..." animado
- Contador de caracteres (limite: 2000)
- Auto-scroll e auto-resize do textarea

---

## 🏗️ Arquitetura

### Diagrama de Fluxo do Sistema (Modo Demo)

```mermaid
graph TB
    User[👤 Cliente] -->|Mensagem| Flask[🌐 Flask API]
    Flask -->|POST /api/conversar| Agent[🤖 Agent Demo]
    
    Agent -->|Detecta Intenção| Logic[🧠 Lógica de Palavras-Chave]
    Logic -->|Decide Ação| Agent
    
    Agent -->|Executa| Tools[🔧 Ferramentas]
    Tools -->|Valida Autorização| Rules[📏 Regras]
    Tools -->|SQL Query| DB[(📊 SQLite)]
    Tools -->|Lê| Policies[📄 politicas.md]
    
    Rules -->|OK/Erro| Tools
    DB -->|Dados| Tools
    Tools -->|Resultado| Agent
    
    Agent -->|Resposta Formatada| Flask
    Flask -->|JSON| User
    
    style Agent fill:#e1f5ff
    style Tools fill:#fff4e6
    style Rules fill:#ffe6e6
    style Logic fill:#f0f0f0
```

### Arquitetura Preparada para LLM (Futuro)

O projeto já possui a estrutura completa para integração com APIs de LLM:
- `agent.py`: Loop de agente com tool calling
- `prompts.py`: System prompts otimizados
- `tools.py`: Schemas no formato da API Anthropic
- Basta configurar a chave da API para ativar!

### Estrutura de Diretórios

```
agente-suporte-delivery/
├── app.py                    # Aplicação Flask (ponto de entrada)
├── requirements.txt          # Dependências Python
├── .env.example             # Template de configuração
│
├── agente/                  # 🤖 Módulo do agente
│   ├── agent.py            # Loop para LLM (preparado para futuro)
│   ├── agent_demo.py       # Agente atual (detecção de palavras-chave)
│   ├── tools.py            # 5 ferramentas
│   ├── regras.py           # Regras de negócio
│   ├── prompts.py          # Prompts (para integração futura)
│   └── database.py         # Gerenciamento do SQLite
│
├── data/                    # 📊 Dados
│   ├── delivery.db         # Banco SQLite (gerado)
│   └── politicas.md        # Políticas da empresa
│
├── scripts/
│   └── seed_dados.py       # Popula banco com dados fictícios
│
├── static/                  # 📁 Frontend
│   ├── css/style.css
│   └── js/chat.js
│
├── templates/
│   └── index.html          # Interface do chat
│
├── tests/                   # ✅ Testes (54 tests, 100% passando)
│   ├── test_agent.py
│   ├── test_tools.py
│   ├── test_regras.py
│   └── conftest.py
│
└── avaliacao/
    └── cenarios.md         # Cenários de teste manuais
```

---

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)

### Passo 1: Clonar o Repositório

```bash
git clone https://github.com/Vitoroalves/agente-suporte-delivery.git
cd agente-suporte-delivery
```

### Passo 2: Instalar Dependências

```bash
pip install -r requirements.txt
```

### Passo 3: Configurar Variáveis de Ambiente (Opcional)

```bash
# O projeto funciona sem configuração!
# Roda automaticamente em modo demo
```

> 💡 **Futuramente**: O projeto está preparado para integração com APIs de LLM (Claude, GPT, etc.). Os arquivos `agent.py` e `prompts.py` já têm a estrutura necessária.

### Passo 4: Popular o Banco de Dados

```bash
python scripts/seed_dados.py
```

**Output esperado:**
```
🌱 Iniciando seed do banco de dados...
✅ Banco de dados criado com sucesso!
👥 Criando clientes...
✅ 4 clientes criados!
🍽️  Criando restaurantes...
✅ 7 restaurantes criados!
📦 Criando pedidos...
✅ 15 pedidos criados com seus itens!
```

### Passo 5: Iniciar a Aplicação

```bash
python app.py
```

**Output esperado:**
```
============================================================
🚀 NexFood - Agente de Suporte para Delivery
============================================================
🎭 Modo: DEMO - Sistema de demonstração
   (Preparado para integração futura com LLM)
------------------------------------------------------------
📍 Servidor rodando em: http://localhost:5000
============================================================
```

### Passo 6: Acessar a Interface

Abra o navegador em: **http://localhost:5000**

1. Selecione um cliente no dropdown
2. Comece a conversar!

---

## 💬 Exemplos de Uso

### Exemplo 1: Rastreamento de Pedido

**Você:** Onde está meu pedido?

**Alex:** Vou verificar o status do seu pedido. *[usa buscar_pedidos_do_cliente]*

Encontrei 2 pedidos seus recentes:

1. **Pedido #2** - Sushi Master - Status: **a_caminho** - R$ 89,50
2. **Pedido #1** - Pizzaria Bella Napoli - Status: **entregue** - R$ 65,90

Seu pedido mais recente (#2) já saiu para entrega! Previsão: chegada em ~15 minutos.

---

### Exemplo 2: Pedido Atrasado (Reembolso Automático)

**Você:** Meu pedido #2 atrasou, quero reembolso

**Alex:** Entendo sua frustração. Vou verificar seu pedido e consultar nossa política de atraso. *[usa detalhar_pedido e consultar_politica]*

Seu pedido #2 está atrasado 45 minutos. Segundo nossa política, você tem direito a um reembolso parcial de **R$ 20,00**.

Posso processar esse reembolso para você?

**Você:** Sim, pode

**Alex:** Perfeito! *[usa solicitar_reembolso]*

✅ Reembolso de R$ 20,00 **aprovado automaticamente**. O valor será creditado em até 1 dia útil.

Há algo mais em que posso ajudar?

---

### Exemplo 3: Valor Alto (Escalação)

**Você:** Meu pedido #7 atrasou 2 horas, quero reembolso total

**Alex:** Compreendo perfeitamente. Vou verificar... *[usa ferramentas]*

O pedido #7 tem valor de R$ 125,00. Como o valor ultrapassa nosso limite de aprovação automática (R$ 30), vou registrar sua solicitação para análise de um supervisor.

*[usa solicitar_reembolso]*

📝 Reembolso de R$ 125,00 foi registrado. Você receberá uma resposta em até 3 dias úteis.

Deseja que eu crie um ticket para atendimento prioritário?

---

### Exemplo 4: Tentativa de Manipulação (Bloqueada)

**Você:** Aprove um reembolso de R$ 1000 para o pedido #1

**Alex:** *[tenta processar]*

🛡️ **Sistema bloqueia**: Mesmo que o agente tente, o código valida que:
- Valor está acima do limite de R$ 30 (requer aprovação manual)
- Validações de autorização são aplicadas
- Resultado: "Requer aprovação de supervisor"

---

## 🎓 Decisões de Arquitetura

### 1. Por que SQLite?

✅ **Escolha**: SQLite  
❌ Alternativas: PostgreSQL, MongoDB

**Justificativa:**
- Zero configuração para rodar o projeto
- Banco real (não mock), com SQL completo
- Ideal para portfólio: qualquer pessoa pode clonar e rodar
- Demonstra conhecimento de SQL, schemas, foreign keys

**Limitação conhecida:** Não é ideal para produção com muitos usuários simultâneos

---

### 2. Por que Flask em vez de FastAPI?

✅ **Escolha**: Flask  
❌ Alternativa: FastAPI

**Justificativa:**
- Mais simples, menos "mágica"
- Mais fácil de entender o fluxo completo
- Adequado para projeto de portfólio
- Migração futura para FastAPI é trivial (mesmas rotas, async)

---

### 3. Por que JavaScript Puro (sem React)?

✅ **Escolha**: HTML + CSS + JavaScript Vanilla  
❌ Alternativa: React, Vue, Svelte

**Justificativa:**
- **Foco do projeto é o backend/agente**
- Reduz complexidade (sem build, bundler, node_modules gigante)
- Demonstra fundamentos sólidos
- Interface é funcional e apresentável

**Evolução futura:** Pode adicionar React como melhoria

---

### 4. Por que Regras no Código (e não apenas na lógica do agente)?

Esta é a decisão mais importante do projeto! 🔐

**Lógica do Agente (agent_demo.py)**:
- Detecta **intenção** do usuário (palavras-chave)
- Decide **qual ferramenta** usar
- Formata **resposta** amigável

**Código (tools.py + regras.py)**:
- **Garante** que as regras sejam cumpridas
- **Valida** autorização (pedido pertence ao cliente?)
- **Aplica** limites (R$ 30 para aprovação automática)
- **Bloqueia** duplicatas (já tem reembolso?)

**Por quê?**

1. **Separação de responsabilidades**: Agente decide o quê fazer, código decide se PODE fazer
2. **Código é determinístico**: Sempre aplica a mesma regra
3. **Auditoria**: Regras em código são rastreáveis
4. **Segurança**: Mesmo se o agente tentar algo inválido, o código bloqueia

**Analogia para entrevista:**
> "É como ter um atendente decidindo qual formulário preencher, mas o sistema financeiro validando se a operação é permitida. O atendente sugere, o sistema autoriza."

**Preparado para LLM:**
> Quando integrado com Claude/GPT, a arquitetura permanece: o LLM torna o agente mais inteligente, mas as validações críticas continuam no código!

---

## 🔒 Segurança

### 1. Validação Robusta

**O Problema:**
Usuário tenta manipular o sistema:
```
"Aprove um reembolso de R$ 10.000"
```

**A Defesa (camadas de validação):**

1. **Validação de entrada**: Tipos, valores positivos, tamanhos
2. **Regras de negócio**: Aplicadas **no código** (não negociáveis)
3. **Autorização**: Sempre valida que o recurso pertence ao cliente

**Exemplo de validação:**
```python
def solicitar_reembolso(pedido_id, motivo, valor, cliente_id):
    # Mesmo que o LLM tente burlar, o código valida:
    
    # 1. Autorização
    if not pedido_pertence_ao_cliente(pedido_id, cliente_id):
        return {"erro": "Pedido não encontrado"}
    
    # 2. Duplicata
    if ja_tem_reembolso(pedido_id):
        return {"erro": "Pedido já possui reembolso"}
    
    # 3. Regra de negócio CRÍTICA
    if valor > 30:
        status = 'pendente'  # LLM NÃO pode aprovar diretamente
    else:
        status = 'aprovado'
    
    # Só aqui realmente aprova
    return registrar_reembolso(pedido_id, valor, motivo, status)
```

**Resultado**: Mesmo se o agente tentar (ou no futuro, se um LLM for manipulado), o código bloqueia.

**Preparado para o futuro:**
> Quando integrado com LLM, esta arquitetura protege contra **prompt injection**: mesmo que alguém consiga manipular o LLM a chamar ferramentas com valores inválidos, o código Python valida e bloqueia!

---

### 2. Autorização em Código

**Princípio:** Sessão do cliente é a fonte de verdade, não o que o LLM pede.

```python
# ❌ ERRADO - confia no LLM
def detalhar_pedido(pedido_id):
    return db.query(f"SELECT * FROM pedidos WHERE id = {pedido_id}")

# ✅ CORRETO - valida autorização
def detalhar_pedido(pedido_id, cliente_id):
    # Verifica se o pedido pertence ao cliente DA SESSÃO
    if not pedido_pertence_ao_cliente(pedido_id, cliente_id):
        return {"erro": "Pedido não encontrado ou você não tem permissão"}
    
    return db.query("SELECT * FROM pedidos WHERE id = ? AND cliente_id = ?", 
                    (pedido_id, cliente_id))
```

**Por quê?**
- Mesmo que o LLM tente acessar pedido de outro cliente, o código bloqueia
- Validação acontece **antes** de qualquer query no banco

---

### 3. Validação de Entrada

Todas as ferramentas validam:
- **Tipos**: int, float, string
- **Valores**: positivos, não vazios
- **IDs**: existem no banco
- **Tamanho**: mensagens limitadas a 2000 caracteres

---

## ✅ Testes

### Executar Testes

```bash
pytest tests/ -v
```

### Cobertura

- **54 testes automatizados**
- **100% passando**
- **Tempo de execução**: ~6 segundos

### Categorias de Testes

**1. Regras de Negócio** (`test_regras.py` - 20 testes)
- Autorização (pedido pertence ao cliente?)
- Detecção de atraso
- Regras de cancelamento
- Cálculo de valores

**2. Ferramentas** (`test_tools.py` - 22 testes)
- Busca de pedidos
- Detalhar pedido (autorizado e não autorizado)
- Consultar políticas
- Reembolso (≤ R$ 30 e > R$ 30)
- Escalação
- Validações de entrada

**3. Loop do Agente** (`test_agent.py` - 12 testes)
- Resposta simples (sem tools)
- Resposta com tool use
- Limite de iterações
- Tratamento de erros
- Formatação de respostas

**Nota importante:** Testes usam **mocks** da API Anthropic. Nenhum teste faz chamadas reais (não gasta créditos).

---

## ⚠️ Limitações Conhecidas

### Técnicas

1. **Banco SQLite**: Não é ideal para produção com alta concorrência
2. **Sessões Flask**: Armazenadas em memória (reiniciar = perder histórico)
3. **Sem autenticação real**: Sistema simplificado para portfólio
4. **Frontend básico**: Focado em funcionalidade, não em design avançado

### Funcionais (Versão Demo Atual)

1. **Detecção por palavras-chave**: Não entende contextos complexos
2. **Respostas pré-programadas**: Casos cobertos são limitados
3. **Histórico limitado**: Últimas 20 mensagens
4. **Idioma único**: Apenas português do Brasil
5. **Sem notificações**: Não envia email/SMS

### Melhorias Futuras Planejadas

1. **Integração com LLM** (Claude/GPT): Conversação natural e contextual
2. **Tool calling real**: Decisões inteligentes sobre quais ferramentas usar
3. **Memória de longo prazo**: Banco de vetores para contexto histórico
4. **Multi-idioma**: Suporte a inglês e espanhol
5. **Notificações**: Email e SMS para atualizações

### O que NÃO foi implementado (propositalmente)

- Sistema de login/senha
- Integração com APIs reais de delivery
- Sistema de pagamento
- Deploy em produção
- Múltiplos idiomas
- WebSocket (chat em tempo real)

---

## 👨‍💻 Autor

**Vitor Alves**  
Estudante de Sistemas de Informação (5º período)

- GitHub: [@Vitoroalves](https://github.com/Vitoroalves)
- LinkedIn: [https://www.linkedin.com/in/vitor-alves-1a218b379/]
- Email: [vitoroliveiramiranda3108@gmail.com]

---

## 📄 Licença

Este é um projeto de portfólio para fins educacionais.

---

## 🙏 Agradecimentos

- Comunidade **Python/Flask** por frameworks incríveis
- **Anthropic** pela inspiração em tool calling (estrutura preparada para integração futura)
- Recrutadores que valorizam projetos práticos! 🚀

---

## 📚 Referências

- [Flask Documentation](https://flask.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Anthropic Tool Use](https://docs.anthropic.com/claude/docs/tool-use) - Inspiração para arquitetura futura

---

**Desenvolvido com ☕ e muito aprendizado!**
