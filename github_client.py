"""GitHub data fetching via PyGithub."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from github import Github

from config import GITHUB_REPO, GITHUB_TOKEN, GITHUB_USERNAME

_github = None
_repo = None


def _get_repo():
    """Get the configured GitHub repository (cached)."""
    global _github, _repo
    if _repo is None:
        _github = Github(GITHUB_TOKEN)
        _repo = _github.get_repo(GITHUB_REPO)
    return _repo


def get_assigned_issues() -> list[dict]:
    """Fetch open issues assigned to the user."""
    repo = _get_repo()
    issues = repo.get_issues(state="open", assignee=GITHUB_USERNAME)

    return [
        {
            "number": issue.number,
            "title": issue.title,
            "labels": [l.name for l in issue.labels],
            "created_at": issue.created_at.isoformat(),
            "comments": issue.comments,
            "url": issue.html_url,
        }
        for issue in issues
        if not issue.pull_request
    ]


def get_open_prs() -> list[dict]:
    """Fetch open PRs authored by or assigned to the user."""
    repo = _get_repo()
    pulls = repo.get_pulls(state="open")

    result = []
    for pr in pulls:
        if pr.user.login == GITHUB_USERNAME or any(
            a.login == GITHUB_USERNAME for a in pr.assignees
        ):
            result.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "draft": pr.draft,
                "mergeable_state": pr.mergeable_state,
                "review_comments": pr.review_comments,
                "url": pr.html_url,
            })

    return result


def get_recent_commits() -> list[dict]:
    """Fetch commits from the last 24 hours by the user."""
    repo = _get_repo()
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    commits = repo.get_commits(author=GITHUB_USERNAME, since=since)

    return [
        {
            "sha": c.sha[:7],
            "message": c.commit.message.split("\n")[0],
            "branch": c.commit.tree.sha[:7],
            "date": c.commit.author.date.isoformat(),
        }
        for c in commits
    ]


def get_issue_detail(issue_number: int) -> dict:
    """Fetch detailed info about a specific issue."""
    repo = _get_repo()
    issue = repo.get_issue(issue_number)

    comments = [
        {
            "author": c.user.login,
            "body": c.body[:200],
            "date": c.created_at.isoformat(),
        }
        for c in issue.get_comments()
    ]

    linked_prs = []
    for event in issue.get_events():
        if event.event == "cross-referenced" and event.source:
            if hasattr(event.source, "issue") and event.source.issue.pull_request:
                linked_prs.append(event.source.issue.number)

    return {
        "number": issue.number,
        "title": issue.title,
        "body": issue.body[:500] if issue.body else "",
        "state": issue.state,
        "assignees": [a.login for a in issue.assignees],
        "labels": [l.name for l in issue.labels],
        "comments": comments,
        "linked_prs": linked_prs,
        "created_at": issue.created_at.isoformat(),
        "url": issue.html_url,
    }


def fetch_context() -> dict:
    """Fetch all GitHub context for the daily briefing (parallel)."""
    with ThreadPoolExecutor(max_workers=3) as pool:
        issues_fut = pool.submit(get_assigned_issues)
        prs_fut = pool.submit(get_open_prs)
        commits_fut = pool.submit(get_recent_commits)

    return {
        "issues": issues_fut.result(),
        "prs": prs_fut.result(),
        "commits": commits_fut.result(),
    }
