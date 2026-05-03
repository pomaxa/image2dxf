from __future__ import annotations

Point = tuple[float, float]


def write_dxf(
    path: str,
    polylines: list[list[Point]],
    *,
    layer: str = "CUT",
    color: int = 1,
) -> None:
    """Write closed LWPOLYLINE entities to a minimal ASCII DXF file."""
    with open(path, "w", encoding="ascii") as handle:
        handle.write(dxf_text(polylines, layer=layer, color=color))


def dxf_text(
    polylines: list[list[Point]],
    *,
    layer: str = "CUT",
    color: int = 1,
) -> str:
    """Return a minimal ASCII DXF document with closed LWPOLYLINE entities."""
    layer = _safe_dxf_name(layer, fallback="CUT")
    lines: list[str] = [
        "0",
        "SECTION",
        "2",
        "HEADER",
        "9",
        "$ACADVER",
        "1",
        "AC1015",
        "9",
        "$INSUNITS",
        "70",
        "4",
        "0",
        "ENDSEC",
        "0",
        "SECTION",
        "2",
        "ENTITIES",
    ]

    for polyline in polylines:
        if len(polyline) < 3:
            continue
        lines.extend(
            [
                "0",
                "LWPOLYLINE",
                "8",
                layer,
                "62",
                str(color),
                "90",
                str(len(polyline)),
                "70",
                "1",
            ]
        )
        for x, y in polyline:
            lines.extend(["10", _fmt(x), "20", _fmt(y)])

    lines.extend(["0", "ENDSEC", "0", "EOF", ""])
    return "\n".join(lines)


def _fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def _safe_dxf_name(value: str, *, fallback: str) -> str:
    safe = "".join(
        char if 32 <= ord(char) <= 126 and char not in "\r\n" else "_"
        for char in value.strip()
    )
    return safe or fallback
