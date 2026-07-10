"""
jukebox

discover, load, and validate theme manifests
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from src.jukebox.models import Author, Links, Palette, Theme, slugifyText

# bundled themes directory lives alongside jukebox package
_BUNDLED_THEMES_DIRECTORY = Path(__file__).resolve().parent.parent / "themes"


def resolveThemesDirectory(cli_override: str | None = None) -> Path:
    """
    resolve themes directory in this order:
      1. cli --themes-dir flag
      2. jukebox_themes_dir environment variable
      3. bundled themes (site-packages/themes/ or src/themes/)
      4. ~/.local/share/jukebox/themes/
    """
    if cli_override is not None:
        return Path(cli_override)

    env_value = os.environ.get("JUKEBOX_THEMES_DIR")

    if env_value is not None:
        return Path(env_value)

    if _BUNDLED_THEMES_DIRECTORY.is_dir():
        return _BUNDLED_THEMES_DIRECTORY

    xdg_data = Path(
        os.environ.get(
            "XDG_DATA_HOME",
            Path.home() / ".local" / "share",
        ),
    )

    return xdg_data / "jukebox" / "themes"


def discoverThemes(themes_dir: Path | None = None) -> list[Path]:
    """walk themes directory and return all theme.yaml paths."""
    if themes_dir is None:
        themes_dir = resolveThemesDirectory()

    return sorted(themes_dir.rglob("theme.yaml"))


def loadManifest(manifest_path: Path) -> Theme:
    """load a single theme.yaml into a Theme model."""
    manifest_data = yaml.safe_load(manifest_path.read_text())

    palette = Palette(
        **{
            key: manifest_data["palette"][key]
            for key in Palette.__dataclass_fields__
            if manifest_data.get("palette", {}).get(key) is not None
        },
    )

    link_data = manifest_data.get("link") or {}
    links = Links(**link_data) if link_data else None

    author_data = manifest_data.get("author")
    author = Author(**author_data) if author_data else None

    theme_name: str = manifest_data["name"]
    artist_name: str = manifest_data["artist"]

    return Theme(
        name=theme_name,
        artist=artist_name,
        release_type=manifest_data.get("type", "album"),
        year=manifest_data.get("year"),
        link=links,
        author=author,
        palette=palette,
        slug=slugifyText(theme_name),
        artist_slug=slugifyText(artist_name),
        source_path=manifest_path,
    )


def loadAllThemes(
    themes_dir: Path | None = None,
) -> list[Theme]:
    """discover and load every theme manifest."""
    return [loadManifest(manifest_path) for manifest_path in discoverThemes(themes_dir)]
