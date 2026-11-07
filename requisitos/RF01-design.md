# RF01 — Design Técnico — Chat Interativo via Terminal

Documento de design do requisito funcional [RF01](RF01.md).

## 1. Visão Geral da Arquitetura

Aplicação Python standalone, executada localmente no terminal. Três componentes principais:

```
┌─────────────┐     ┌──────────────────────────────┐     ┌──────────────┐
│  Usuário    │────▶│  main.py (loop CLI)          │────▶│  OpenAI API  │
│  (terminal) │◀────│  └── Agent (Strands SDK)     │◀────│  (LLM)       │
└─────────────┘     │       ├── OpenAIModel        │     └──────────────┘
                    │       ├── FileSessionManager │            ▲
                    │       └── @tool datetime     │────────────┘
                    └──────────────┬───────────────┘   (tool calls)
                                   │
                            ./sessions/  (histórico persistido em arquivo)
                                   │
                            .env (OPENAI_API_KEY, OPENAI_MODEL)
```

## 2. Stack e Dependências

| Componente | Escolha | Justificativa |
|---|---|---|
| Linguagem | Python ≥ 3.10 | Requisito; exigência do Strands SDK |
| Framework de agente | `strands-agents` | Requisito (AWS Strands Agents SDK) |
| Provedor LLM | `strands-agents[openai]` (extra) | Suporte nativo a OpenAI no Strands; instala o SDK `openai` |
| Configuração | `python-dotenv` | Leitura do `.env` |
| Memória | `FileSessionManager` (nativo do Strands) | Persiste sessão em arquivos locais, sem código extra |
| Tool data/hora | Função custom com `@tool` | ~10 linhas; evita dependência do pacote `strands-agents-tools` |

`requirements.txt`:

```
strands-agents[openai]>=1.0.0
python-dotenv>=1.0.0
```

## 3. Estrutura de Arquivos

```
Projeto/
├── .env                  # secrets e config (não versionado)
├── .env.example          # template das variáveis
├── requirements.txt
├── main.py               # loop do chat + bootstrap do agente
└── sessions/             # criado em runtime — histórico persistido
    └── <session_id>/     # arquivos JSON do FileSessionManager
```

## 4. Configuração (.env)

| Variável | Obrigatória | Default | Descrição |
|---|---|---|---|
| `OPENAI_API_KEY` | Sim | — | Chave da API OpenAI |
| `OPENAI_MODEL` | Não | `gpt-4o-mini` | ID do modelo OpenAI |
| `SESSION_ID` | Não | `default` | Identificador da sessão persistida |
| `SESSIONS_DIR` | Não | `./sessions` | Diretório dos arquivos de sessão |

`.env.example` versionado com os nomes das variáveis; `.env` no `.gitignore`.

## 5. Componentes

### 5.1 Modelo — `OpenAIModel`

```python
model = OpenAIModel(
    client_args={"api_key": os.environ["OPENAI_API_KEY"]},
    model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
)
```

- A chave é lida do `.env` via `python-dotenv`; sem a chave, o programa aborta com mensagem clara antes de criar o agente.
- O modelo é configurável por variável de ambiente, sem mudança de código.

### 5.2 Memória — `FileSessionManager`

```python
session_manager = FileSessionManager(
    session_id=os.getenv("SESSION_ID", "default"),
    storage_dir=os.getenv("SESSIONS_DIR", "./sessions"),
)
```

- Persiste o histórico da conversa em arquivos JSON locais automaticamente.
- Ao reabrir o programa com o mesmo `SESSION_ID`, o contexto anterior é restaurado.
- Comportamento de memória multi-turno nativo do `Agent` + `SessionManager`; nenhuma lógica manual de histórico.

### 5.3 Tool — data/hora atual

```python
@tool
def current_datetime() -> str:
    """Retorna a data e hora locais atuais no formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")
```

- O agente invoca a tool automaticamente quando a pergunta depende de data/hora (ex.: "que dia é hoje?").
- Alternativa considerada: `current_time` do pacote `strands-agents-tools` — descartada para manter dependências mínimas.

### 5.4 Agente e loop CLI — `main.py`

```python
agent = Agent(
    model=model,
    tools=[current_datetime],
    session_manager=session_manager,
    system_prompt="Você é um assistente útil. Responda em português.",
)
```

Loop de interação:

1. Carrega `.env` (`load_dotenv()`).
2. Valida `OPENAI_API_KEY`; se ausente → mensagem de erro e `sys.exit(1)`.
3. Cria modelo, session manager e agente.
4. Exibe instruções (`Digite 'sair' para encerrar`).
5. `input("Você: ")` → se `sair`/`exit`/`quit` (case-insensitive) → encerra.
6. Entrada vazia → volta ao passo 5 sem chamar o modelo.
7. `agent(mensagem)` → imprime resposta → volta ao passo 5.
8. Exceções da API/rede → mensagem amigável → volta ao passo 5 (loop não quebra).
9. `KeyboardInterrupt` (Ctrl+C) → encerra graciosamente.

## 6. Fluxo de Dados

```
entrada do usuário
   → loop CLI
   → Agent (Strands)
       ├── se precisar de data/hora → tool current_datetime → volta ao agente
       ├── lê/escreve histórico → FileSessionManager → ./sessions/
       └── prompt → OpenAI API → resposta
   → saída no terminal
```

## 7. Decisões de Design

| Decisão | Alternativa | Motivo da escolha |
|---|---|---|
| `FileSessionManager` | SQLite/JSON manual | Nativo do Strands, zero código de persistência |
| Tool `@tool` custom | `strands-agents-tools` | Dependência mínima, requisito trivial |
| Modelo via `OPENAI_MODEL` | Hardcoded | Flexibilidade sem custo |
| `system_prompt` fixo | Arquivo de prompt | Simplicidade ("agente super simples") |

## 8. Rastreabilidade com RF01

| Item de design | Atende |
|---|---|
| `OpenAIModel` + `strands-agents[openai]` | OpenAI via Strands |
| `.env` + `load_dotenv()` | RN04 |
| `FileSessionManager` (arquivo local) | RN01 (atualizada: memória **persistida**) |
| Tool `current_datetime` | Novo requisito de design (item 5) |
| Loop `input()` / comando de saída | RN02, RN03 |
| Validação de entrada e try/except | RN05, RN06 |
