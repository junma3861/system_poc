# Chat Companion

Chat Companion is a lightweight Python toolkit for building companion chatbots. It includes:

- **LLM module** wrapping the OpenRouter chat completions API
- **Prompt module** with reusable query suggestion, response, and ranking prompts
- **Memory module** that tracks short-term conversation history and persists long-term summaries
- **CLI** for interactive experimentation and manual memory management

## Features

- Configurable OpenRouter client with pluggable HTTP transport for testing
- Prompt templates that render structured inputs from conversation context
- Short-term memory powered by a ring buffer to keep the latest turns lightweight
- Long-term memory that stores timestamped summaries on disk and exposes semantic search hooks
- Modular `Chatbot` orchestration layer tying LLM, prompts, and memories together

## Project Layout

```
chat_companion/
├── pyproject.toml
├── README.md
├── src/
│   └── chat_companion/
│       ├── cli.py
│       ├── chatbot.py
│       ├── config.py
│       ├── llm/
│       │   └── openrouter.py
│       ├── memory/
│       │   ├── __init__.py
│       │   ├── long_term.py
│       │   ├── manager.py
│       │   └── short_term.py
│       └── prompts/
│           └── templates.py
└── tests/
```

## Getting Started

1. **Set up Python**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. **Install dependencies**
   ```bash
   pip install -e .[dev]
   ```
3. **Configure OpenRouter access**
   - Create a `.env` file in the project root containing:
     ```
     OPENROUTER_API_KEY=sk-or-...
     OPENROUTER_MODEL=openrouter/auto
     CHAT_COMPANION_APP_NAME=chat-companion
     ```
   - See the OpenRouter documentation for API key details.

## Usage

Run the interactive CLI:
```bash
chat-companion --session demo
```
CLI commands:
- Type free-form text to chat with the assistant.
- `:suggest` to receive follow-up query suggestions.
- `:history` to inspect the short-term memory buffer.
- `:summary` to force a long-term summary write.
- `:exit` to quit the session.

The CLI stores session summaries under `var/memory_store.json` by default. Adjust `CHAT_COMPANION_MEMORY_PATH` to point elsewhere.

## Testing

```bash
pytest
```

## Configuration Reference

| Environment Variable | Description | Default |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Required API key for OpenRouter. | _None_ |
| `OPENROUTER_MODEL` | Model identifier passed to OpenRouter. | `openrouter/auto` |
| `OPENROUTER_BASE_URL` | Override API base URL. | `https://openrouter.ai/api/v1` |
| `CHAT_COMPANION_APP_NAME` | App name used for telemetry headers. | `chat-companion-dev` |
| `CHAT_COMPANION_MEMORY_PATH` | File path for long-term summaries. | `var/memory_store.json` |

## Next Steps

- Integrate semantic retrieval for long-term summaries.
- Add streaming responses and typed message schemas.
- Swap CLI with a FastAPI or web UI front-end when ready.
