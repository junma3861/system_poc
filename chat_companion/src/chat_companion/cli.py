"""Command-line interface for the Chat Companion project."""

from __future__ import annotations

import argparse
import sys
from typing import Optional, Sequence

from .chatbot import Chatbot
from .config import load_settings
from .llm.openrouter import OpenRouterClient
from .memory import LongTermMemory, MemoryManager, ShortTermMemory
from .prompts.templates import build_default_library


def build_chatbot() -> Chatbot:
    settings = load_settings(require_api_key=True)
    short_term = ShortTermMemory(capacity=settings.short_term_limit)
    long_term = LongTermMemory(settings.memory_store_path)
    memory = MemoryManager(short_term, long_term)
    prompts = build_default_library()
    llm_client = OpenRouterClient(settings)
    return Chatbot(llm_client, prompts, memory)


def repl(bot: Chatbot, session_id: str) -> None:
    print("Chat Companion ready. Type :help for commands.")
    while True:
        try:
                user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not user_input:
            continue
        if user_input.startswith(":"):
            handled = handle_command(bot, user_input, session_id)
            if handled == "exit":
                break
            continue
        try:
            response = bot.respond(user_input)
            print(f"assistant: {response}")
        except Exception as exc:  # pragma: no cover - CLI feedback path
            print(f"[error] {exc}")


def handle_command(bot: Chatbot, command: str, session_id: str) -> Optional[str]:
    if command == ":help":
        print(
            ":suggest -> show follow-up queries\n"
            ":history -> show recent turns\n"
            ":summary -> persist long-term summary\n"
            ":exit -> quit"
        )
    elif command == ":suggest":
        suggestions = bot.suggest_queries()
        for item in suggestions:
            print(f"- {item}")
    elif command == ":history":
        for message in bot.memory.history():
            print(f"{message['role']}: {message['content']}")
    elif command == ":summary":
        summary = bot.force_summary(session_id)
        print(f"Saved summary: {summary}")
    elif command == ":exit":
        return "exit"
    else:
        print("Unknown command. Type :help for a list of commands.")
    return None


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chat Companion CLI")
    parser.add_argument("--session", default="default", help="Session identifier for memory storage")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    bot = build_chatbot()
    try:
        repl(bot, session_id=args.session)
    finally:
        bot.llm.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
