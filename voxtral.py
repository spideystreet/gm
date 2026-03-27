"""Speech-to-text and TTS via Mistral API."""

import base64
import io
import re
import wave
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import sounddevice as sd

from config import STT_MODEL, TTS_MODEL


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


def _tts_chunk(client, text: str) -> bytes | None:
    """Synthesize a single text chunk to raw audio bytes."""
    try:
        response = client.audio.speech.complete(
            model=TTS_MODEL,
            input=text,
            response_format="wav",
        )
        return base64.b64decode(response.audio_data)
    except Exception:
        return None


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences for chunked TTS."""
    parts = re.split(r'(?<=[.!?:])\s+', text.strip())
    # Group small parts together (min ~40 chars per chunk)
    chunks = []
    current = ""
    for part in parts:
        current += (" " if current else "") + part
        if len(current) >= 40:
            chunks.append(current)
            current = ""
    if current:
        chunks.append(current)
    return chunks


def speak_chunked(client, text: str) -> None:
    """Synthesize and play speech chunk by chunk for lower latency."""
    sentences = _split_sentences(text)
    if not sentences:
        return

    # Pre-fetch TTS for first chunks in parallel while playing
    pool = ThreadPoolExecutor(max_workers=2)
    futures = []
    for sentence in sentences:
        futures.append(pool.submit(_tts_chunk, client, sentence))

    for fut in futures:
        wav_bytes = fut.result()
        if wav_bytes is None:
            continue

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            rate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
            dtype = "int16" if wf.getsampwidth() == 2 else "int32"

        audio = np.frombuffer(frames, dtype=dtype)
        if channels > 1:
            audio = audio.reshape(-1, channels)

        sd.play(audio, samplerate=rate)
        sd.wait()

    pool.shutdown(wait=False)
