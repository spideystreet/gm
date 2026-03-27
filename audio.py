"""Microphone recording via sounddevice with silence detection."""

import io
import wave

import numpy as np
import sounddevice as sd

from config import CHANNELS, MAX_RECORD_SECONDS, SAMPLE_RATE, SILENCE_DURATION, SILENCE_THRESHOLD


def record() -> bytes:
    """Record audio from microphone, stops after silence is detected."""
    chunk_size = int(SAMPLE_RATE * 0.1)  # 100ms chunks
    silence_chunks = int(SILENCE_DURATION / 0.1)
    max_chunks = int(MAX_RECORD_SECONDS / 0.1)

    chunks = []
    silent_count = 0
    has_speech = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16") as stream:
        for _ in range(max_chunks):
            data, _ = stream.read(chunk_size)
            chunks.append(data.copy())

            level = np.abs(data).mean()
            if level > SILENCE_THRESHOLD:
                has_speech = True
                silent_count = 0
            else:
                silent_count += 1

            if has_speech and silent_count >= silence_chunks:
                break

    audio = np.concatenate(chunks)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    buf.seek(0)
    return buf.read()
