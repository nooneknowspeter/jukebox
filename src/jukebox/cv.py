"""
jukebox picker

a gui to derive 16 base scheme from cover art uv,
click and select uv coordinates to create scheme

SPACE - randomly pick 16 colors from cover art uv
ENTER | RETURN - confirm and return palette
DRAG - move selector
J/K | SCROLL - resize selector
Q | ESCAPE - quit
"""

import os
import random
from typing import final
import pygame
from pathlib import Path
import pygame_gui
import logging
import numpy as np
import cv2 as cv

from pygame.typing import ColorLike, Point, RectLike

from src.jukebox.models import PALETTE_BASE_KEYS

DISPLAY_WIDTH, DISPLAY_HEIGHT = 1024, 1024

DISPLAY_FLAGS = 0

TEST_COVER_ART_IMAGE = str(
    Path(__file__).parent.parent.parent
    / "assets"
    / "covers"
    / "bathory-hammerheart.png"
)


def _rgbToHex(red: int, green: int, blue: int) -> str:
    return f"#{red:02x}{green:02x}{blue:02x}".upper()


def _perceivedLuminance(red: int, green: int, blue: int) -> float:
    return 0.299 * red + 0.587 * green + 0.114 * blue


def _computeMeanColorInCircle(
    cover_art_image_rgb_matrix: np.ndarray,
    center_x: int,
    center_y: int,
    circle_radius: int,
) -> tuple[int, int, int]:
    image_height, image_width = cover_art_image_rgb_matrix.shape[:2]

    bounding_left = max(center_x - circle_radius, 0)
    bounding_top = max(center_y - circle_radius, 0)
    bounding_right = min(center_x + circle_radius, image_width)
    bounding_bottom = min(center_y + circle_radius, image_height)

    if bounding_right <= bounding_left or bounding_bottom <= bounding_top:
        return (0, 0, 0)

    cropped_region_rgb = cover_art_image_rgb_matrix[
        bounding_top:bounding_bottom,
        bounding_left:bounding_right,
    ].copy()

    mask_height = bounding_bottom - bounding_top
    mask_width = bounding_right - bounding_left
    circular_mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
    local_center_x = center_x - bounding_left
    local_center_y = center_y - bounding_top

    cv.circle(
        img=circular_mask,
        center=(local_center_x, local_center_y),
        radius=circle_radius,
        color=255,
        thickness=-1,
    )

    mean_channel_values = cv.mean(cropped_region_rgb, mask=circular_mask)
    mean_red = int(mean_channel_values[0])
    mean_green = int(mean_channel_values[1])
    mean_blue = int(mean_channel_values[2])

    return (mean_red, mean_green, mean_blue)


def _buildPaletteDict(color_hex_list: list[str]) -> dict[str, str]:
    palette_entries: dict[str, str] = {}

    for palette_index, palette_key in enumerate(PALETTE_BASE_KEYS):
        palette_entries[palette_key] = color_hex_list[palette_index]

    return palette_entries


def generateRandomPalette(
    cover_art_image_path: str,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    selector_radius: int = 10,
) -> list[str]:
    """generate 16 random colors from cover art using circular mean."""
    if not os.path.exists(path=cover_art_image_path):
        logging.critical(f"cover art image does not exist: {cover_art_image_path}")
        raise FileNotFoundError

    cover_art_image_surface = pygame.image.load(file=cover_art_image_path)
    cover_art_image_surface = pygame.transform.scale(
        surface=cover_art_image_surface,
        size=(display_width, display_height),
    )
    cover_art_image_rgb_matrix = pygame.surfarray.array3d(
        surface=cover_art_image_surface,
    )

    colors_with_luminance: list[tuple[str, float]] = []
    random.seed()

    for selector_index in range(16):
        random_x = random.randint(0, display_width - 1)
        random_y = random.randint(0, display_height - 1)

        mean_red, mean_green, mean_blue = _computeMeanColorInCircle(
            cover_art_image_rgb_matrix=cover_art_image_rgb_matrix,
            center_x=random_x,
            center_y=random_y,
            circle_radius=selector_radius,
        )

        hex_color = _rgbToHex(mean_red, mean_green, mean_blue)
        luminance = _perceivedLuminance(mean_red, mean_green, mean_blue)
        colors_with_luminance.append((hex_color, luminance))

    colors_with_luminance.sort(key=lambda color_entry: color_entry[1])

    return [hex_color for hex_color, _ in colors_with_luminance]


