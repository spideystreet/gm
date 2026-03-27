"""LLM reasoning via Mistral Small."""

import json
import re
from collections.abc import Iterator

from config import LLM_MODEL
from github_client import get_issue_detail

BRIEFING_PROMPT = """\
You are a concise dev assistant. The user just said: "{query}"

Here is their GitHub context for today:

**Assigned Issues ({issue_count}):**
{issues}

**Open PRs ({pr_count}):**
{prs}

**Commits (last 24h, {commit_count}):**
{commits}

Give a clear, actionable morning briefing. Be concise — bullet points, no fluff.
If the user asked a specific question, answer it directly using the context.
If they asked about a specific issue number, use the detailed info provided.
Always mention what needs attention first (failing CI, review requests, high priority)."""


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


def _build_prompt(query: str, context: dict) -> str:
    """Build the LLM prompt from query and pre-fetched context."""
    issue_number = _extract_issue_number(query)
    extra = ""
    if issue_number:
        try:
            detail = get_issue_detail(issue_number)
            extra = f"\n**Detail for #{issue_number}:**\n{json.dumps(detail, indent=2)}"
        except Exception:
            extra = f"\n(Could not fetch details for #{issue_number})"

    issues_text = _format_issues(context["issues"])
    prs_text = _format_prs(context["prs"])
    commits_text = _format_commits(context["commits"])

    return BRIEFING_PROMPT.format(
        query=query,
        issue_count=len(context["issues"]),
        issues=issues_text + extra,
        pr_count=len(context["prs"]),
        prs=prs_text,
        commit_count=len(context["commits"]),
        commits=commits_text,
    )


def generate_briefing_stream(client, query: str, context: dict) -> Iterator[str]:
    """Stream the briefing token by token."""
    prompt = _build_prompt(query, context)

    for chunk in client.chat.stream(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
    ):
        delta = chunk.data.choices[0].delta.content
        if delta:
            yield delta
