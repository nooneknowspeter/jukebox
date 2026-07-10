"""
jukebox

theme helper
generate theme from cover art image
"""

import sys
from pathlib import Path

import yaml

from src.jukebox.cv import generateRandomPalette, runJukeboxPicker

from src.jukebox.models import PALETTE_BASE_KEYS


def _buildThemeManifest(palette_hex_colors: list[str]) -> dict:
    """build theme.yaml dict from 16 hex colors."""
    palette_entries: dict[str, str] = {}

    for palette_index, palette_key in enumerate(PALETTE_BASE_KEYS):
        palette_entries[palette_key] = palette_hex_colors[palette_index]

    return {
        "name": "untitled",
        "artist": "unknown",
        "type": "album",
        "year": 2025,
        "palette": palette_entries,
    }


def _writeThemeYaml(theme_manifest: dict, output_path: Path) -> None:
    """write theme manifest dict to yaml file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as output_file:
        yaml.dump(theme_manifest, output_file, default_flow_style=False)

    print(f"exported theme.yaml to {output_path}")


def init(
    cover_art_image_path: str,
    output_path: str = "theme.yaml",
    is_gui: bool = False,
) -> None:
    """generate theme palette from cover art and write to yaml."""
    if is_gui:
        palette_hex_colors = runJukeboxPicker(
            cover_art_image_path=cover_art_image_path,
        )
    else:
        palette_hex_colors = generateRandomPalette(
            cover_art_image_path=cover_art_image_path,
        )

    if not palette_hex_colors:
        print("no palette generated", file=sys.stderr)
        sys.exit(1)

    theme_manifest = _buildThemeManifest(palette_hex_colors)
    _writeThemeYaml(theme_manifest, Path(output_path))
