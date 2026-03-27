"""Environment configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # format: owner/repo
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Mistral models
STT_MODEL = "voxtral-mini-transcribe-2507"
LLM_MODEL = "mistral-small-latest"
TTS_MODEL = "voxtral-mini-tts-2603"

# Audio settings
MAX_RECORD_SECONDS = 30
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 500
SILENCE_DURATION = 1.5  # seconds of silence before auto-stop
