from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class Component:
    label: int
    pixels: list[tuple[int, int]]
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    touches_edge: bool

    @property
    def area(self) -> int:
        return len(self.pixels)


def bridge_width_to_px(bridge_mm: float, scale_mm_per_pixel: float) -> int:
    if bridge_mm <= 0:
        return 0
    if scale_mm_per_pixel <= 0:
        raise ValueError("scale_mm_per_pixel must be greater than 0.")
    return max(1, ceil(bridge_mm / scale_mm_per_pixel))


def add_island_bridges(
    mask: list[list[bool]],
    *,
    bridge_width_px: int,
    bridge_side: str = "top",
) -> tuple[list[list[bool]], int]:
    """Connect inner black islands to the largest black component."""
    if bridge_width_px <= 0:
        return [row[:] for row in mask], 0
    if bridge_side not in {"top", "bottom", "left", "right", "nearest"}:
        raise ValueError("bridge_side must be top, bottom, left, right, or nearest")

    labels, components = label_black_components(mask)
    if len(components) <= 1:
        return [row[:] for row in mask], 0

    main = max(components, key=lambda component: component.area)
    result = [row[:] for row in mask]
    bridges_created = 0

    candidates = [
        component
        for component in components
        if component.label != main.label
        and not component.touches_edge
        and _inside(component, main)
    ]
    candidates.sort(key=lambda component: component.area, reverse=True)

    for component in candidates:
        path = _shortest_path_to_label(
            labels,
            component,
            main.label,
            bridge_side=bridge_side,
        )
        if not path:
            continue
        _paint_bridge(result, path, bridge_width_px)
        bridges_created += 1

    return result, bridges_created


def label_black_components(
    mask: list[list[bool]],
) -> tuple[list[list[int]], list[Component]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    labels = [[0 for _ in range(width)] for _ in range(height)]
    components: list[Component] = []
    next_label = 1

    for y in range(height):
        for x in range(width):
            if not mask[y][x] or labels[y][x]:
                continue
            component = _collect_component(mask, labels, x, y, next_label)
            components.append(component)
            next_label += 1

    return labels, components


def _collect_component(
    mask: list[list[bool]],
    labels: list[list[int]],
    start_x: int,
    start_y: int,
    label: int,
) -> Component:
    height = len(mask)
    width = len(mask[0]) if height else 0
    queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
    labels[start_y][start_x] = label
    pixels: list[tuple[int, int]] = []
    min_x = max_x = start_x
    min_y = max_y = start_y
    touches_edge = False

    while queue:
        x, y = queue.popleft()
        pixels.append((x, y))
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)
        touches_edge = touches_edge or x in {0, width - 1} or y in {0, height - 1}

        for nx, ny in _neighbors(x, y):
            if (
                0 <= nx < width
                and 0 <= ny < height
                and mask[ny][nx]
                and not labels[ny][nx]
            ):
                labels[ny][nx] = label
                queue.append((nx, ny))

    return Component(
        label=label,
        pixels=pixels,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
        touches_edge=touches_edge,
    )


def _shortest_path_to_label(
    labels: list[list[int]],
    component: Component,
    target_label: int,
    *,
    bridge_side: str,
) -> list[tuple[int, int]]:
    height = len(labels)
    width = len(labels[0]) if height else 0
    queue: deque[tuple[int, int]] = deque()
    seen = [[False for _ in range(width)] for _ in range(height)]
    parent: dict[tuple[int, int], tuple[int, int] | None] = {}

    seed_cells = _preferred_seed_cells(labels, component, bridge_side)
    if not seed_cells:
        seed_cells = _preferred_seed_cells(labels, component, "nearest")

    for nx, ny in seed_cells:
        if labels[ny][nx] == target_label:
            return []
        if labels[ny][nx] == 0 and not seen[ny][nx]:
            seen[ny][nx] = True
            parent[(nx, ny)] = None
            queue.append((nx, ny))

    while queue:
        x, y = queue.popleft()
        for nx, ny in _neighbors(x, y):
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if labels[ny][nx] == target_label:
                return _reconstruct_path(parent, (x, y))
            if labels[ny][nx] == 0 and not seen[ny][nx]:
                seen[ny][nx] = True
                parent[(nx, ny)] = (x, y)
                queue.append((nx, ny))

    return []


def _preferred_seed_cells(
    labels: list[list[int]],
    component: Component,
    bridge_side: str,
) -> list[tuple[int, int]]:
    height = len(labels)
    width = len(labels[0]) if height else 0
    seeds: list[tuple[int, int]] = []

    for x, y in _preferred_component_pixels(component, bridge_side):
        for nx, ny in _ordered_seed_neighbors(x, y, bridge_side):
            if 0 <= nx < width and 0 <= ny < height and labels[ny][nx] == 0:
                seeds.append((nx, ny))

    return _unique(seeds)


def _preferred_component_pixels(
    component: Component,
    bridge_side: str,
) -> list[tuple[int, int]]:
    if bridge_side == "top":
        pixels = [point for point in component.pixels if point[1] == component.min_y]
        return sorted(pixels, key=lambda point: (abs(point[0] - _mid_x(component)), point[0]))
    if bridge_side == "bottom":
        pixels = [point for point in component.pixels if point[1] == component.max_y]
        return sorted(pixels, key=lambda point: (abs(point[0] - _mid_x(component)), point[0]))
    if bridge_side == "left":
        pixels = [point for point in component.pixels if point[0] == component.min_x]
        return sorted(pixels, key=lambda point: (abs(point[1] - _mid_y(component)), point[1]))
    if bridge_side == "right":
        pixels = [point for point in component.pixels if point[0] == component.max_x]
        return sorted(pixels, key=lambda point: (abs(point[1] - _mid_y(component)), point[1]))
    return component.pixels


def _ordered_seed_neighbors(
    x: int,
    y: int,
    bridge_side: str,
) -> tuple[tuple[int, int], ...]:
    if bridge_side == "top":
        return ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1))
    if bridge_side == "bottom":
        return ((x, y + 1), (x - 1, y), (x + 1, y), (x, y - 1))
    if bridge_side == "left":
        return ((x - 1, y), (x, y - 1), (x, y + 1), (x + 1, y))
    if bridge_side == "right":
        return ((x + 1, y), (x, y - 1), (x, y + 1), (x - 1, y))
    return _neighbors(x, y)


def _unique(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, int]] = []
    for point in points:
        if point not in seen:
            seen.add(point)
            result.append(point)
    return result


def _mid_x(component: Component) -> float:
    return (component.min_x + component.max_x) / 2


def _mid_y(component: Component) -> float:
    return (component.min_y + component.max_y) / 2


def _reconstruct_path(
    parent: dict[tuple[int, int], tuple[int, int] | None],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    path = [end]
    current = end
    while parent[current] is not None:
        current = parent[current]
        path.append(current)
    path.reverse()
    return path


def _paint_bridge(
    mask: list[list[bool]],
    path: list[tuple[int, int]],
    width_px: int,
) -> None:
    height = len(mask)
    width = len(mask[0]) if height else 0
    before = (width_px - 1) // 2
    after = width_px // 2

    for x, y in path:
        for yy in range(y - before, y + after + 1):
            for xx in range(x - before, x + after + 1):
                if 0 <= xx < width and 0 <= yy < height:
                    mask[yy][xx] = True


def _inside(component: Component, main: Component) -> bool:
    return (
        main.min_x <= component.min_x
        and component.max_x <= main.max_x
        and main.min_y <= component.min_y
        and component.max_y <= main.max_y
    )


def _neighbors(x: int, y: int) -> tuple[tuple[int, int], ...]:
    return ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
