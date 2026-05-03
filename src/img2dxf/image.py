from __future__ import annotations

from collections import deque
from os import PathLike
from pathlib import Path
from typing import BinaryIO

from PIL import Image


def load_monochrome(
    image_path: str | PathLike[str] | BinaryIO,
    *,
    threshold: int | None = None,
    invert: bool = False,
    min_area_px: int = 0,
) -> tuple[list[list[bool]], Image.Image, int]:
    """Load an image and return a black-pixel mask plus a preview image."""
    source = Image.open(image_path).convert("L")
    histogram = source.histogram()
    cutoff = otsu_threshold(histogram) if threshold is None else threshold
    if not 0 <= cutoff <= 255:
        raise ValueError("threshold must be between 0 and 255")

    width, height = source.size
    pixels = source.load()
    mask: list[list[bool]] = []
    for y in range(height):
        row: list[bool] = []
        for x in range(width):
            dark = pixels[x, y] <= cutoff
            row.append(not dark if invert else dark)
        mask.append(row)

    if min_area_px > 1:
        mask = remove_small_components(mask, min_area_px)

    return mask, mask_to_preview(mask), cutoff


def mask_to_preview(mask: list[list[bool]]) -> Image.Image:
    height = len(mask)
    width = len(mask[0]) if height else 0
    preview = Image.new("1", (width, height), 1)
    preview_pixels = preview.load()
    for y, row in enumerate(mask):
        for x, is_black in enumerate(row):
            preview_pixels[x, y] = 0 if is_black else 1
    return preview


def save_preview(preview: Image.Image, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    preview.save(path)


def otsu_threshold(histogram: list[int]) -> int:
    total = sum(histogram)
    if total == 0:
        return 127

    weighted_total = sum(level * count for level, count in enumerate(histogram))
    background_weight = 0
    background_sum = 0
    best_level = 127
    best_variance = -1.0

    for level, count in enumerate(histogram):
        background_weight += count
        if background_weight == 0:
            continue

        foreground_weight = total - background_weight
        if foreground_weight == 0:
            break

        background_sum += level * count
        foreground_sum = weighted_total - background_sum
        background_mean = background_sum / background_weight
        foreground_mean = foreground_sum / foreground_weight
        variance = background_weight * foreground_weight * (
            background_mean - foreground_mean
        ) ** 2

        if variance > best_variance:
            best_variance = variance
            best_level = level

    return best_level


def remove_small_components(mask: list[list[bool]], min_area: int) -> list[list[bool]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    seen = [[False for _ in range(width)] for _ in range(height)]
    cleaned = [row[:] for row in mask]

    for y in range(height):
        for x in range(width):
            if seen[y][x] or not mask[y][x]:
                continue

            component = _collect_component(mask, seen, x, y)
            if len(component) < min_area:
                for cx, cy in component:
                    cleaned[cy][cx] = False

    return cleaned


def _collect_component(
    mask: list[list[bool]],
    seen: list[list[bool]],
    start_x: int,
    start_y: int,
) -> list[tuple[int, int]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
    seen[start_y][start_x] = True
    component: list[tuple[int, int]] = []

    while queue:
        x, y = queue.popleft()
        component.append((x, y))
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (
                0 <= nx < width
                and 0 <= ny < height
                and not seen[ny][nx]
                and mask[ny][nx]
            ):
                seen[ny][nx] = True
                queue.append((nx, ny))

    return component
