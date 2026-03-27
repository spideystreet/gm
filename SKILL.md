---
name: gm
description: Morning standup replaced — voice or text query to get a smart GitHub daily briefing powered by Voxtral and Mistral Small
license: MIT
compatibility: Python 3.10+, uv
user-invocable: true
allowed-tools:
  - bash
  - read_file
---

# gm — Your morning standup, replaced

Speak to your terminal or type a query — get a smart daily briefing from your GitHub activity.

## What this skill does

When the user invokes `/gm`, run the gm tool to:

1. Capture a voice query (or text input if no mic / `--text` flag)
2. Transcribe it with Voxtral Transcribe 2
3. Fetch the user's GitHub context (assigned issues, open PRs, recent commits)
4. Generate an actionable briefing with Mistral Small
5. Optionally speak the response via Voxtral TTS (`--speak` flag)

## How to run

First, ensure dependencies are installed. From the skill directory, run:

```bash
uv sync
```

Then execute:

```bash
# Voice mode (default) — records 10s from mic
uv run python main.py

# Text mode — type your query instead of speaking
uv run python main.py --text

# With spoken response
uv run python main.py --speak
```

## Required environment variables

These must be set in `.env` at the project root or exported in the shell:

- `MISTRAL_API_KEY` — Mistral API key
- `GITHUB_TOKEN` — GitHub personal access token
- `GITHUB_REPO` — Target repository (format: `owner/repo`)
- `GITHUB_USERNAME` — Your GitHub username

## Example queries

- "What do I have today?"
- "Any PRs that need my review?"
- "What's issue 42 about?"
- "What did I commit yesterday?"
- "Summarize my open issues"
