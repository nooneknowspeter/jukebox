"""
jukebox

data models for theme manifests
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import regex

HEX_COLOR_RE = regex.compile(r"^#[0-9a-fA-F]{6}$")

PALETTE_BASE_KEYS = [
    "base00",
    "base01",
    "base02",
    "base03",
    "base04",
    "base05",
    "base06",
    "base07",
    "base08",
    "base09",
    "base0A",
    "base0B",
    "base0C",
    "base0D",
    "base0E",
    "base0F",
]


@dataclass
class Author:
    name: str
    github: str | None = None


@dataclass
class Links:
    cover: str | None = None
    spotify: str | None = None
    wikipedia: str | None = None


@dataclass
class Palette:
    # base16 canonical colors
    base00: str
    base01: str
    base02: str
    base03: str
    base04: str
    base05: str
    base06: str
    base07: str
    base08: str
    base09: str
    base0A: str
    base0B: str
    base0C: str
    base0D: str
    base0E: str
    base0F: str

    # neovim black-metal theme fields
    alt: str = "#5f8787"
    alt_bg: str = "#121212"
    bg: str = "#000000"
    comment: str = "#505050"
    constant: str = "#aaaaaa"
    fg: str = "#c1c1c1"
    func: str = "#888888"
    keyword: str = "#999999"
    line: str = "#000000"
    number: str = "#aaaaaa"
    operator: str = "#9b99a3"
    property: str = "#c1c1c1"
    string: str = "#ddeecc"
    type: str = "#999999"
    visual: str = "#333333"
    diag_red: str = "#5f8787"
    diag_blue: str = "#999999"
    diag_yellow: str = "#5f8787"
    diag_green: str = "#6e4c4c"

    def colormap(self) -> dict[str, str]:
        """terminal color mapping (black-metal colormap)."""
        return {
            "black": self.alt_bg,
            "grey": self.comment,
            "red": self.diag_red,
            "orange": self.number,
            "green": self.property,
            "yellow": self.func,
            "blue": self.constant,
            "purple": self.keyword,
            "magenta": self.type,
            "cyan": self.string,
            "white": self.fg,
        }

    def resolve(self, key: str) -> str:
        try:
            color_value = getattr(
                self,
                key,
            )

        except AttributeError:
            error_message = f"unknown palette key: {key}"

            raise KeyError(error_message) from None

        if color_value is None:
            error_message = f"palette key '{key}' is not set"

            raise KeyError(error_message)

        return color_value

    def as_dict(self) -> dict[str, str]:
        return {
            key: value
            for key, value in self.__dict__.items()
            if value is not None and HEX_COLOR_RE.match(value)
        }


@dataclass
class Theme:
    name: str
    artist: str
    release_type: str = "album"
    year: int | None = None
    link: Links | None = None
    author: Author | None = None
    palette: Palette = field(default_factory=Palette)

    slug: str = ""
    artist_slug: str = ""
    source_path: Path = field(default_factory=Path)

    def __post_init__(self):
        if not self.slug:
            self.slug = slugifyText(self.name)

        if not self.artist_slug:
            self.artist_slug = slugifyText(self.artist)


def slugifyText(text: str) -> str:
    return regex.sub(
        r"[^a-z0-9]+",
        "-",
        text.lower(),
    ).strip("-")
