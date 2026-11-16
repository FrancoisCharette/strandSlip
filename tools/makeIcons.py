"""Draw Strand Slip's application icon, the way Wager Book and The One Assets draw theirs.

The icon is drawn with QPainter *at each size* rather than scaled down from
one large rendering, because a 16 px icon shrunk from 256 px is mush: its
strokes fall below a pixel and the shape stops reading. Each size keeps fewer
wires and drops detail as it shrinks.

The artwork: the section of a strand on a tile in the group's indigo accent.
A steel core, ringed by aluminium wires lying side by side as in the 1991
strand, and one wire in coral - the one that slips - with a short arrow
beside it showing it on the move.

    python tools/makeIcons.py

Writes ``src/strandSlip/resources/strandSlip.ico`` (16 to 256 px) and a
1024 px PNG of the same drawing. The app finds them through ``appConfig``,
never by path.
"""

from __future__ import annotations

import math
import os
import struct
from pathlib import Path

# Before any QApplication exists: draw on the real platform, not offscreen.
os.environ.pop("QT_QPA_PLATFORM", None)

repo = Path(__file__).resolve().parents[1]
outputDir = repo / "src" / "strandSlip" / "resources"
stem = "strandSlip"

from PySide6.QtCore import QBuffer, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import (  # noqa: E402
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QApplication  # noqa: E402

# What a .ico carries: 16 is the title bar and taskbar, 256 the extra-large
# view in Explorer; the sizes between are what Windows picks at other DPIs.
iconSizes = (16, 24, 32, 48, 64, 128, 256)

tileTop = QColor("#5B4BC4")  # the tabs' accent, lifted
tileBottom = QColor("#2E2373")
coreLight = QColor("#A9B1C2")  # steel
coreDark = QColor("#6B7385")
wireLight = QColor("#F4F6FA")  # aluminium
wireDark = QColor("#C3C9D6")
wireEdge = QColor("#2A2160")
slipColour = QColor("#FB7185")  # the wire that slips
slipDark = QColor("#E11D48")

slipAngle = 45.0  # degrees from three o'clock, anticlockwise: the top-right wire


def wireCount(size: int) -> int:
    """Fewer, larger wires as the icon shrinks, so each one still reads as a wire."""
    if size < 24:
        return 6
    if size < 48:
        return 8
    return 10


def outerRadius(size: int) -> float:
    """The strand's outer radius: smaller where the slip arrow needs room outside it."""
    return size * (0.42 if size < 32 else 0.33)


def wireRadius(size: int) -> float:
    """Wires touching their neighbours around the core: w = (c + w) sin(π/n)."""
    share = math.sin(math.pi / wireCount(size))
    return outerRadius(size) * share / (1 + share)


def coreRadius(size: int) -> float:
    return outerRadius(size) - 2 * wireRadius(size)


def centre(size: int) -> QPointF:
    return QPointF(size * 0.5, size * 0.5)


def drawTile(painter: QPainter, size: int) -> None:
    # Tighter corners when small, or the rounding eats the artwork.
    radius = size * (0.18 if size < 32 else 0.22)
    gradient = QLinearGradient(QPointF(0, 0), QPointF(0, size))
    gradient.setColorAt(0.0, tileTop)
    gradient.setColorAt(1.0, tileBottom)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)


def drawDisc(
    painter: QPainter, middle: QPointF, radius: float, light: QColor, dark: QColor, edge: float
) -> None:
    """A round section, lit from the top left so it reads as metal."""
    gradient = QRadialGradient(middle + QPointF(-radius * 0.35, -radius * 0.35), radius * 1.4)
    gradient.setColorAt(0.0, light)
    gradient.setColorAt(1.0, dark)
    painter.setBrush(gradient)
    painter.setPen(QPen(wireEdge, edge) if edge > 0 else Qt.PenStyle.NoPen)
    painter.drawEllipse(middle, radius, radius)


def drawStrand(painter: QPainter, size: int) -> None:
    middle = centre(size)
    core = coreRadius(size)
    wire = wireRadius(size)
    ring = core + wire
    count = wireCount(size)
    edge = 0.0 if size < 32 else max(1.0, size * 0.008)
    drawDisc(painter, middle, core, coreLight, coreDark, edge)
    # One wire sits on the slip angle; the others are spaced evenly from it.
    for index in range(count):
        angle = math.radians(slipAngle + index * 360.0 / count)
        at = middle + QPointF(ring * math.cos(angle), -ring * math.sin(angle))
        slipping = index == 0
        light, dark = (slipColour, slipDark) if slipping else (wireLight, wireDark)
        drawDisc(painter, at, wire, light, dark, edge)


def drawSlipArrow(painter: QPainter, size: int) -> None:
    """An arc just outside the coral wire, pointing round the ring: it is moving."""
    if size < 32:
        return  # below this the arrow is a smudge beside the wire
    middle = centre(size)
    reach = outerRadius(size) + size * 0.065
    width = max(1.6, size * 0.035)
    box = QRectF(middle.x() - reach, middle.y() - reach, 2 * reach, 2 * reach)
    span = 34.0
    start = slipAngle - span / 2
    pen = QPen(QBrush(slipColour), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(box, round(start * 16), round(span * 16))
    # The head at the anticlockwise end, along the tangent.
    tip = math.radians(start + span)
    point = middle + QPointF(reach * math.cos(tip), -reach * math.sin(tip))
    tangent = QPointF(-math.sin(tip), -math.cos(tip))
    normal = QPointF(math.cos(tip), -math.sin(tip))
    head = size * 0.06
    path = QPainterPath()
    path.moveTo(point + tangent * head)
    path.lineTo(point - tangent * (head * 0.25) + normal * (head * 0.75))
    path.lineTo(point - tangent * (head * 0.25) - normal * (head * 0.75))
    path.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(slipColour)
    painter.drawPath(path)


def render(size: int) -> QPixmap:
    """The icon at one size, drawn rather than scaled."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    drawTile(painter, size)
    drawStrand(painter, size)
    drawSlipArrow(painter, size)
    painter.end()
    return pixmap


def pngBytes(pixmap: QPixmap) -> bytes:
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return bytes(buffer.data())


def packIco(images: list[tuple[int, bytes]]) -> bytes:
    """A multi-size .ico holding PNG entries.

    Written by hand rather than through Qt's writer, so every size is the one
    drawn at that size. Windows since Vista reads PNG inside an ICO, which
    keeps the 256 px entry small.
    """
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, payload = [], []
    for size, data in images:
        side = 0 if size >= 256 else size  # 0 means 256 in an ICO
        entries.append(struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(data), offset))
        payload.append(data)
        offset += len(data)
    return header + b"".join(entries) + b"".join(payload)


def main() -> int:
    application = QApplication.instance() or QApplication([])  # noqa: F841 - kept alive
    outputDir.mkdir(parents=True, exist_ok=True)
    ico = outputDir / f"{stem}.ico"
    ico.write_bytes(packIco([(size, pngBytes(render(size))) for size in iconSizes]))
    png = outputDir / f"{stem}.png"
    render(1024).save(str(png), "PNG")
    sizes = "/".join(str(size) for size in iconSizes)
    print(f"{ico.relative_to(repo)}  {ico.stat().st_size / 1024:.1f} kB  ({sizes} px)")
    print(f"{png.relative_to(repo)}  1024 px")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
