from __future__ import annotations

import argparse
from pathlib import Path

from .convert import ConversionOptions, convert_image


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = convert_image(
            args.input,
            ConversionOptions(
                threshold=args.threshold,
                invert=args.invert,
                width_mm=args.width_mm,
                scale_mm_per_pixel=args.scale_mm_per_pixel,
                bridge_mm=args.bridge_mm,
                bridge_side=args.bridge_side,
                simplify=args.simplify,
                simplify_mm=args.simplify_mm,
                min_area_px=args.min_area_px,
                layer=args.layer,
                color=args.color,
            ),
        )
    except ValueError as error:
        parser.error(str(error))

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="ascii") as handle:
        handle.write(result.dxf)

    if args.mono_output:
        with open(args.mono_output, "wb") as handle:
            handle.write(result.preview_png)

    print(
        f"threshold={result.threshold} paths={result.path_count} "
        f"bridges={result.bridges_created} "
        f"simplify={result.simplify_tolerance_mm:.3f}mm "
        f"scale={result.scale_mm_per_pixel:.6f}mm/px output={args.output}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an image to a monochrome preview and DXF cut paths."
    )
    parser.add_argument("input", help="Input raster image, for example PNG or JPG.")
    parser.add_argument("output", help="Output DXF file.")
    parser.add_argument(
        "--mono-output",
        help="Optional monochrome preview image path.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        help="Fixed threshold from 0 to 255. Defaults to Otsu auto threshold.",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Trace light regions instead of dark regions.",
    )
    parser.add_argument(
        "--width-mm",
        type=float,
        help="Target DXF width in millimeters.",
    )
    parser.add_argument(
        "--scale-mm-per-pixel",
        type=float,
        help="Explicit millimeters per source pixel.",
    )
    parser.add_argument(
        "--simplify",
        type=float,
        default=0.75,
        help="Polyline simplification tolerance in pixels. Use 0 to preserve steps.",
    )
    parser.add_argument(
        "--simplify-mm",
        type=float,
        help="Polyline simplification tolerance in millimeters. Overrides --simplify.",
    )
    parser.add_argument(
        "--bridge-mm",
        type=float,
        default=0.0,
        help="Add bridges to inner black islands. Use 2 for a 2 mm bridge.",
    )
    parser.add_argument(
        "--bridge-side",
        choices=("top", "bottom", "left", "right", "nearest"),
        default="top",
        help="Preferred side for bridges. Default is top.",
    )
    parser.add_argument(
        "--min-area-px",
        type=int,
        default=0,
        help="Remove black components smaller than this area in pixels.",
    )
    parser.add_argument(
        "--layer",
        default="CUT",
        help="DXF layer name for cut paths.",
    )
    parser.add_argument(
        "--color",
        type=int,
        default=1,
        help="AutoCAD color index for cut paths. Default 1 is red.",
    )
    return parser
