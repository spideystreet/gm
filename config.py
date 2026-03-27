"""Environment configuration."""

import os

from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # format: owner/repo
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

# Mistral models
STT_MODEL = "voxtral-transcribe-2"
LLM_MODEL = "mistral-small-latest"
TTS_MODEL = "voxtral-mini-tts-2603"

# Audio settings
RECORD_SECONDS = 10
SAMPLE_RATE = 16000
CHANNELS = 1
