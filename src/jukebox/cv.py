"""
jukebox picker

a gui to derive 16 base scheme from cover art uv,
click and select uv coordinates to create scheme

SPACE - randomly pick 16 colors from cover art uv
ENTER | RETURN - confirm
Q | ESCAPE - quit
"""

# TODO:

import os
from typing import final
import pygame
import sys
from pathlib import Path
import pygame_gui
import logging

from pygame.typing import ColorLike, Point, RectLike

DISPLAY_WIDTH, DISPLAY_HEIGHT = 1024, 1024

DISPLAY_FLAGS = 0

TEST_COVER_ART_IMAGE = str(
    Path(__file__).parent.parent.parent
    / "assets"
    / "covers"
    / "bathory-hammerheart.png"
)


@final
class ColorSelector:
    def __init__(
        self,
        selector_position: Point = (0, 0),
        selector_size: int = 10,
        selector_color: str | ColorLike = "#FFFFFF",
        selector_size_multiplier: int = 5,
        selector_width: int = 2,
        selector_text: str = "",
        selector_text_color: str | ColorLike = "#FFFFFF",
        selector_text_position: RectLike = (0, 0),
    ) -> None:
        self.selector_position = selector_position
        self.selector_size = selector_size
        self.selector_color = selector_color
        self.selector_size_multiplier = selector_size_multiplier
        self.selector_width = selector_width

        self.selector_text = selector_text
        self.selector_text_color = selector_text_color
        self.selector_text_position = selector_text_position

    def drawSelector(
        self,
        screen: pygame.Surface,
        font: pygame.Font,
        cursor_position: Point,
        color_at_cursor: pygame.Color,
    ) -> None:
        # TODO: adjust radius of circle using bind
        # TODO: gaussian blend colors inside circle radius
        logging.debug(f"mouse position: {cursor_position}")
        logging.debug(f"color at mouse cursor: {color_at_cursor}")

        self.selector_position = cursor_position

        hex_at_cursor: str = (
            f"#{color_at_cursor[0]:02x}{color_at_cursor[1]:02x}{color_at_cursor[2]:02x}"
        )
        rgb_at_cursor: str = (
            f"{color_at_cursor[0]}, {color_at_cursor[1]}, {color_at_cursor[2]}"
        )

        self.selector_text = "\n".join([hex_at_cursor, rgb_at_cursor])

        _ = pygame.draw.aacircle(
            surface=screen,
            color=self.selector_color,
            center=self.selector_position,
            radius=self.selector_size,
            width=self.selector_width,
        )

        selector_text_surface = font.render(
            text=self.selector_text,
            antialias=True,
            color=self.selector_text_color,
        )

        self.selector_text_position = (
            cursor_position[0] + selector_text_surface.width * 0.4,
            cursor_position[1] - selector_text_surface.height * 0.4,
        )

        _ = screen.blit(
            source=selector_text_surface,
            dest=self.selector_text_position,
        )


def runJukeboxPicker(
    cover_art_image_path: str = TEST_COVER_ART_IMAGE,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    is_fullscreen: bool = False,
) -> None:

    if not os.path.exists(path=cover_art_image_path):
        logging.critical(f"cover art image does not exist: {cover_art_image_path}")

        raise FileNotFoundError

    display_flags = DISPLAY_FLAGS

    if is_fullscreen:
        display_flags = DISPLAY_FLAGS | pygame.FULLSCREEN

    _ = pygame.init()
    screen = pygame.display.set_mode(
        size=(display_width, display_height),
        flags=display_flags,
    )
    clock = pygame.time.Clock()
    pygame.display.set_caption("jukebox picker")
    font = pygame.font.Font(  # TODO: use branding font
        filename=None,
        size=24,
    )
    is_running: bool = True
    manager = pygame_gui.UIManager((800, 600))

    color_selector = ColorSelector()

    cover_art_image_surface = pygame.image.load(file=cover_art_image_path)
    cover_art_image_surface = pygame.transform.scale(
        surface=cover_art_image_surface,
        size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
    )

    while is_running:
        delta_time = clock.tick(60) / 1000

        # TODO: draw help on screen

        _ = screen.blit(
            source=cover_art_image_surface,
            dest=(0, 0),
        )

        mouse_position = pygame.mouse.get_pos()

        color_at_mouse_cursor_position = cover_art_image_surface.get_at(mouse_position)

        color_selector.drawSelector(
            screen=screen,
            font=font,
            cursor_position=mouse_position,
            color_at_cursor=color_at_mouse_cursor_position,
        )

        for event in pygame.event.get():
            _ = manager.process_events(event)

            if event.type == pygame.QUIT:
                is_running = False

            keys = pygame.key.get_pressed()

            if keys[pygame.K_k]:
                # TODO: increase color selector size
                pass

            if keys[pygame.KMOD_SHIFT] and keys[pygame.K_k]:
                # TODO: increase color selector size
                pass

            if keys[pygame.K_j]:
                # TODO: decrease color selector size
                pass

            if keys[pygame.KMOD_SHIFT] and keys[pygame.K_j]:
                # TODO: decrease color selector size
                pass

            if keys[pygame.K_SPACE]:
                # TODO: random 16 color selection in uv space
                pass

            if keys[pygame.K_RETURN]:
                # TODO: color selection confirmation
                pass

            if keys[pygame.K_q] or keys[pygame.K_ESCAPE]:
                is_running = False

        manager.update(delta_time)
        manager.draw_ui(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    runJukeboxPicker()