@final
class ColorSelector:
    def __init__(
        self,
        selector_position: Point = (0, 0),
        selector_radius: int = 10,
        selector_max_radius: int = 50,
        selector_min_radius: int = 1,
        selector_color: str | ColorLike = "#FFFFFF",
        selector_radius_step: int = 5,
        selector_stroke_width: int = 2,
        selector_label_text: str = "",
        selector_label_color: str | ColorLike = "#FFFFFF",
        selector_label_background: str | ColorLike = "#000000",
        selector_label_position: RectLike = (0, 0),
        selector_index: int = 0,
    ) -> None:
        self.selector_position = selector_position
        self.selector_radius = selector_radius
        self.selector_color = selector_color
        self.selector_radius_step = selector_radius_step
        self.selector_stroke_width = selector_stroke_width

        self.selector_label_text = selector_label_text
        self.selector_label_background = selector_label_background
        self.selector_label_color = selector_label_color
        self.selector_label_position = selector_label_position
        self.selector_max_radius = selector_max_radius
        self.selector_min_radius = selector_min_radius

        self.mean_color_rgb: tuple[int, int, int] = (0, 0, 0)
        self.mean_color_hex: str = "#000000"
        self.is_dragging: bool = False
        self.selector_index: int = selector_index

    def isPointInsideCircle(self, test_point: Point) -> bool:
        delta_x = test_point[0] - self.selector_position[0]
        delta_y = test_point[1] - self.selector_position[1]
        distance_squared = delta_x * delta_x + delta_y * delta_y
        radius_squared = self.selector_radius * self.selector_radius
        return distance_squared <= radius_squared

    def increaseSelectorRadius(
        self,
        use_radius_step: bool = False,
    ) -> None:
        if self.selector_radius >= self.selector_max_radius:
            return

        if use_radius_step:
            self.selector_radius += self.selector_radius_step
        else:
            self.selector_radius += 1

    def decreaseSelectorRadius(
        self,
        use_radius_step: bool = False,
    ) -> None:
        if self.selector_radius <= self.selector_min_radius:
            return

        if use_radius_step:
            self.selector_radius -= self.selector_radius_step
        else:
            self.selector_radius -= 1

    def computeMeanColorInRadius(
        self,
        cover_art_image_rgb_matrix: np.ndarray,
    ) -> tuple[int, int, int]:
        center_x = int(self.selector_position[0])
        center_y = int(self.selector_position[1])

        mean_rgb = _computeMeanColorInCircle(
            cover_art_image_rgb_matrix=cover_art_image_rgb_matrix,
            center_x=center_x,
            center_y=center_y,
            circle_radius=self.selector_radius,
        )

        self.mean_color_rgb = mean_rgb
        self.mean_color_hex = _rgbToHex(*mean_rgb)

        return mean_rgb

    def drawSelector(
        self,
        screen_surface: pygame.Surface,
        label_font: pygame.Font,
        cover_art_image_rgb_matrix: np.ndarray,
    ) -> None:
        mean_rgb = self.computeMeanColorInRadius(cover_art_image_rgb_matrix)

        self.selector_color = self.mean_color_hex
        self.selector_label_background = self.mean_color_hex

        _ = pygame.draw.aacircle(
            surface=screen_surface,
            color=self.selector_color,
            center=self.selector_position,
            radius=self.selector_radius,
            width=self.selector_stroke_width,
        )

        if self.selector_index == -1:
            index_label = f"CURSOR {self.mean_color_hex}"
        else:
            index_label = f"[{self.selector_index}] {self.mean_color_hex}"
        rgb_label = f"{mean_rgb[0]}, {mean_rgb[1]}, {mean_rgb[2]}"
        self.selector_label_text = "\n".join([index_label, rgb_label])

        label_surface = label_font.render(
            text=self.selector_label_text,
            antialias=True,
            color=self.selector_label_color,
            bgcolor=self.selector_label_background,
        )

        label_offset_x = self.selector_position[0] + self.selector_radius + 4
        label_offset_y = self.selector_position[1] + self.selector_radius + 4

        label_x_position = (
            label_offset_x - label_surface.width
            if (label_offset_x + label_surface.width) > screen_surface.width
            else label_offset_x
        )

        label_y_position = (
            label_offset_y - label_surface.height
            if (label_offset_y + label_surface.height) > screen_surface.height
            else label_offset_y
        )

        self.selector_label_position = (label_x_position, label_y_position)

        _ = screen_surface.blit(
            source=label_surface,
            dest=self.selector_label_position,
        )


