"""LLM reasoning via Mistral Small."""

import json
import re
from collections.abc import Iterator

from config import LLM_MODEL
from github_client import get_issue_detail

SYSTEM_PROMPT = """\
You are a concise dev assistant having a voice conversation with a developer.
You have access to their GitHub context below.

{context}

Rules:
- Use short, spoken French sentences. No markdown, no bullet points, no special characters.
- Be concise and conversational, like a quick chat with a colleague.
- If the user asks about a specific issue number, use the detailed info provided.
- Mention what needs attention first (failing CI, review requests, high priority).
- Never use asterisks, dashes, hashes, or any formatting — just plain spoken text."""


def _format_issues(issues: list[dict]) -> str:
    if not issues:
        return "None"
    return "\n".join(
        f"- #{i['number']} — {i['title']} ({', '.join(i['labels']) or 'no labels'}, {i['comments']} comments)"
        for i in issues
    )


def _format_prs(prs: list[dict]) -> str:
    if not prs:
        return "None"
    lines = []
    for pr in prs:
        status = "draft" if pr["draft"] else pr["mergeable_state"]
        lines.append(f"- #{pr['number']} — {pr['title']} ({status})")
    return "\n".join(lines)


def _format_commits(commits: list[dict]) -> str:
    if not commits:
        return "None in last 24h"
    return "\n".join(f"- {c['sha']} {c['message']}" for c in commits)


def _extract_issue_number(query: str) -> int | None:
    """Try to extract an issue number from the user query."""
    match = re.search(r"#?(\d+)", query)
    if match:
        return int(match.group(1))
    return None


def build_system_message(context: dict) -> dict:
    """Build the system message with GitHub context."""
    issues_text = _format_issues(context["issues"])
    prs_text = _format_prs(context["prs"])
    commits_text = _format_commits(context["commits"])

    context_block = (
        f"Assigned Issues ({len(context['issues'])}):\n{issues_text}\n\n"
        f"Open PRs ({len(context['prs'])}):\n{prs_text}\n\n"
        f"Commits (last 24h, {len(context['commits'])}):\n{commits_text}"
    )

    return {
        "role": "system",
        "content": SYSTEM_PROMPT.format(context=context_block),
    }


def enrich_query(query: str) -> str:
    """Fetch extra issue detail if the query mentions an issue number."""
    issue_number = _extract_issue_number(query)
    if issue_number:
        try:
            detail = get_issue_detail(issue_number)
            return f"{query}\n\n(Detail for #{issue_number}: {json.dumps(detail)})"
        except Exception:
            pass
    return query


def stream_response(client, messages: list[dict]) -> Iterator[str]:
    """Stream the LLM response token by token."""
    for chunk in client.chat.stream(
        model=LLM_MODEL,
        messages=messages,
    ):
        delta = chunk.data.choices[0].delta.content
        if delta:
            yield delta
