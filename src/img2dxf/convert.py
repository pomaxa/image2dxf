from __future__ import annotations

from dataclasses import dataclass
from html import escape
from io import BytesIO
from os import PathLike
from typing import BinaryIO

from .bridges import add_island_bridges, bridge_width_to_px
from .dxf import dxf_text
from .image import load_monochrome, mask_to_preview
from .vectorize import Polyline, to_mm_polylines, trace_mask


@dataclass(frozen=True)
class ConversionOptions:
    threshold: int | None = None
    invert: bool = False
    width_mm: float | None = None
    scale_mm_per_pixel: float | None = None
    bridge_mm: float = 0.0
    bridge_side: str = "top"
    simplify: float = 0.75
    simplify_mm: float | None = None
    backend: str = "native"
    min_area_px: int = 0
    layer: str = "CUT"
    color: int = 1


@dataclass(frozen=True)
class ConversionResult:
    width_px: int
    height_px: int
    threshold: int
    scale_mm_per_pixel: float
    bridge_width_px: int
    bridges_created: int
    simplify_tolerance_px: float
    simplify_tolerance_mm: float
    backend: str
    paths: list[Polyline]
    dxf: str
    preview_png: bytes
    svg: str

    @property
    def path_count(self) -> int:
        return len(self.paths)

    @property
    def node_count(self) -> int:
        return sum(len(path) for path in self.paths)


def convert_image(
    image_source: str | PathLike[str] | BinaryIO,
    options: ConversionOptions,
) -> ConversionResult:
    mask, _, threshold = load_monochrome(
        image_source,
        threshold=options.threshold,
        invert=options.invert,
        min_area_px=options.min_area_px,
    )
    height = len(mask)
    width = len(mask[0]) if height else 0
    if width == 0 or height == 0:
        raise ValueError("input image is empty")

    scale = resolve_scale(
        image_width_px=width,
        width_mm=options.width_mm,
        scale_mm_per_pixel=options.scale_mm_per_pixel,
    )
    bridge_width_px = bridge_width_to_px(options.bridge_mm, scale)
    if bridge_width_px:
        mask, bridges_created = add_island_bridges(
            mask,
            bridge_width_px=bridge_width_px,
            bridge_side=options.bridge_side,
        )
    else:
        bridges_created = 0

    simplify_tolerance_px = resolve_simplify_tolerance_px(
        scale_mm_per_pixel=scale,
        simplify_px=options.simplify,
        simplify_mm=options.simplify_mm,
    )
    backend = normalize_backend(options.backend)
    paths = trace_paths(mask, simplify=simplify_tolerance_px, backend=backend)
    polylines = to_mm_polylines(
        paths,
        image_height_px=height,
        scale_mm_per_pixel=scale,
    )

    preview_buffer = BytesIO()
    preview = mask_to_preview(mask)
    preview.save(preview_buffer, format="PNG")

    return ConversionResult(
        width_px=width,
        height_px=height,
        threshold=threshold,
        scale_mm_per_pixel=scale,
        bridge_width_px=bridge_width_px,
        bridges_created=bridges_created,
        simplify_tolerance_px=simplify_tolerance_px,
        simplify_tolerance_mm=simplify_tolerance_px * scale,
        backend=backend,
        paths=paths,
        dxf=dxf_text(polylines, layer=options.layer, color=options.color),
        preview_png=preview_buffer.getvalue(),
        svg=svg_preview(paths, width=width, height=height),
    )


def resolve_scale(
    *,
    image_width_px: int,
    width_mm: float | None = None,
    scale_mm_per_pixel: float | None = None,
) -> float:
    if width_mm and scale_mm_per_pixel:
        raise ValueError("Use either width_mm or scale_mm_per_pixel, not both.")
    if width_mm:
        if width_mm <= 0:
            raise ValueError("width_mm must be greater than 0.")
        return width_mm / image_width_px
    if scale_mm_per_pixel:
        if scale_mm_per_pixel <= 0:
            raise ValueError("scale_mm_per_pixel must be greater than 0.")
        return scale_mm_per_pixel
    return 1.0


def resolve_simplify_tolerance_px(
    *,
    scale_mm_per_pixel: float,
    simplify_px: float,
    simplify_mm: float | None = None,
) -> float:
    if scale_mm_per_pixel <= 0:
        raise ValueError("scale_mm_per_pixel must be greater than 0.")
    if simplify_px < 0:
        raise ValueError("simplify must be 0 or greater.")
    if simplify_mm is None:
        return simplify_px
    if simplify_mm < 0:
        raise ValueError("simplify_mm must be 0 or greater.")
    return simplify_mm / scale_mm_per_pixel


def normalize_backend(backend: str) -> str:
    normalized = backend.strip().lower()
    if normalized not in {"native", "opencv"}:
        raise ValueError("backend must be native or opencv")
    return normalized


def trace_paths(
    mask: list[list[bool]],
    *,
    simplify: float,
    backend: str,
) -> list[Polyline]:
    if backend == "native":
        return trace_mask(mask, simplify=simplify)
    if backend == "opencv":
        from .opencv_vectorize import trace_mask_opencv

        return trace_mask_opencv(mask, simplify=simplify)
    raise ValueError("backend must be native or opencv")


def svg_preview(paths: list[Polyline], *, width: int, height: int) -> str:
    stroke_width = max(1.0, min(width, height) / 260)
    path_data = "\n".join(_svg_path(path) for path in paths)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        'role="img" aria-label="Vector preview">'
        '<rect width="100%" height="100%" fill="#ffffff"/>'
        f'<g fill="none" stroke="#d7352a" stroke-width="{stroke_width:.3f}" '
        'stroke-linejoin="round" stroke-linecap="round">'
        f"{path_data}"
        "</g>"
        "</svg>"
    )


def _svg_path(path: Polyline) -> str:
    commands = " ".join(f"{x},{y}" for x, y in path)
    return f'<polygon points="{escape(commands)}"/>'
