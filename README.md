# gm

Your morning standup, replaced. Speak to your terminal, get a smart daily briefing from your GitHub activity — powered by Voxtral and Mistral Small.

Built with Voxtral TTS + Voxtral Transcribe 2 + Mistral Small.

## Installation

```bash
brew install portaudio  # macOS
uv sync
```

Add your keys to `.env`:

```
MISTRAL_API_KEY=your_key
GITHUB_TOKEN=your_token
GITHUB_REPO=owner/repo
GITHUB_USERNAME=your_username
```

## Usage

```bash
# Voice mode (default)
uv run python main.py

# Text mode (no mic)
uv run python main.py --text

# With spoken response
uv run python main.py --speak
```

## Stack

| Component | Model / Lib |
|-----------|-------------|
| STT | Voxtral Transcribe 2 |
| LLM | Mistral Small |
| TTS | Voxtral Mini TTS |
| Audio | sounddevice |
| GitHub | PyGithub |
