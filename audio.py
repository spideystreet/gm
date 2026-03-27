"""Microphone recording via sounddevice."""

import io
import wave

import numpy as np
import sounddevice as sd

from config import CHANNELS, RECORD_SECONDS, SAMPLE_RATE


def record() -> bytes:
    """Record audio from microphone and return WAV bytes."""
    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )
    sd.wait()

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    buf.seek(0)
    return buf.read()
