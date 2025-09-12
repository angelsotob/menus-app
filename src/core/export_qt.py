from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMarginsF, QPoint, QPointF
from PySide6.QtGui import QImage, QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrinter
from PySide6.QtWidgets import QWidget


def export_widget_to_pdf(widget: QWidget, path: str | Path) -> None:
    """Renders the widget to PDF, adjusting and centering the content to A4 with margins.."""
    path = str(path)
    printer = QPrinter(QPrinter.HighResolution)
    printer.setOutputFormat(QPrinter.PdfFormat)
    printer.setOutputFileName(path)

    # A4 vertical + margins in millimeters
    printer.setPageSize(QPageSize(QPageSize.A4))
    printer.setPageOrientation(QPageLayout.Portrait)
    printer.setPageMargins(QMarginsF(12, 12, 12, 12), QPageLayout.Unit.Millimeter)

    painter = QPainter()
    try:
        if not painter.begin(printer):
            return

        # Printable area in pixels of the device
        layout = printer.pageLayout()
        page_rect = layout.paintRectPixels(printer.resolution())
        pw, ph = float(page_rect.width()), float(page_rect.height())
        ww, wh = float(widget.width()), float(widget.height())
        if ww <= 0 or wh <= 0 or pw <= 0 or ph <= 0:
            # Fallback
            widget.render(painter, QPoint(0, 0))
            return

        # Uniform scaling to fit the print area
        sx = pw / ww
        sy = ph / wh
        scale = min(sx, sy)

        # Centered
        tx = (pw - ww * scale) / 2.0
        ty = (ph - wh * scale) / 2.0

        painter.translate(QPointF(tx, ty))
        painter.scale(scale, scale)
        widget.render(painter, QPoint(0, 0))
    finally:
        painter.end()


def export_widget_to_image(
    widget: QWidget,
    path: str | Path,
    fmt: str = "PNG",
    scale: float = 2.0,
) -> None:
    """Render widget to image (PNG/JPEG) with scale factor."""
    w = max(1, int(widget.width() * scale))
    h = max(1, int(widget.height() * scale))
    image = QImage(w, h, QImage.Format_ARGB32)
    image.fill(0x00000000)

    painter = QPainter()
    try:
        if not painter.begin(image):
            return
        painter.scale(scale, scale)
        widget.render(painter, QPoint(0, 0))
    finally:
        painter.end()

    fmt = fmt.upper()
    if fmt in {"JPG", "JPEG"}:
        fmt = "JPEG"

    image.save(str(path), fmt)
