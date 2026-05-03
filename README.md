# Image to DXF

[![Tests](https://github.com/pomaxa/image2dxf/actions/workflows/tests.yml/badge.svg)](https://github.com/pomaxa/image2dxf/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/github/license/pomaxa/image2dxf)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.1.0-2f6f4e)](pyproject.toml)
[![Pillow 10+](https://img.shields.io/badge/Pillow-10%2B-6b46c1)](requirements.txt)
[![Last commit](https://img.shields.io/github/last-commit/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf/commits/main)
[![Repo size](https://img.shields.io/github/repo-size/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf)
[![Issues](https://img.shields.io/github/issues/pomaxa/image2dxf)](https://github.com/pomaxa/image2dxf/issues)
[![Stars](https://img.shields.io/github/stars/pomaxa/image2dxf?style=social)](https://github.com/pomaxa/image2dxf/stargazers)

Small CLI tool for preparing raster artwork for laser cutting. It converts an image to monochrome, traces the black regions, and writes closed DXF polylines in millimeters.

## Setup

```sh
python3 -m pip install -e .
```

If editable install is not needed, run directly from the repository:

```sh
PYTHONPATH=src python3 -m img2dxf input.png output.dxf --width-mm 100
```

## Usage

```sh
img2dxf input.png output.dxf --width-mm 100 --mono-output preview.png
```

For stencil-style artwork where inner letter parts must stay attached, add bridges:

```sh
img2dxf input.png output.dxf --width-mm 100 --bridge-mm 2
```

Run the local preview UI:

```sh
PYTHONPATH=src python3 -m img2dxf.web --host 127.0.0.1 --port 8000
```

Useful options:

```sh
--threshold 128          Use a fixed black/white threshold instead of Otsu auto threshold
--invert                 Cut light regions instead of dark regions
--scale-mm-per-pixel 0.1 Use an explicit scale instead of target width
--bridge-mm 2            Add bridges to inner black islands, such as O/e counters
--bridge-side top        Put bridges on top, bottom, left, right, or nearest side
--simplify 0.8           Reduce DXF nodes; value is in source pixels
--min-area-px 20         Remove tiny black components before tracing
--layer CUT              Set the DXF layer name
```

Black pixels become cut paths. Use `--mono-output` to inspect the exact raster mask before sending the DXF to laser software.

## Tests

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests
```
