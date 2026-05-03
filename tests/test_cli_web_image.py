import base64
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

from img2dxf.cli import main as cli_main
from img2dxf.dxf import dxf_text, write_dxf
from img2dxf.image import load_monochrome, mask_to_preview, otsu_threshold, save_preview
from img2dxf.web import (
    decode_data_url,
    parse_float,
    parse_int,
    parse_optional_float,
    parse_optional_nonnegative_float,
    parse_threshold,
)


def sample_png() -> BytesIO:
    image = Image.new("RGB", (6, 4), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((1, 1, 4, 2), fill="black")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


class ImageProcessingTests(unittest.TestCase):
    def test_load_monochrome_supports_invert_and_small_component_cleanup(self):
        image = Image.new("L", (4, 3), 255)
        pixels = image.load()
        pixels[0, 0] = 0
        pixels[2, 1] = 0
        pixels[3, 1] = 0
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        mask, preview, threshold = load_monochrome(
            buffer,
            threshold=128,
            min_area_px=2,
        )

        self.assertEqual(threshold, 128)
        self.assertFalse(mask[0][0])
        self.assertTrue(mask[1][2])
        self.assertEqual(preview.size, (4, 3))

        buffer.seek(0)
        inverted, _, _ = load_monochrome(buffer, threshold=128, invert=True)

        self.assertFalse(inverted[1][2])
        self.assertTrue(inverted[0][1])

    def test_load_monochrome_rejects_invalid_threshold(self):
        with self.assertRaises(ValueError):
            load_monochrome(sample_png(), threshold=300)

    def test_preview_helpers_write_png(self):
        preview = mask_to_preview([[True, False], [False, True]])

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "nested" / "preview.png"
            save_preview(preview, str(output))

            self.assertTrue(output.exists())
            self.assertTrue(output.read_bytes().startswith(b"\x89PNG"))

    def test_otsu_threshold_handles_empty_histogram(self):
        self.assertEqual(otsu_threshold([]), 127)


class DxfWriterTests(unittest.TestCase):
    def test_dxf_skips_short_polylines_and_formats_numbers(self):
        dxf = dxf_text(
            [
                [(1, 2), (3, 4)],
                [(0, 0), (1.5, 0), (1.5, 2)],
            ],
            layer=" CUT ",
            color=3,
        )

        self.assertEqual(dxf.count("LWPOLYLINE"), 1)
        self.assertIn("\n8\nCUT\n", dxf)
        self.assertIn("\n10\n1.5\n", dxf)

    def test_write_dxf_writes_ascii_file(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "part.dxf"

            write_dxf(str(output), [[(0, 0), (1, 0), (1, 1)]])

            self.assertIn("EOF", output.read_text(encoding="ascii"))


class CliTests(unittest.TestCase):
    def test_cli_writes_dxf_and_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.png"
            output = Path(directory) / "output.dxf"
            preview = Path(directory) / "preview.png"
            source.write_bytes(sample_png().getvalue())

            exit_code = cli_main(
                [
                    str(source),
                    str(output),
                    "--width-mm",
                    "30",
                    "--simplify-mm",
                    "0.2",
                    "--mono-output",
                    str(preview),
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("LWPOLYLINE", output.read_text(encoding="ascii"))
            self.assertTrue(preview.exists())


class WebHelperTests(unittest.TestCase):
    def test_decode_data_url_accepts_plain_and_data_url_base64(self):
        encoded = base64.b64encode(b"image").decode("ascii")

        self.assertEqual(decode_data_url(encoded), b"image")
        self.assertEqual(decode_data_url(f"data:image/png;base64,{encoded}"), b"image")

    def test_parse_helpers_validate_numbers(self):
        self.assertEqual(parse_threshold({"autoThreshold": True}), None)
        self.assertEqual(parse_threshold({"autoThreshold": False, "threshold": "90"}), 90)
        self.assertEqual(parse_optional_float("12.5"), 12.5)
        self.assertEqual(parse_optional_nonnegative_float("0"), 0.0)
        self.assertEqual(parse_float("", 1.25), 1.25)
        self.assertEqual(parse_int("", 7), 7)

        with self.assertRaises(ValueError):
            parse_threshold({"autoThreshold": False, "threshold": "999"})
        with self.assertRaises(ValueError):
            parse_optional_float("-1")
        with self.assertRaises(ValueError):
            parse_optional_nonnegative_float("-0.1")


if __name__ == "__main__":
    unittest.main()
