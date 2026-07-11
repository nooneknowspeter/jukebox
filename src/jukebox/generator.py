"""
jukebox

jinja2 template engine for rendering themes to output formats
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.jukebox.models import Theme


TEMPLATES_DIRECTORY = Path(__file__).resolve().parent / "templates"
OUTPUT_DIRECTORY = Path.cwd() / "output"

EXTENSION_MAP = {
    "ghostty": ".conf",
    "wezterm": ".toml",
    "kitty": ".conf",
    "alacritty": ".toml",
    "foot": ".ini",
    "tmux": ".conf",
    "yazi": ".toml",
    "tinted-theming": ".yaml",
}

TEMPLATE_TARGETS: dict[str, str] = {
    "ghostty": "terminal/ghostty.j2",
    "wezterm": "terminal/wezterm.j2",
    "tinted-theming": "misc/tinted-theming.j2",
}


COLOR_BIT_DEPTH: int = 2**8


def _hexStringConversion(hex_color: str) -> tuple[int, ...]:
    """
    intermediary function to convert hex color string to rgb tuple
    """
    hex_value: str = hex_color.lstrip("#")

    rgb_list: list[int] = [int(hex_value[index : index + 2], 16) for index in (0, 2, 4)]

    return tuple(rgb_list)


def _hex2rgb(hex_color: str) -> str:
    """
    convert #ff00aa to 255,0,170.
    """
    return ",".join(str(value) for value in _hexStringConversion(hex_color))


def _lighten(hex_color: str, amount: int = 10) -> str:
    """lighten a hex color by mixing with white."""
    red, green, blue = (value for value in _hexStringConversion(hex_color))

    red = min(
        COLOR_BIT_DEPTH,
        red + int((COLOR_BIT_DEPTH - red) * amount / 100),
    )
    green = min(
        COLOR_BIT_DEPTH,
        green + int((COLOR_BIT_DEPTH - green) * amount / 100),
    )
    blue = min(
        COLOR_BIT_DEPTH,
        blue + int((COLOR_BIT_DEPTH - blue) * amount / 100),
    )

    return f"#{red:02x}{green:02x}{blue:02x}"


def _darken(hex_color: str, amount: int = 10) -> str:
    """darken a hex color by mixing with black."""
    red, green, blue = (value for value in _hexStringConversion(hex_color))

    red = max(0, red - int(red * amount / 100))
    green = max(0, green - int(green * amount / 100))
    blue = max(0, blue - int(blue * amount / 100))

    return f"#{red:02x}{green:02x}{blue:02x}"


def buildEnv() -> Environment:
    """construct a jinja2 environment with jukebox filters."""
    template_loader = FileSystemLoader(str(TEMPLATES_DIRECTORY))

    jinja_env = Environment(
        loader=template_loader,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    jinja_env.filters["hex2rgb"] = _hex2rgb
    jinja_env.filters["lighten"] = _lighten
    jinja_env.filters["darken"] = _darken

    return jinja_env


def renderTemplate(
    jinja_env: Environment,
    template_name: str,
    theme: Theme,
    palette: dict[str, str],
) -> str:
    """render a single jinja2 template for one theme."""
    return jinja_env.get_template(template_name).render(
        theme=theme,
        palette=palette,
    )


def generateAll(
    jinja_env: Environment,
    themes: list[Theme],
    targets: list[str] | None = None,
) -> None:
    """generate all themes for all (or specified) output targets."""
    target_map: dict[str, str] = _discoverTargets(jinja_env)

    selected_targets: dict[str, str] = {
        target_name: template_path
        for target_name, template_path in target_map.items()
        if targets is None or target_name in targets
    }

    for theme in themes:
        resolved_palette = _resolvePalette(theme)

        for target_name, template_path in selected_targets.items():
            rendered_output = renderTemplate(
                jinja_env,
                template_path,
                theme,
                resolved_palette,
            )
            destination = (
                OUTPUT_DIRECTORY / target_name / f"{theme.artist_slug}-{theme.slug}"
            )

            _writeExact(destination, rendered_output, target_name)


def _resolvePalette(theme: Theme) -> dict[str, str]:
    """
    merge base16 with semantic aliases.
    aliases take precedence when present.
    """
    base_color_keys: list[str] = [
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
    alias_color_keys: list[str] = [
        "alt",
        "alt_bg",
        "bg",
        "fg",
        "string",
        "keyword",
        "func",
        "type",
        "comment",
        "constant",
        "number",
        "operator",
        "property",
        "line",
        "visual",
        "diag_red",
        "diag_blue",
        "diag_yellow",
        "diag_green",
    ]

    base_palette = {key: getattr(theme.palette, key) for key in base_color_keys}

    alias_palette = {
        key: getattr(theme.palette, key)
        for key in alias_color_keys
        if getattr(theme.palette, key) is not None
    }

    base_palette.update(alias_palette)

    return base_palette


def _writeExact(destination: Path, content: str, target_name: str) -> None:
    """write rendered content to the correct output path."""
    file_extension = EXTENSION_MAP.get(target_name, ".txt")
    destination = destination.with_suffix(file_extension)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    destination.write_text(content)


def _discoverTargets(jinja_env: Environment) -> dict[str, str]:
    """map target name to template path relative to templates directory."""
    return TEMPLATE_TARGETS
