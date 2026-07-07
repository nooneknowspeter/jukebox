"""
jukebox

command-line interface
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src.jukebox.generator import (
    EXTENSION_MAP,
    OUTPUT_DIRECTORY,
    TEMPLATES_DIRECTORY,
    buildEnv,
    generateAll,
)
from src.jukebox.manifest import loadAllThemes, resolveThemesDirectory
from src.jukebox.screenshots import buildAllScreenshots, retrieveCoverArt


def _readVersion() -> str:
    """read version from importlib.metadata, falling back to pyproject.toml."""
    try:
        import importlib.metadata

        return importlib.metadata.version("jukebox")
    except Exception:
        pass

    pyproject = Path(__file__).resolve().parent.parent.parent.parent / "pyproject.toml"

    if pyproject.is_file():
        for line in pyproject.read_text().splitlines():
            stripped = line.strip()

            if stripped.startswith("version"):
                return stripped.split("=")[1].strip().strip('"').strip("'")

    return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="jukebox",
        description="create themes from music cover art manifests",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"jukebox {_readVersion()}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="list all available themes")

    show_parser = subparsers.add_parser("show", help="show theme details")
    show_parser.add_argument("theme", help="theme slug (artist-album)")

    generate_parser = subparsers.add_parser(
        "generate",
        help="generate theme output files",
    )
    generate_parser.add_argument(
        "theme",
        nargs="?",
        help="specific theme slug (leave empty for all)",
    )
    generate_parser.add_argument(
        "--target",
        "-t",
        action="append",
        help="target format (e.g. ghostty, wezterm)",
    )
    generate_parser.add_argument(
        "--themes-dir",
        type=Path,
        help="override themes directory",
    )

    subparsers.add_parser(
        "env",
        help="show environment variables and constant values",
    )

    screenshot_parser = subparsers.add_parser(
        "screenshot",
        help="generate composite images (cover art + palette swatches)",
    )
    screenshot_parser.add_argument(
        "theme",
        nargs="?",
        help="specific theme slug (leave empty for all)",
    )

    cover_parser = subparsers.add_parser(
        "cover",
        help="download cover art for a theme",
    )
    cover_parser.add_argument("theme", help="theme slug")
    cover_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("assets/screenshots"),
        help="output directory",
    )

    cli_args = parser.parse_args()

    if cli_args.command == "env":
        jukebox_themes_dir_env = os.environ.get("JUKEBOX_THEMES_DIR", "not set")
        xdg_data_home_env = os.environ.get("XDG_DATA_HOME", "not set")
        resolved_themes = resolveThemesDirectory()

        print(f"version:              {_readVersion()}")
        print(f"JUKEBOX_THEMES_DIR:   {jukebox_themes_dir_env}")
        print(f"XDG_DATA_HOME:        {xdg_data_home_env}")
        print(f"themes directory:     {resolved_themes}")
        print(f"templates directory:  {TEMPLATES_DIRECTORY}")
        print(f"output directory:     {OUTPUT_DIRECTORY}")
        print(f"extension map:        {EXTENSION_MAP}")

        return

    if cli_args.command in ("show", "generate"):
        themes_directory = resolveThemesDirectory(
            str(cli_args.themes_dir) if getattr(cli_args, "themes_dir", None) else None,
        )
    else:
        themes_directory = resolveThemesDirectory()

    all_themes = loadAllThemes(themes_directory)

    if cli_args.command == "list":
        for theme in all_themes:
            author_name = theme.author.name if theme.author else "unknown"

            print(
                f"  {theme.artist_slug}/{theme.slug:<40}"
                f" {theme.name:<40}"
                f" {theme.artist:<30}"
                f" by {author_name}",
            )

    elif cli_args.command == "show":
        for theme in all_themes:
            combined_slug = f"{theme.artist_slug}-{theme.slug}"

            if cli_args.theme not in (
                combined_slug,
                theme.slug,
                theme.name.lower(),
            ):
                continue

            print(f"name:     {theme.name}")
            print(f"artist:   {theme.artist}")
            print(f"type:     {theme.release_type}")
            print(f"year:     {theme.year or 'n/a'}")
            print(f"author:   {theme.author.name if theme.author else 'n/a'}")
            print(f"path:     {theme.source_path}")
            print("palette:")

            for key, value in theme.palette.as_dict().items():
                print(f"  {key}: {value}")

            return

        print(f"theme '{cli_args.theme}' not found", file=sys.stderr)
        sys.exit(1)

    elif cli_args.command == "generate":
        jinja_env = buildEnv()
        target_list = cli_args.target or None

        generateAll(jinja_env, all_themes, targets=target_list)

    elif cli_args.command == "screenshot":
        buildAllScreenshots(
            all_themes
            if not cli_args.theme
            else [
                theme
                for theme in all_themes
                if any(
                    cli_args.theme in (f"{theme.artist_slug}-{theme.slug}", theme.slug)
                )
            ],
        )

    elif cli_args.command == "cover":
        for theme in all_themes:
            combined_slug = f"{theme.artist_slug}-{theme.slug}"

            if cli_args.theme not in (
                combined_slug,
                theme.slug,
                theme.name.lower(),
            ):
                continue

            cover_art_url: str | None = None

            if theme.link:
                cover_art_url = (
                    theme.link.cover or theme.link.spotify or theme.link.wikipedia
                )

            cli_args.output.mkdir(parents=True, exist_ok=True)
            output_filename = f"{theme.artist_slug}-{theme.slug}.png"
            retrieveCoverArt(
                url=cover_art_url,
                output_filename=str(cli_args.output / output_filename),
            )
            print(f"saved to {cli_args.output / output_filename}")

            return

        print(f"theme '{cli_args.theme}' not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
