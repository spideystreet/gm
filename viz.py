"""Terminal audio waveform visualizations — Mistral pixel aesthetic."""

import math
import time

from rich.text import Text

BARS = " ▁▂▃▄▅▆▇█"
NUM_BARS = 30

# Mistral orange palette
ORANGE = "#ff7000"
ORANGE_MID = "#cc5500"
ORANGE_DIM = "#884400"


def _bar(value: float) -> str:
    """Convert 0.0-1.0 to a block character."""
    idx = int(value * (len(BARS) - 1))
    return BARS[min(idx, len(BARS) - 1)]


def render_listening(level: float, width: int = NUM_BARS) -> Text:
    """Waveform reacting to microphone input level."""
    t = time.monotonic()
    half = width // 2
    bars = []
    intensity = min(level / 300, 1.0)

    for i in range(half):
        dist = i / half
        wave = (
            math.sin(t * 6 + i * 0.7) * 0.35
            + math.sin(t * 9 + i * 0.4) * 0.25
            + 0.25
        )
        envelope = 1.0 - dist * 0.5
        height = wave * envelope * (0.2 + intensity * 0.8)
        bars.append(max(0.05, min(height, 1.0)))

    bars = list(reversed(bars)) + bars

    text = Text()
    text.append("\n    ◆  ", style="bold cyan")
    for b in bars:
        style = "bold cyan" if b > 0.6 else "cyan" if b > 0.3 else "dim cyan"
        text.append(_bar(b), style=style)
    text.append("\n")
    return text


def render_speaking(width: int = NUM_BARS) -> Text:
    """Animated waveform for TTS playback."""
    t = time.monotonic()
    half = width // 2
    bars = []

    for i in range(half):
        dist = i / half
        wave = (
            math.sin(t * 3.5 + i * 0.6) * 0.3
            + math.sin(t * 6 + i * 0.35) * 0.25
            + math.sin(t * 1.5 + i * 1.2) * 0.15
            + 0.4
        )
        envelope = 1.0 - dist * 0.5
        height = wave * envelope
        bars.append(max(0.05, min(height, 1.0)))

    bars = list(reversed(bars)) + bars

    text = Text()
    text.append("    ◆  ", style=f"bold {ORANGE}")
    for b in bars:
        if b > 0.6:
            style = f"bold {ORANGE}"
        elif b > 0.3:
            style = ORANGE_MID
        else:
            style = ORANGE_DIM
        text.append(_bar(b), style=style)
    text.append("\n")
    return text


class SpeakingWaveform:
    """Dynamic Rich renderable — re-generates waveform on every render cycle."""

    def __rich_console__(self, console, options):
        yield render_speaking()
