"""gm — your morning standup, replaced."""

import sys

from mistralai.client import Mistral
from rich.console import Console
from rich.panel import Panel

from config import GITHUB_REPO, GITHUB_TOKEN, GITHUB_USERNAME, MISTRAL_API_KEY

console = Console()


def main() -> None:
    """Entry point for gm."""
    missing = []
    if not MISTRAL_API_KEY:
        missing.append("MISTRAL_API_KEY")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not GITHUB_REPO:
        missing.append("GITHUB_REPO")
    if not GITHUB_USERNAME:
        missing.append("GITHUB_USERNAME")

    if missing:
        console.print(
            Panel(
                f"Missing env vars: {', '.join(missing)}\n"
                "Add them to .env or export them.",
                title="[bold]gm[/]",
                border_style="red",
            )
        )
        sys.exit(1)

    text_mode = "--text" in sys.argv
    speak_mode = "--speak" in sys.argv

    client = Mistral(api_key=MISTRAL_API_KEY)

    if text_mode:
        query = console.input("[bold]>[/] ")
    else:
        console.print("[dim]Listening...[/]")
        try:
            from audio import record
            from voxtral import transcribe

            audio_data = record()
            query = transcribe(client, audio_data)
        except Exception as e:
            console.print(f"[red]Audio error: {e}[/]")
            console.print("[dim]Falling back to text input.[/]")
            query = console.input("[bold]>[/] ")

    console.print(f"[dim]> {query}[/]\n")

    from brain import generate_briefing

    try:
        briefing = generate_briefing(client, query)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)

    console.print(Panel(briefing, title="[bold]gm[/]", border_style="green"))

    if speak_mode:
        try:
            from voxtral import speak

            speak(client, briefing)
        except Exception as e:
            console.print(f"[dim]TTS error: {e}[/]")


if __name__ == "__main__":
    main()
