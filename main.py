import os
import re
import sys
from datetime import datetime

from dotenv import load_dotenv
from strands import Agent, tool
from strands.event_loop._retry import ModelRetryStrategy
from strands.models.openai import OpenAIModel
from strands.session.file_session_manager import FileSessionManager

EXIT_COMMANDS = {"sair", "exit", "quit"}
MAX_INPUT_CHARS = 2000
SYSTEM_PROMPT = "Você é um assistente útil. Responda em português."
API_KEY_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]+")


def safe_error(exc: Exception) -> str:
    """Remove segredos (ex.: chaves sk-*) de mensagens de erro antes de exibir."""
    return API_KEY_PATTERN.sub("sk-***", str(exc))


@tool
def current_datetime() -> str:
    """Retorna a data e hora locais atuais no formato ISO 8601."""
    return datetime.now().isoformat(timespec="seconds")


def main() -> None:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Erro: OPENAI_API_KEY nao encontrada. Crie um arquivo .env com sua chave (veja .env.example).")
        sys.exit(1)

    model = OpenAIModel(
        client_args={"api_key": api_key, "max_retries": 1},
        model_id=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )
    session_manager = FileSessionManager(
        session_id=os.getenv("SESSION_ID", "default"),
        storage_dir=os.getenv("SESSIONS_DIR", "./sessions"),
    )
    agent = Agent(
        model=model,
        tools=[current_datetime],
        session_manager=session_manager,
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
        retry_strategy=ModelRetryStrategy(max_attempts=2, initial_delay=1, max_delay=8),
    )

    print("Chat iniciado. Digite 'sair' para encerrar.")
    while True:
        try:
            user_input = input("Voce: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nEncerrando. Ate logo!")
            break

        if not user_input:
            continue
        if len(user_input) > MAX_INPUT_CHARS:
            print(f"Entrada muito longa (maximo {MAX_INPUT_CHARS} caracteres). Tente resumir.\n")
            continue
        if user_input.lower() in EXIT_COMMANDS:
            print("Encerrando. Ate logo!")
            break

        try:
            response = agent(user_input)
            print(f"Agente: {response}\n")
        except Exception as exc:
            print(f"Erro ao consultar o agente: {safe_error(exc)}. Tente novamente.\n")


if __name__ == "__main__":
    main()
