from __future__ import annotations

import argparse
import base64
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from io import BytesIO
from typing import Any

from .convert import ConversionOptions, convert_image

MAX_UPLOAD_BYTES = 25 * 1024 * 1024


class ConverterHandler(BaseHTTPRequestHandler):
    server_version = "img2dxf-web/0.1"

    def do_GET(self) -> None:
        if self.path in {"/", "/index.html"}:
            html = files("img2dxf").joinpath("web_assets/index.html").read_bytes()
            self._send_bytes(html, "text/html; charset=utf-8")
            return
        if self.path in {"/app-icon.svg", "/favicon.svg"}:
            icon = files("img2dxf").joinpath("web_assets/app-icon.svg").read_bytes()
            self._send_bytes(icon, "image/svg+xml")
            return
        if self.path == "/health":
            self._send_json({"ok": True})
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if self.path != "/api/convert":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            payload = self._read_json()
            image_bytes = decode_data_url(str(payload["image"]))
            options = ConversionOptions(
                threshold=parse_threshold(payload),
                invert=bool(payload.get("invert", False)),
                width_mm=parse_optional_float(payload.get("widthMm")),
                scale_mm_per_pixel=None,
                bridge_mm=parse_float(payload.get("bridgeMm"), 0.0),
                bridge_side=str(payload.get("bridgeSide") or "top"),
                simplify=parse_float(payload.get("simplify"), 0.75),
                min_area_px=parse_int(payload.get("minAreaPx"), 0),
                layer=str(payload.get("layer") or "CUT")[:64],
                color=parse_int(payload.get("color"), 1),
            )
            result = convert_image(BytesIO(image_bytes), options)
        except Exception as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            return

        self._send_json(
            {
                "widthPx": result.width_px,
                "heightPx": result.height_px,
                "threshold": result.threshold,
                "scaleMmPerPixel": result.scale_mm_per_pixel,
                "bridgeWidthPx": result.bridge_width_px,
                "bridgesCreated": result.bridges_created,
                "pathCount": result.path_count,
                "nodeCount": result.node_count,
                "previewPng": "data:image/png;base64,"
                + base64.b64encode(result.preview_png).decode("ascii"),
                "svg": result.svg,
                "dxf": result.dxf,
            }
        )

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            raise ValueError("empty request body")
        if length > MAX_UPLOAD_BYTES:
            raise ValueError("image is too large")
        data = self.rfile.read(length)
        return json.loads(data.decode("utf-8"))

    def _send_json(
        self,
        payload: dict[str, Any],
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_bytes(self, data: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def decode_data_url(value: str) -> bytes:
    if "," in value:
        value = value.split(",", 1)[1]
    return base64.b64decode(value, validate=True)


def parse_threshold(payload: dict[str, Any]) -> int | None:
    if payload.get("autoThreshold", True):
        return None
    threshold = parse_int(payload.get("threshold"), 128)
    if not 0 <= threshold <= 255:
        raise ValueError("threshold must be between 0 and 255")
    return threshold


def parse_optional_float(value: Any) -> float | None:
    if value in {None, ""}:
        return None
    parsed = float(value)
    if parsed <= 0:
        raise ValueError("width must be greater than 0")
    return parsed


def parse_float(value: Any, default: float) -> float:
    if value in {None, ""}:
        return default
    return float(value)


def parse_int(value: Any, default: int) -> int:
    if value in {None, ""}:
        return default
    return int(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the img2dxf web UI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    server = ThreadingHTTPServer((args.host, args.port), ConverterHandler)
    print(f"img2dxf web UI: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
