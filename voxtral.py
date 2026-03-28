"""Speech-to-text and TTS via Mistral API."""

import base64
import json
import queue
import re
import threading
from collections.abc import Iterator

import httpx
import numpy as np
import sounddevice as sd

from config import (
    AUDIO_OUTPUT_DEVICE,
    MISTRAL_API_KEY,
    STT_MODEL,
    TTS_MODEL,
    TTS_VOICE_ID,
)

TTS_SAMPLE_RATE = 24000
TTS_API_URL = "https://api.mistral.ai/v1/audio/speech"


def transcribe(client, audio_data: bytes) -> str:
    """Transcribe WAV audio bytes to text."""
    result = client.audio.transcriptions.complete(
        model=STT_MODEL,
        file={
            "file_name": "recording.wav",
            "content": audio_data,
            "content_type": "audio/wav",
        },
        language="fr",
    )
    return result.text.strip()


def _play_pcm(pcm_bytes: bytes) -> None:
    """Play raw PCM float32 audio at 24kHz."""
    audio = np.frombuffer(pcm_bytes, dtype=np.float32)
    if len(audio) == 0:
        return
    sd.play(audio, samplerate=TTS_SAMPLE_RATE, device=AUDIO_OUTPUT_DEVICE)
    sd.wait()


def _stream_tts_to_queue(text: str, audio_queue: queue.Queue) -> None:
    """Stream TTS via SSE and push PCM chunks directly to the audio queue."""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "model": TTS_MODEL,
        "input": text,
        "response_format": "pcm",
        "stream": True,
    }
    if TTS_VOICE_ID:
        payload["voice_id"] = TTS_VOICE_ID

    try:
        with httpx.stream(
            "POST", TTS_API_URL, headers=headers, json=payload, timeout=30,
        ) as response:
            for line in response.iter_lines():
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                obj = json.loads(data)
                audio_b64 = obj.get("data", {}).get("audio_data") or obj.get("audio_data")
                if audio_b64:
                    audio_queue.put(base64.b64decode(audio_b64))
    except Exception:
        pass


def speak_streaming(client, token_stream: Iterator[str]) -> Iterator[str]:
    """TTS that starts speaking while the LLM is still generating.

    Yields tokens back so the caller can still display them.
    Uses streaming PCM TTS for minimal latency.
    """
    audio_queue: queue.Queue[bytes | None] = queue.Queue()
    sentence_queue: queue.Queue[str | None] = queue.Queue()

    def _player() -> None:
        """Play audio chunks as they arrive."""
        while True:
            data = audio_queue.get()
            if data is None:
                break
            _play_pcm(data)

    def _tts_worker() -> None:
        """Process sentences sequentially to preserve order."""
        while True:
            text = sentence_queue.get()
            if text is None:
                break
            _stream_tts_to_queue(text, audio_queue)
        audio_queue.put(None)

    player_t = threading.Thread(target=_player, daemon=True)
    tts_t = threading.Thread(target=_tts_worker, daemon=True)
    player_t.start()
    tts_t.start()

    buffer = ""
    sentence_end = re.compile(r'[.!?:]\s')

    for token in token_stream:
        yield token
        buffer += token

        match = sentence_end.search(buffer)
        if match and len(buffer[:match.end()].strip()) >= 20:
            sentence = buffer[:match.end()].strip()
            buffer = buffer[match.end():]
            sentence_queue.put(sentence)

    if buffer.strip():
        sentence_queue.put(buffer.strip())

    sentence_queue.put(None)
    tts_t.join()
    player_t.join()
