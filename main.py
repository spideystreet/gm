"""gm — your morning standup, replaced."""

import sys
from concurrent.futures import ThreadPoolExecutor, Future

from mistralai.client import Mistral
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text

from config import GITHUB_REPO, GITHUB_TOKEN, GITHUB_USERNAME, MISTRAL_API_KEY

console = Console()


def _render_chat(history: list[dict], streaming: str | None = None) -> Text:
    """Render chat history as conversation bubbles."""
    output = Text()
    for msg in history:
        if msg["role"] == "user":
            output.append("  🎙 ", style="bold cyan")
            output.append(msg["content"], style="cyan")
            output.append("\n\n")
        elif msg["role"] == "assistant":
            output.append("  🤖 ", style="bold green")
            output.append(msg["content"], style="green")
            output.append("\n\n")

    if streaming is not None:
        output.append("  🤖 ", style="bold green")
        output.append(streaming or "...", style="green")

    return output


def _get_query(client, text_mode: bool) -> str:
    """Get user input via voice or text."""
    if text_mode:
        return console.input("[bold cyan]>[/] ")

    console.print("[dim]🎙 Listening...[/]")
    try:
        from audio import record
        from voxtral import transcribe

        audio_data = record()
        query = transcribe(client, audio_data)
        return query
    except Exception as e:
        console.print(f"[red]Audio error: {e}[/]")
        return console.input("[bold cyan]>[/] ")


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

    # Fetch GitHub context once at startup
    from github_client import fetch_context
    context_fut: Future = pool.submit(fetch_context)

    from brain import build_system_message, enrich_query, stream_response

    console.print(Panel("[bold]gm[/] — voice conversation mode\n[dim]Ctrl+C to quit[/]", border_style="blue"))

    # First query while GitHub context loads
    query = _get_query(client, text_mode)

    context = context_fut.result()
    messages = [build_system_message(context)]
    chat_history: list[dict] = []

    # Conversation loop
    while True:
        chat_history.append({"role": "user", "content": query})

        enriched = enrich_query(query)
        messages.append({"role": "user", "content": enriched})

        full_text = ""
        token_stream = stream_response(client, messages)

        if speak_mode:
            from voxtral import speak_streaming
            token_stream = speak_streaming(client, token_stream)

        with Live(
            _render_chat(chat_history, streaming="..."),
            console=console,
            refresh_per_second=15,
            vertical_overflow="visible",
        ) as live:
            for chunk in token_stream:
                full_text += chunk
                live.update(_render_chat(chat_history, streaming=full_text))

            # Add to history inside Live so final render includes it
            messages.append({"role": "assistant", "content": full_text})
            chat_history.append({"role": "assistant", "content": full_text})
            live.update(_render_chat(chat_history))

        # Next turn
        try:
            query = _get_query(client, text_mode)
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]bye![/]")
            break

        if not query.strip():
            continue

    pool.shutdown(wait=False)


if __name__ == "__main__":
    main()
