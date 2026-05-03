# Repository Guidelines

## Project Structure & Module Organization

Application source code lives under `src/img2dxf/`, tests live under `tests/`, and reusable assets such as drawings, calibration files, examples, or documentation images should go under `assets/` when introduced. Keep generated DXF, preview PNG, and build output out of source directories; use `dist/`, `build/`, or another clearly named ignored directory.

Recommended layout:

```text
src/img2dxf/  Application and library code
tests/        Automated tests mirroring src/ structure
assets/       Static project assets and sample files
docs/         Design notes and operator-facing documentation
```

## Build, Test, and Development Commands

Use Python 3.10+ and install the package in editable mode before local development:

```sh
python3 -m pip install -e .  # Install the img2dxf CLI locally
img2dxf input.png output.dxf --width-mm 100 --mono-output preview.png
img2dxf input.png output.dxf --width-mm 100 --bridge-mm 2 --bridge-side top
PYTHONPATH=src python3 -m img2dxf.web --host 127.0.0.1 --port 8000
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 coverage run -m unittest discover -s tests && coverage report
```

The CLI converts raster artwork to a monochrome mask, traces black regions, and writes DXF polylines in millimeters.

## Coding Style & Naming Conventions

Use 4-space indentation for Python and descriptive snake_case names for modules, functions, and tests. Keep modules focused: image loading belongs in `image.py`, tracing in `vectorize.py`, DXF writing in `dxf.py`, and CLI wiring in `cli.py`.

## Testing Guidelines

Place tests in `tests/` and mirror the source layout where practical. Prefer deterministic tests that do not require connected laser hardware. Name tests after behavior, for example `test_single_black_pixel_becomes_square`. CI enforces at least 80% coverage through `coverage.py`.

## Commit & Pull Request Guidelines

This checkout has no Git metadata, so no existing commit convention is available. Use short imperative commit subjects such as `Add DXF writer` or `Document calibration workflow`. Pull requests should include a concise summary, test results, linked issues when applicable, and sample input/output files for conversion changes.

## Agent-Specific Instructions

Before editing, inspect the current tree and avoid overwriting user-created files. Keep repository guidance updated when adding new directories, tools, or workflows.
