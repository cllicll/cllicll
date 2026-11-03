#!/usr/bin/env python3
"""Create dependency-free SVG cards from GitHub public repository metadata."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = os.getenv("PROFILE_USERNAME", "cllicll")
TOKEN = os.getenv("GITHUB_TOKEN")
ASSETS = Path(__file__).resolve().parents[1] / "assets"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "profile-card-generator", "X-GitHub-Api-Version": "2022-11-28"}
if TOKEN:
    HEADERS["Authorization"] = "Bearer " + TOKEN

THEMES = {
    "dark": ("#0D1117", "#30363D", "#C4B5FD", "#E6EDF3", "#9DA7B5"),
    "light": ("#FFFFFF", "#E5E7EB", "#6D28D9", "#24292F", "#57606A"),
}
LANG_COLORS = {"Dart":"#00B4AB", "TypeScript":"#3178C6", "JavaScript":"#F1E05A", "Swift":"#F05138", "Python":"#3572A5", "Kotlin":"#A97BFF", "Java":"#B07219", "HTML":"#E34C26", "CSS":"#563D7C", "Go":"#00ADD8"}


def api(path):
    req = Request("https://api.github.com" + path, headers=HEADERS)
    with urlopen(req, timeout=20) as response:
        return json.load(response)


def public_repos():
    profile = api("/users/" + USER)
    if profile.get("login", "").lower() != USER.lower():
        raise RuntimeError("Unexpected GitHub user")
    result = []
    for page in range(1, 21):
        batch = api(f"/users/{USER}/repos?type=owner&sort=full_name&per_page=100&page={page}")
        if not isinstance(batch, list):
            raise RuntimeError("Invalid API response")
        result.extend(r for r in batch if not r.get("private", False))
        if len(batch) < 100:
            return result
    raise RuntimeError("Too many pages; refusing incomplete metrics")


def tx(x, y, value, size, color, weight=400, anchor=None):
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}"{anchor_attr}>{escape(str(value))}</text>'


def rect(x, y, width, height, fill, radius=0):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" fill="{fill}"/>'


def card(title, description, lines, theme, height):
    bg, border, accent, fg, muted = THEMES[theme]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height}" viewBox="0 0 460 {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)}</title>', f'<desc id="desc">{escape(description)}</desc>',
             '<style>text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif}</style>',
             f'<rect x="1" y="1" width="458" height="{height-2}" rx="14" fill="{bg}" stroke="{border}"/>',
             tx(26, 40, title, 21, accent, 700),
             f'<path d="M26 55 H434" stroke="{border}"/>'] + lines + ["</svg>"]
    return "\n".join(parts) + "\n"


def stats(repos, theme):
    bg, border, accent, fg, muted = THEMES[theme]
    original = [r for r in repos if not r.get("fork")]
    items = [("Public repositories", len(repos)), ("Original repositories", len(original)),
             ("Stars received", sum(r.get("stargazers_count", 0) for r in original)),
             ("Forks received", sum(r.get("forks_count", 0) for r in original))]
    lines = []
    for i, (label, value) in enumerate(items):
        y = 91 + i*29
        lines.extend([tx(26, y, label, 14, muted), tx(432, y, f"{value:,}", 17, fg, 700, "end")])
    lines.append(tx(26, 195, "Source: public GitHub repositories", 11, muted))
    return card("GitHub Overview", "Public repository counts, stars and forks; private repositories excluded.", lines, theme, 215)


def technology_focus(theme):
    """Declared technology focus, not inferred language percentages."""
    bg, border, accent, fg, muted = THEMES[theme]
    groups = [
        ("Mobile", "Flutter / Dart", "#00B4AB"),
        ("iOS learning", "Swift / SwiftUI", "#F05138"),
        ("Backend", "Node.js / NestJS", "#3178C6"),
        ("Data", "PostgreSQL / Redis", "#8B5CF6"),
    ]
    lines = []
    for index, (label, value, color) in enumerate(groups):
        y = 91 + index * 33
        lines.extend([
            rect(26, y - 12, 9, 9, color, 3),
            tx(45, y, label, 13, muted),
            tx(431, y, value, 13, fg, 600, "end"),
        ])
    lines.append(tx(26, 235, "Declared stack - not repository language statistics", 11, muted))
    return card("Technology Focus", "Self-described engineering stack; not measured repository usage.", lines, theme, 255)


def main():
    repos = public_repos()
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"stats-{theme}.svg").write_text(stats(repos, theme), encoding="utf-8")
        (ASSETS / f"languages-{theme}.svg").write_text(technology_focus(theme), encoding="utf-8")
    print(f"Generated SVG cards for {USER}: {len(repos)} public repositories")


if __name__ == "__main__":
    main()