def _drawHelpOverlay(
    screen_surface: pygame.Surface,
    help_font: pygame.Font,
) -> None:
    help_lines = [
        "SPACE  - randomly pick 16 colors",
        "ENTER  - confirm palette",
        "CLICK  - add selector (< 16)",
        "J/K    - resize selector",
        "SCROLL - resize selector",
        "DRAG   - move selector",
        "Q/ESC  - quit",
    ]

    line_height = help_font.get_linesize()
    padding = 8
    overlay_width = 280
    overlay_height = len(help_lines) * line_height + padding * 2

    help_background_surface = pygame.Surface(
        (overlay_width, overlay_height),
        pygame.SRCALPHA,
    )
    help_background_surface.fill((0, 0, 0, 180))

    for line_index, help_line in enumerate(help_lines):
        help_text_surface = help_font.render(
            text=help_line,
            antialias=True,
            color="#FFFFFF",
        )
        help_background_surface.blit(
            source=help_text_surface,
            dest=(padding, padding + line_index * line_height),
        )

    _ = screen_surface.blit(
        source=help_background_surface,
        dest=(8, 8),
    )


def _findNearestSelectorToPosition(
    color_selectors: list[ColorSelector],
    target_position: Point,
    cursor_selector: ColorSelector | None = None,
) -> ColorSelector | None:
    nearest_selector: ColorSelector | None = None
    smallest_distance_squared = float("inf")

    candidates = list(color_selectors)

    if cursor_selector is not None:
        candidates.append(cursor_selector)

    for selector in candidates:
        delta_x = target_position[0] - selector.selector_position[0]
        delta_y = target_position[1] - selector.selector_position[1]
        distance_squared = delta_x * delta_x + delta_y * delta_y

        if distance_squared < smallest_distance_squared:
            smallest_distance_squared = distance_squared
            nearest_selector = selector

    return nearest_selector


