from __future__ import annotations

from collections import defaultdict
from math import hypot

GridPoint = tuple[int, int]
Edge = tuple[GridPoint, GridPoint]
Polyline = list[GridPoint]


def trace_mask(mask: list[list[bool]], *, simplify: float = 0.75) -> list[Polyline]:
    """Trace black-pixel boundaries into closed pixel-grid polylines."""
    edges = _boundary_edges(mask)
    outgoing: dict[GridPoint, list[GridPoint]] = defaultdict(list)
    for start, end in edges:
        outgoing[start].append(end)

    unused = set(edges)
    paths: list[Polyline] = []

    while unused:
        start, end = next(iter(unused))
        path: Polyline = [start]
        previous = start
        current = end
        closed = False

        while True:
            edge = (previous, current)
            if edge not in unused:
                break
            unused.remove(edge)
            path.append(current)

            if current == start:
                path.pop()
                closed = True
                break

            candidates = [
                point for point in outgoing[current] if (current, point) in unused
            ]
            if not candidates:
                break

            next_point = _choose_next(previous, current, candidates)
            previous, current = current, next_point

        if closed and len(path) >= 3:
            simplified = simplify_closed_path(path, simplify)
            if len(simplified) >= 3:
                paths.append(simplified)

    return paths


def to_mm_polylines(
    paths: list[Polyline],
    *,
    image_height_px: int,
    scale_mm_per_pixel: float,
) -> list[list[tuple[float, float]]]:
    return [
        [
            (x * scale_mm_per_pixel, (image_height_px - y) * scale_mm_per_pixel)
            for x, y in path
        ]
        for path in paths
    ]


def simplify_closed_path(path: Polyline, tolerance: float) -> Polyline:
    path = _remove_collinear(path)
    if tolerance <= 0 or len(path) <= 3:
        return path

    a = _farthest_index(path, 0)
    b = _farthest_index(path, a)
    if a == b:
        return path

    chain_one = _cycle_slice(path, a, b)
    chain_two = _cycle_slice(path, b, a)
    simplified = _rdp(chain_one, tolerance)[:-1] + _rdp(chain_two, tolerance)[:-1]
    return _remove_duplicate_neighbors(_remove_collinear(simplified))


def _boundary_edges(mask: list[list[bool]]) -> set[Edge]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    edges: set[Edge] = set()

    def black(x: int, y: int) -> bool:
        return 0 <= x < width and 0 <= y < height and mask[y][x]

    for y, row in enumerate(mask):
        for x, is_black in enumerate(row):
            if not is_black:
                continue
            if not black(x, y - 1):
                edges.add(((x, y), (x + 1, y)))
            if not black(x + 1, y):
                edges.add(((x + 1, y), (x + 1, y + 1)))
            if not black(x, y + 1):
                edges.add(((x + 1, y + 1), (x, y + 1)))
            if not black(x - 1, y):
                edges.add(((x, y + 1), (x, y)))

    return edges


def _choose_next(
    previous: GridPoint, current: GridPoint, candidates: list[GridPoint]
) -> GridPoint:
    incoming = _direction_index(current[0] - previous[0], current[1] - previous[1])

    def score(point: GridPoint) -> tuple[int, int, int]:
        outgoing = _direction_index(point[0] - current[0], point[1] - current[1])
        turn = (outgoing - incoming) % 4
        priority = {1: 0, 0: 1, 3: 2, 2: 3}[turn]
        return priority, point[1], point[0]

    return min(candidates, key=score)


def _direction_index(dx: int, dy: int) -> int:
    if dx > 0:
        return 0
    if dy > 0:
        return 1
    if dx < 0:
        return 2
    return 3


def _remove_collinear(path: Polyline) -> Polyline:
    if len(path) <= 3:
        return path
    result: Polyline = []
    for index, point in enumerate(path):
        previous = path[index - 1]
        following = path[(index + 1) % len(path)]
        if not _is_collinear(previous, point, following):
            result.append(point)
    return result


def _is_collinear(a: GridPoint, b: GridPoint, c: GridPoint) -> bool:
    return (b[0] - a[0]) * (c[1] - b[1]) == (b[1] - a[1]) * (c[0] - b[0])


def _remove_duplicate_neighbors(path: Polyline) -> Polyline:
    result: Polyline = []
    for point in path:
        if not result or result[-1] != point:
            result.append(point)
    if len(result) > 1 and result[0] == result[-1]:
        result.pop()
    return result


def _farthest_index(path: Polyline, from_index: int) -> int:
    origin = path[from_index]
    return max(
        range(len(path)),
        key=lambda index: _distance(origin, path[index]),
    )


def _cycle_slice(path: Polyline, start: int, end: int) -> Polyline:
    if start <= end:
        return path[start : end + 1]
    return path[start:] + path[: end + 1]


def _rdp(points: Polyline, tolerance: float) -> Polyline:
    if len(points) < 3:
        return points

    start = points[0]
    end = points[-1]
    max_distance = -1.0
    max_index = 0

    for index in range(1, len(points) - 1):
        distance = _line_distance(points[index], start, end)
        if distance > max_distance:
            max_distance = distance
            max_index = index

    if max_distance > tolerance:
        left = _rdp(points[: max_index + 1], tolerance)
        right = _rdp(points[max_index:], tolerance)
        return left[:-1] + right

    return [start, end]


def _line_distance(point: GridPoint, start: GridPoint, end: GridPoint) -> float:
    if start == end:
        return _distance(point, start)
    numerator = abs(
        (end[1] - start[1]) * point[0]
        - (end[0] - start[0]) * point[1]
        + end[0] * start[1]
        - end[1] * start[0]
    )
    denominator = hypot(end[1] - start[1], end[0] - start[0])
    return numerator / denominator


def _distance(a: GridPoint, b: GridPoint) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])
