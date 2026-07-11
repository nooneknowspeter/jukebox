"""
jukebox

export theme data to json and regenerate screenshots.md
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.jukebox.models import Theme


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = REPO_ROOT / "assets" / "screenshots"
COVERS_DIR = REPO_ROOT / "assets" / "covers"
FRONTEND_PUBLIC = REPO_ROOT / "frontend" / "public"
OUTPUT_DIR = REPO_ROOT / "output"

GITHUB_SCREENSHOT_BASE = (
    "https://raw.githubusercontent.com/nooneknowspeter/jukebox"
    "/refs/heads/develop/assets/screenshots"
)


def _themeToDict(theme: Theme) -> dict:
    """convert a theme model to a json-serializable dict."""
    combined_slug = f"{theme.artist_slug}-{theme.slug}"

    author = None
    if theme.author:
        author = {
            "name": theme.author.name,
            "github": theme.author.github,
        }

    link = None
    if theme.link:
        link = {
            "cover": theme.link.cover,
            "spotify": theme.link.spotify,
            "wikipedia": theme.link.wikipedia,
        }

    return {
        "slug": combined_slug,
        "name": theme.name,
        "artist": theme.artist,
        "release_type": theme.release_type,
        "year": theme.year,
        "author": author,
        "link": link,
        "palette": theme.palette.as_dict(),
        "images": {
            "screenshot": f"/assets/screenshots/{combined_slug}.png",
            "cover": f"/assets/covers/{combined_slug}.png",
        },
    }


def _copyAssets() -> None:
    """copy screenshots and covers to frontend/public/assets/."""
    for subfolder in ("screenshots", "covers"):
        src = REPO_ROOT / "assets" / subfolder
        dst = FRONTEND_PUBLIC / "assets" / subfolder

        if not src.is_dir():
            continue

        dst.mkdir(parents=True, exist_ok=True)

        for file in src.iterdir():
            if file.is_file():
                shutil.copy2(file, dst / file.name)


def exportThemesJson(themes: list[Theme]) -> None:
    """generate themes.json and copy assets to frontend."""
    themes_data = [_themeToDict(theme) for theme in themes]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_PUBLIC.mkdir(parents=True, exist_ok=True)

    json_content = json.dumps(themes_data, indent=4)

    output_path = OUTPUT_DIR / "themes.json"
    output_path.write_text(json_content)

    frontend_path = FRONTEND_PUBLIC / "themes.json"
    frontend_path.write_text(json_content)

    _copyAssets()

    print(f"wrote {output_path}")
    print(f"wrote {frontend_path}")
    print(f"copied assets to {FRONTEND_PUBLIC / 'assets'}")


def exportScreenshotsMd(themes: list[Theme]) -> None:
    """regenerate SCREENSHOTS.md from theme data."""
    sorted_themes = sorted(themes, key=lambda t: (t.artist.lower(), t.name.lower()))

    lines = [
        "# screenshots",
        "",
        "composite images showing cover art alongside base16 palette swatches.",
        "",
        "| | theme | artist | year |",
        "| --- | --- | --- | ---- |",
    ]

    for theme in sorted_themes:
        combined_slug = f"{theme.artist_slug}-{theme.slug}"
        img_url = f"{GITHUB_SCREENSHOT_BASE}/{combined_slug}.png"
        year_str = str(theme.year) if theme.year else "n/a"

        lines.append(
            f"| ![{theme.name}]({img_url})"
            f" | {theme.name}"
            f" | {theme.artist}"
            f" | {year_str} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            f"_{len(sorted_themes)} themes_",
            "",
        ]
    )

    screenshots_path = REPO_ROOT / "SCREENSHOTS.md"
    screenshots_path.write_text("\n".join(lines))

    print(f"wrote {screenshots_path}")
