# Image to DXF

<p align="center">
  <img src="src/img2dxf/web_assets/app-icon.svg" width="96" alt="Image to DXF app icon">
</p>

[![Tests](https://github.com/pomaxa/image2dxf/actions/workflows/tests.yml/badge.svg)](https://github.com/pomaxa/image2dxf/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25_minimum-brightgreen)](.github/workflows/tests.yml)
[![License: MIT](https://img.shields.io/github/license/pomaxa/image2dxf)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.1.0-2f6f4e)](pyproject.toml)
[![Pillow 10+](https://img.shields.io/badge/Pillow-10%2B-6b46c1)](requirements.txt)
[![Last commit](https://img.shields.io/github/last-commit/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf/commits/main)
[![Repo size](https://img.shields.io/github/repo-size/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf)
[![Issues](https://img.shields.io/github/issues/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf/issues)
[![Stars](https://img.shields.io/github/stars/pomaxa/image2dxf?style=social)](https://github.com/pomaxa/image2dxf/stargazers)

Image to DXF prepares raster artwork for laser cutting. It converts PNG/JPG-style images to a monochrome mask, traces cut contours, optionally adds stencil bridges for inner letter islands, and writes closed DXF polylines in millimeters.

## Features

- Local web UI with original, monochrome, and vector previews.
- CLI for repeatable conversions and batch-friendly workflows.
- Otsu auto-threshold or fixed black/white threshold.
- DXF output using closed `LWPOLYLINE` entities on a configurable layer.
- Stencil bridges for counters in letters like `O`, `e`, `P`, and `a`.
- Polygon simplification in millimeters for cleaner laser paths.
- No cloud processing; images are handled locally.

## Quick Start

```sh
git clone git@github.com:pomaxa/image2dxf.git
cd image2dxf
python3 -m pip install -e .
img2dxf-web
```

OpenCV tracing is optional. Install it when you want to compare the faster contour backend:

```sh
python3 -m pip install -e ".[opencv]"
```

Open the local UI:

```text
http://127.0.0.1:8000
```

For direct repository execution without installing scripts:

```sh
PYTHONPATH=src python3 -m img2dxf.web --host 127.0.0.1 --port 8000
```

## CLI Usage

Basic conversion:

```sh
img2dxf input.png output.dxf --width-mm 100 --mono-output preview.png
```

Keep inner letter parts attached for stencil-style cutting:

```sh
img2dxf input.png output.dxf --width-mm 100 --bridge-mm 2 --bridge-side top
```

Reduce excess polygon nodes in physical units:

```sh
img2dxf input.png output.dxf --width-mm 100 --simplify-mm 0.2
```

Use OpenCV contour tracing:

```sh
img2dxf input.png output.dxf --width-mm 100 --backend opencv
```

## Key Options

```text
--width-mm 100           Scale output to a target width in millimeters
--scale-mm-per-pixel 0.1 Use an explicit raster-to-DXF scale
--threshold 128          Use a fixed threshold instead of auto-threshold
--invert                 Trace light regions instead of dark regions
--bridge-mm 2            Add bridges to inner black islands
--bridge-side top        top, bottom, left, right, or nearest
--backend native         native or opencv contour tracing
--simplify-mm 0.2        Simplify contours in millimeters
--simplify 0.8           Simplify contours in source pixels
--min-area-px 20         Remove tiny black components before tracing
--layer CUT              DXF layer name
```

Black pixels become cut paths. Always inspect `--mono-output` or the web preview before sending the DXF to laser software.

## Recommended Laser Workflow

1. Start with a high-contrast image on a clean background.
2. Adjust threshold until the monochrome preview matches the desired cut shape.
3. Set the final physical width with `--width-mm`.
4. Add bridges, usually `--bridge-mm 2`, when letter interiors must not fall out.
5. Increase `--simplify-mm` gradually until the path is clean without losing important detail.
6. Import the DXF into laser software and confirm size, layer, and closed contours.

## Development

Run tests:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests
```

Run coverage locally after installing development dependencies:

```sh
python3 -m pip install -e ".[dev,opencv]"
PYTHONDONTWRITEBYTECODE=1 coverage run -m unittest discover -s tests
coverage report
```

Project layout:

```text
src/img2dxf/              Converter, DXF writer, web server, and tracing code
src/img2dxf/web_assets/   Web UI assets
tests/                    Unit tests
```

## License

MIT. See [LICENSE](LICENSE).
