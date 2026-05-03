import unittest
from io import BytesIO

from PIL import Image, ImageDraw

from img2dxf.bridges import (
    add_island_bridges,
    bridge_width_to_px,
    label_black_components,
)
from img2dxf.convert import (
    ConversionOptions,
    convert_image,
    resolve_simplify_tolerance_px,
)
from img2dxf.dxf import dxf_text
from img2dxf.vectorize import to_mm_polylines, trace_mask


class TraceMaskTests(unittest.TestCase):
    def test_single_black_pixel_becomes_square(self):
        paths = trace_mask([[True]], simplify=0)

        self.assertEqual(len(paths), 1)
        self.assertEqual(set(paths[0]), {(0, 0), (1, 0), (1, 1), (0, 1)})

    def test_adjacent_pixels_share_one_outer_boundary(self):
        paths = trace_mask([[True, True]], simplify=0)

        self.assertEqual(len(paths), 1)
        self.assertEqual(set(paths[0]), {(0, 0), (2, 0), (2, 1), (0, 1)})

    def test_separate_pixels_make_separate_paths(self):
        paths = trace_mask([[True, False, True]], simplify=0)

        self.assertEqual(len(paths), 2)

    def test_coordinates_convert_to_bottom_left_mm(self):
        polylines = to_mm_polylines(
            [[(0, 0), (2, 0), (2, 1), (0, 1)]],
            image_height_px=1,
            scale_mm_per_pixel=5,
        )

        self.assertEqual(
            polylines[0],
            [(0, 5), (10, 5), (10, 0), (0, 0)],
        )


class ConvertImageTests(unittest.TestCase):
    def test_convert_image_returns_preview_and_dxf(self):
        image = Image.new("RGB", (8, 6), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 1, 5, 4), fill="black")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        result = convert_image(
            buffer,
            ConversionOptions(width_mm=16, threshold=128, simplify=0),
        )

        self.assertEqual(result.width_px, 8)
        self.assertEqual(result.height_px, 6)
        self.assertEqual(result.path_count, 1)
        self.assertIn("LWPOLYLINE", result.dxf)
        self.assertTrue(result.preview_png.startswith(b"\x89PNG"))

    def test_convert_image_can_add_bridges(self):
        image = Image.new("RGB", (7, 7), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((1, 1, 5, 5), fill="black")
        draw.rectangle((2, 2, 4, 4), fill="white")
        draw.point((3, 3), fill="black")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        result = convert_image(
            buffer,
            ConversionOptions(threshold=128, bridge_mm=1, scale_mm_per_pixel=1),
        )

        self.assertEqual(result.bridges_created, 1)
        self.assertEqual(result.bridge_width_px, 1)

    def test_convert_image_accepts_simplify_in_mm(self):
        image = Image.new("RGB", (8, 6), "white")
        draw = ImageDraw.Draw(image)
        draw.rectangle((2, 1, 5, 4), fill="black")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        result = convert_image(
            buffer,
            ConversionOptions(threshold=128, width_mm=16, simplify_mm=0.5),
        )

        self.assertAlmostEqual(result.simplify_tolerance_px, 0.25)
        self.assertAlmostEqual(result.simplify_tolerance_mm, 0.5)

    def test_simplify_mm_overrides_pixel_tolerance(self):
        tolerance = resolve_simplify_tolerance_px(
            scale_mm_per_pixel=0.2,
            simplify_px=9,
            simplify_mm=0.5,
        )

        self.assertAlmostEqual(tolerance, 2.5)


class DxfTests(unittest.TestCase):
    def test_non_ascii_layer_is_sanitized(self):
        dxf = dxf_text([[(0, 0), (1, 0), (1, 1)]], layer="Резка")

        self.assertIn("_____", dxf)
        dxf.encode("ascii")


class BridgeTests(unittest.TestCase):
    def test_inner_black_island_is_connected_to_main_component(self):
        mask = [
            [False, False, False, False, False, False, False],
            [False, True, True, True, True, True, False],
            [False, True, False, False, False, True, False],
            [False, True, False, True, False, True, False],
            [False, True, False, False, False, True, False],
            [False, True, True, True, True, True, False],
            [False, False, False, False, False, False, False],
        ]

        bridged, count = add_island_bridges(mask, bridge_width_px=1)
        _, components = label_black_components(bridged)

        self.assertEqual(count, 1)
        self.assertEqual(len(components), 1)
        self.assertTrue(bridged[2][3])
        self.assertFalse(bridged[4][3])

    def test_bridge_can_be_moved_to_bottom(self):
        mask = [
            [False, False, False, False, False, False, False],
            [False, True, True, True, True, True, False],
            [False, True, False, False, False, True, False],
            [False, True, False, True, False, True, False],
            [False, True, False, False, False, True, False],
            [False, True, True, True, True, True, False],
            [False, False, False, False, False, False, False],
        ]

        bridged, count = add_island_bridges(
            mask,
            bridge_width_px=1,
            bridge_side="bottom",
        )

        self.assertEqual(count, 1)
        self.assertFalse(bridged[2][3])
        self.assertTrue(bridged[4][3])

    def test_bridge_width_uses_scale_and_rounds_up(self):
        self.assertEqual(bridge_width_to_px(2.0, 0.75), 3)


if __name__ == "__main__":
    unittest.main()