def runJukeboxPicker(
    cover_art_image_path: str = TEST_COVER_ART_IMAGE,
    display_width: int = DISPLAY_WIDTH,
    display_height: int = DISPLAY_HEIGHT,
    is_fullscreen: bool = False,
) -> list[str]:

    if not os.path.exists(path=cover_art_image_path):
        logging.critical(f"cover art image does not exist: {cover_art_image_path}")
        raise FileNotFoundError

    display_flags = DISPLAY_FLAGS

    if is_fullscreen:
        display_flags = DISPLAY_FLAGS | pygame.FULLSCREEN

    _ = pygame.init()
    screen_surface = pygame.display.set_mode(
        size=(display_width, display_height),
        flags=display_flags,
    )
    frame_clock = pygame.time.Clock()
    pygame.display.set_caption("jukebox picker")
    label_font = pygame.font.Font(
        filename=None,
        size=18,
    )
    is_running: bool = True
    ui_manager = pygame_gui.UIManager((800, 600))

    color_selectors: list[ColorSelector] = []
    active_dragging_selector: ColorSelector | None = None
    cursor_selector = ColorSelector(selector_index=-1)

    cover_art_image_surface = pygame.image.load(file=cover_art_image_path)
    cover_art_image_surface = pygame.transform.scale(
        surface=cover_art_image_surface,
        size=(DISPLAY_WIDTH, DISPLAY_HEIGHT),
    )
    cover_art_image_rgb_matrix = pygame.surfarray.array3d(
        surface=cover_art_image_surface,
    )

    while is_running:
        delta_time = frame_clock.tick(60) / 1000

        _ = screen_surface.blit(
            source=cover_art_image_surface,
            dest=(0, 0),
        )

        for selector in color_selectors:
            selector.drawSelector(
                screen_surface=screen_surface,
                label_font=label_font,
                cover_art_image_rgb_matrix=cover_art_image_rgb_matrix,
            )

        mouse_position = pygame.mouse.get_pos()
        cursor_selector.selector_position = mouse_position
        cursor_selector.drawSelector(
            screen_surface=screen_surface,
            label_font=label_font,
            cover_art_image_rgb_matrix=cover_art_image_rgb_matrix,
        )

        _drawHelpOverlay(screen_surface, label_font)

        for event in pygame.event.get():
            _ = ui_manager.process_events(event)

            if event.type == pygame.QUIT:
                is_running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hit_selector = False

                for selector in reversed(color_selectors):
                    if selector.isPointInsideCircle(event.pos):
                        selector.is_dragging = True
                        active_dragging_selector = selector
                        hit_selector = True
                        break

                if not hit_selector and len(color_selectors) < 16:
                    new_selector = ColorSelector(
                        selector_position=event.pos,
                        selector_radius=10,
                        selector_index=len(color_selectors),
                    )
                    color_selectors.append(new_selector)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if active_dragging_selector:
                    active_dragging_selector.is_dragging = False
                    active_dragging_selector = None

            if event.type == pygame.MOUSEMOTION and active_dragging_selector:
                active_dragging_selector.selector_position = event.pos

            if event.type == pygame.MOUSEWHEEL:
                mouse_position = pygame.mouse.get_pos()
                nearest_selector = _findNearestSelectorToPosition(
                    color_selectors,
                    mouse_position,
                    cursor_selector=cursor_selector,
                )

                if nearest_selector:
                    if event.y == 1:
                        nearest_selector.increaseSelectorRadius(
                            use_radius_step=False,
                        )

                    if event.y == -1:
                        nearest_selector.decreaseSelectorRadius(
                            use_radius_step=False,
                        )

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    color_selectors.clear()
                    random.seed()

                    for selector_index in range(16):
                        random_x = random.randint(0, display_width - 1)
                        random_y = random.randint(0, display_height - 1)
                        new_selector = ColorSelector(
                            selector_position=(random_x, random_y),
                            selector_radius=cursor_selector.selector_radius,
                            selector_index=selector_index,
                        )
                        color_selectors.append(new_selector)

                if event.key == pygame.K_RETURN:
                    if len(color_selectors) == 16:
                        colors_with_luminance = [
                            (
                                selector.mean_color_hex,
                                _perceivedLuminance(*selector.mean_color_rgb),
                            )
                            for selector in color_selectors
                        ]
                        colors_with_luminance.sort(
                            key=lambda color_entry: color_entry[1],
                        )

                        palette_hex_colors = [
                            hex_color for hex_color, _ in colors_with_luminance
                        ]

                        pygame.quit()
                        return palette_hex_colors

                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    is_running = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_k]:
            mouse_position = pygame.mouse.get_pos()
            nearest_selector = _findNearestSelectorToPosition(
                color_selectors,
                mouse_position,
                cursor_selector=cursor_selector,
            )

            if nearest_selector:
                nearest_selector.increaseSelectorRadius(
                    use_radius_step=False,
                )

        if keys[pygame.K_j]:
            mouse_position = pygame.mouse.get_pos()
            nearest_selector = _findNearestSelectorToPosition(
                color_selectors,
                mouse_position,
                cursor_selector=cursor_selector,
            )

            if nearest_selector:
                nearest_selector.decreaseSelectorRadius(
                    use_radius_step=False,
                )

        ui_manager.update(delta_time)
        ui_manager.draw_ui(screen_surface)
        pygame.display.flip()

    pygame.quit()
    return []


if __name__ == "__main__":
    runJukeboxPicker()
