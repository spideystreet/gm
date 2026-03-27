"""Speech-to-text and TTS via Mistral API."""

import base64
import io
import wave

import sounddevice as sd
import numpy as np

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
        language="en",
    )
    return result.text.strip()


def speak(client, text: str) -> None:
    """Synthesize speech and play through speakers."""
    response = client.audio.speech.complete(
        model=TTS_MODEL,
        input=text,
        response_format="wav",
    )

    wav_bytes = base64.b64decode(response.audio_data)

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
