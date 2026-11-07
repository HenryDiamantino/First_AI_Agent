# RF01 — Plano de Implementação

Plano de implementação do chat interativo via terminal, baseado em [RF01](RF01.md) (funcional) e [RF01-design.md](RF01-design.md) (técnico).

## 1. Escopo

Entregar um `main.py` executável via `python main.py` que implementa o loop de chat com OpenAI via Strands Agents, memória persistida em `./sessions/` e tool de data/hora — cobrindo as RN01–RN07 do RF01.

## 2. Agentes e Papéis

| Agente | Tipo | Responsabilidade |
|---|---|---|
| **Tech Lead** | Orquestrador | Aprova design, revisa código, valida DoD, acompanha progresso |
| **Dev Agent** | Executor | Implementa código, cria arquivos de configuração, resolve erros de build/runtime |
| **QA Agent** | Verificador | Executa cenários de teste manuais, valida critérios de aceite do RF01 |
| **Usuário (humano)** | Aprovador | Fornece `OPENAI_API_KEY`, faz aceite final executando o chat |

> Em squads pequenos, Dev Agent e QA Agent podem ser o mesmo executor; o Tech Lead revisa e o humano aceita.

## 3. Pré-requisitos

| # | Item | Responsável |
|---|---|---|
| P1 | Python ≥ 3.10 instalado (`python --version`) | Dev Agent |
| P2 | Chave OpenAI válida disponível | Usuário |
| P3 | RF01 e design aprovados | Tech Lead |

## 4. Atividades

### Fase 1 — Setup do projeto

| ID | Atividade | Entregável | Agente | Depende de |
|---|---|---|---|---|
| A1 | Criar `requirements.txt` (`strands-agents[openai]`, `python-dotenv`) | `requirements.txt` | Dev | P3 |
| A2 | Criar `.env.example` e `.gitignore` (`.env`, `sessions/`, `__pycache__/`, `venv/`) | `.env.example`, `.gitignore` | Dev | — |
| A3 | Criar ambiente virtual e instalar dependências (`pip install -r requirements.txt`) | venv funcional | Dev | A1 |

### Fase 2 — Implementação do `main.py`

| ID | Atividade | Regra atendida | Agente | Depende de |
|---|---|---|---|---|
| A4 | `load_dotenv()` + validação de `OPENAI_API_KEY` (erro claro e `sys.exit(1)` se ausente) | RN04 | Dev | A3 |
| A5 | Tool `@tool current_datetime()` retornando `datetime.now().isoformat()` | RN07 | Dev | — |
| A6 | `OpenAIModel` com `api_key` do env e `model_id` de `OPENAI_MODEL` (default `gpt-4o-mini`) | Design 5.1 | Dev | A4 |
| A7 | `FileSessionManager` com `SESSION_ID`/`SESSIONS_DIR` configuráveis | RN01 | Dev | — |
| A8 | Instanciar `Agent` com model + tools + session_manager + system_prompt em PT-BR | Design 5.4 | Dev | A5, A6, A7 |
| A9 | Loop CLI: `input()`, comando `sair`/`exit`/`quit`, ignora vazios, `KeyboardInterrupt` | RN02, RN03, RN05 | Dev | A8 |
| A10 | Try/except no `agent(msg)` com mensagem amigável sem quebrar o loop | RN06 | Dev | A9 |

### Fase 3 — Verificação (cenários de teste manual)

| ID | Cenário | Comando/Ação | Esperado | Critério RF01 |
|---|---|---|---|---|
| T1 | Start feliz | `python main.py` com `.env` válido | Prompt de boas-vindas | CA1 |
| T2 | Pergunta/resposta | "Olá, meu nome é X" | Resposta coerente | CA2 |
| T3 | Memória em sessão | "Qual é o meu nome?" | Responde "X" | CA3 |
| T4 | Persistência | Fechar, reabrir, "qual é o meu nome?" | Responde "X" (lê `./sessions/`) | CA4 |
| T5 | Tool data/hora | "Que horas são?" | Data/hora real atual | CA5 |
| T6 | Saída | `sair` e `Ctrl+C` | Encerra graciosamente | CA6 |
| T7 | Sem API key | Remover `OPENAI_API_KEY` do `.env`, rodar | Mensagem clara, sem stack trace | CA7 |
| T8 | Chave inválida | Key falsa, enviar mensagem | Erro amigável, loop continua | CA8 |
| T9 | Entrada vazia | Enter sem digitar | Não chama API, novo prompt | RN05 |

### Fase 4 — Fechamento

| ID | Atividade | Entregável | Agente | Depende de |
|---|---|---|---|---|
| A11 | Revisão de código (segurança: sem key em código/log; simplicidade) | Aprovação | Tech Lead | A10 |
| A12 | README com instruções de execução (venv, `.env`, `python main.py`) | `README.md` | Dev | A11 |
| A13 | Aceite final executando T1–T9 | Sign-off | Usuário | T1–T9, A12 |

## 5. Definition of Done (DoD)

- [ ] `requirements.txt`, `.env.example`, `.gitignore`, `main.py`, `README.md` criados
- [ ] Nenhum segredo versionado (`.env` no `.gitignore`)
- [ ] Todos os cenários T1–T9 passando
- [ ] Todos os critérios de aceite do RF01 marcados
- [ ] Revisão do Tech Lead aprovada

## 6. Acompanhamento

- **Status por atividade**: pendente → em andamento → concluída (marcação neste plano ou no todo da sessão).
- **Marcos**: M1 = setup OK (A1–A3) · M2 = chat funciona (A4–A9) · M3 = testes verdes (T1–T9) · M4 = aceite (A11–A13).
- **Critério de progresso**: cada cenário de teste passando é evidência objetiva — não há estimativa de tempo; mede-se por marcos concluídos.
- **Bloqueios comuns**: chave OpenAI inválida/sem quota, `pip` sem acesso ao PyPI, versão de Python < 3.10.

## 7. Riscos

| Risco | Mitigação |
|---|---|
| API Strands/OpenAI com breaking changes na versão instalada | Fixar versão mínima testada no `requirements.txt` após validação |
| Chave exposta acidentalmente | `.env` no `.gitignore`; `.env.example` só com nomes de variáveis |
| Sessão corrompida em `./sessions/` | Deletar a pasta ou trocar `SESSION_ID` — documentar no README |
