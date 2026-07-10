"""
jukebox

retrieve cover art from spotify, wikipedia, or direct urls
"""

# TODO: get root logger

from __future__ import annotations

import logging
from collections.abc import Mapping

import regex
import requests
from bs4 import BeautifulSoup

try:
    from PIL import Image, ImageDraw, ImageFont

    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

USER_AGENT_HEADER = (
    "jukebox/0.0 (https://github.com/nooneknowspeter/jukebox/; nooneknows)"
)

_IMAGE_URL_PATTERN = regex.compile(
    r"\.(jpe?g|png|gif|webp|bmp)(\?|$)|/(imgs|images|media|cdn)/",
    regex.IGNORECASE,
)


def _isImageUrl(url: str) -> bool:
    """check if a url points directly to an image file or proxy."""
    return _IMAGE_URL_PATTERN.search(url) is not None


def retrieveCoverArt(
    url: str | None = None,
    output_filename: str | None = None,
) -> None:
    """
    download cover art from a url.
    supports: direct image url, wikipedia page, spotify page.
    """
    if url is None:
        logging.info(f"url: {url}, please provide a url")

        return

    request_headers: Mapping[str, str | bytes] = {
        "User-Agent": USER_AGENT_HEADER,
    }

    if _isImageUrl(url):
        logging.info("source: direct image url")

        cover_art_binary = requests.get(url=url, headers=request_headers).content

    else:
        logging.info(f"get request url: {url}")

        http_response: requests.Response = requests.get(
            url=url,
            headers=request_headers,
        )

        logging.info(f"response: {http_response}")

        response_content = http_response.content
        html_soup = BeautifulSoup(
            markup=response_content,
            features="html.parser",
        )

        cover_art_uri: str = ""

        if regex.search("wikipedia", url) is not None:
            logging.info("source: wikipedia")

            cover_art_uri = f"https:{str(html_soup.find_all('img')[3]['src'])}"

        if regex.search("spotify", url) is not None:
            logging.info("source: spotify")

            cover_art_uri = str(html_soup.find_all("img")[0]["src"])

        logging.info(f"get cover image content: {cover_art_uri}")

        if not cover_art_uri:
            logging.info("no cover art found at url")

            return

        cover_art_binary = requests.get(
            url=cover_art_uri,
            headers=request_headers,
        ).content

    if output_filename:
        with open(file=output_filename, mode="wb") as output_file:
            try:
                logging.info(f"saving to {output_filename}")

                _ = output_file.write(cover_art_binary)

            except Exception as error:
                logging.fatal(f"{error}")

                raise error


def _resolveCoverUrl(theme) -> str | None:
    """resolve the best cover art url from a theme's links."""
    if not theme.link:
        return None

    return theme.link.cover or theme.link.spotify or theme.link.wikipedia


def _loadFont(size: int = 12) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """load a monospace font, falling back to PIL default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/dejavu/DejaVuSansMono.ttf",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue

    return ImageFont.load_default()


def buildScreenshot(
    theme,
    cover_path: str,
    output_path: str,
) -> None:
    """
    create a composite image showing the cover art alongside the palette swatches.
    """
    if not _HAS_PIL:
        print("pillow is required for screenshot generation")
        return

    cover = Image.open(cover_path).convert("RGB")
    cover = cover.resize((280, 280), Image.LANCZOS)

    font = _loadFont(11)
    title_font = _loadFont(14)

    canvas_width = 640
    canvas_height = 340
    canvas = Image.new("RGB", (canvas_width, canvas_height), "#1a1a1a")
    draw = ImageDraw.Draw(canvas)

    # header
    title_text = f"{theme.name} — {theme.artist}"
    draw.text((20, 10), title_text, fill="#cccccc", font=title_font)

    # cover art
    canvas.paste(cover, (20, 40))

    # palette swatches — two columns of 8
    base_colors = [
        ("base00", theme.palette.base00),
        ("base01", theme.palette.base01),
        ("base02", theme.palette.base02),
        ("base03", theme.palette.base03),
        ("base04", theme.palette.base04),
        ("base05", theme.palette.base05),
        ("base06", theme.palette.base06),
        ("base07", theme.palette.base07),
        ("base08", theme.palette.base08),
        ("base09", theme.palette.base09),
        ("base0A", theme.palette.base0A),
        ("base0B", theme.palette.base0B),
        ("base0C", theme.palette.base0C),
        ("base0D", theme.palette.base0D),
        ("base0E", theme.palette.base0E),
        ("base0F", theme.palette.base0F),
    ]

    swatch_x = 320
    swatch_y_start = 40
    col_width = 150
    row_height = 28
    gap = 10

    for index, (name, hex_color) in enumerate(base_colors):
        col = index // 8
        row = index % 8
        x = swatch_x + col * (col_width + gap)
        y = swatch_y_start + row * row_height

        swatch_w = col_width - 56
        swatch_h = 20

        # colored rectangle
        draw.rectangle([x, y, x + swatch_w, y + swatch_h], fill=hex_color)

        # border for dark/light contrast
        draw.rectangle(
            [x, y, x + swatch_w, y + swatch_h],
            outline="#333333",
            width=1,
        )

        # hex label
        text_x = x + swatch_w + 6
        text_y = y + 2
        draw.text((text_x, text_y), hex_color, fill="#aaaaaa", font=font)

    canvas.save(output_path, "PNG")


def buildAllScreenshots(
    themes: list,
    cover_dir: str = "assets/covers",
    output_dir: str = "assets/screenshots",
) -> None:
    """generate composite screenshots for all themes."""
    import os

    os.makedirs(cover_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    for theme in themes:
        combined_slug = f"{theme.artist_slug}-{theme.slug}"
        cover_path = os.path.join(cover_dir, f"{combined_slug}.png")

        if not os.path.exists(cover_path):
            cover_url = _resolveCoverUrl(theme)

            if cover_url:
                print(f"  downloading cover for {combined_slug}")
                retrieveCoverArt(
                    url=cover_url,
                    output_filename=cover_path,
                )

        if os.path.exists(cover_path):
            out_path = os.path.join(output_dir, f"{combined_slug}.png")
            buildScreenshot(theme, cover_path, out_path)
        else:
            print(f"  no cover available for {combined_slug}")
