"""gm — your morning standup, replaced."""

import sys
from concurrent.futures import ThreadPoolExecutor, Future

from mistralai.client import Mistral
from rich.console import Console
from rich.live import Live
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
    speak_mode = "--no-speak" not in sys.argv

    client = Mistral(api_key=MISTRAL_API_KEY)
    pool = ThreadPoolExecutor(max_workers=2)

    # Start GitHub fetch immediately (independent of voice input)
    from github_client import fetch_context
    context_fut: Future = pool.submit(fetch_context)

    if text_mode:
        query = console.input("[bold]>[/] ")
    else:
        console.print("[dim]Listening...[/]")
        try:
            from audio import record
            from voxtral import transcribe

            audio_data = record()
            console.print("[dim]Transcribing...[/]")
            query = transcribe(client, audio_data)
        except Exception as e:
            console.print(f"[red]Audio error: {e}[/]")
            console.print("[dim]Falling back to text input.[/]")
            query = console.input("[bold]>[/] ")

    console.print(f"[dim]> {query}[/]\n")

    from brain import generate_briefing_stream

    try:
        # Wait for GitHub context (likely already done during recording)
        context = context_fut.result()

        # Stream LLM response with live display
        full_text = ""
        with Live(Panel("...", title="[bold]gm[/]", border_style="green"), console=console, refresh_per_second=10) as live:
            for chunk in generate_briefing_stream(client, query, context):
                full_text += chunk
                live.update(Panel(full_text, title="[bold]gm[/]", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        sys.exit(1)

    if speak_mode:
        try:
            from voxtral import speak_chunked

            speak_chunked(client, full_text)
        except Exception as e:
            console.print(f"[dim]TTS error: {e}[/]")

    pool.shutdown(wait=False)


if __name__ == "__main__":
    main()
