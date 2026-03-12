# CodenamesLLM

A Python implementation of the popular board game **Codenames**, with the twist being that you can play against LLM-based opponents.

Play as the SpyMaster or Guesser on either team, mix and match human and AI players, and watch GPT reason through clues and guesses in real time.

## Features

- **Three player interfaces** — freely assign any role to any interface:
  - **LLM** — GPT-powered SpyMaster and Guesser with chain-of-thought reasoning
  - **GUI (Tkinter)** — clickable game board with color-coded cards, move history panel, and an AI word-count slider
  - **CLI** — lightweight text-based interface for terminal play
- **Mix and match** — pair an AI SpyMaster with a human Guesser, pit two AIs against each other, or play fully manually
- **LangSmith tracing** — all LLM calls are instrumented with `@traceable` for observability and debugging
- **400-word dictionary** sourced from the official Codenames word list

## Requirements

- Python 3.10+
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [LangSmith API key](https://smith.langchain.com/) (for LLM tracing)

### Python Dependencies

| Package | Purpose |
|---|---|
| `langchain-openai` | OpenAI chat model integration |
| `langsmith` | LLM call tracing and observability |
| `pydantic` | Structured output parsing for LLM responses |
| `python-dotenv` | Load API keys from `.env` |
| `colorama` | Colored terminal output |
| `tkinter` | GUI (included with most Python installations) |
