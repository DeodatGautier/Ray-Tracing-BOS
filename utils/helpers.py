"""
utils/helpers.py - Helper functions for UI and other tasks.
"""

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QColor
from PyQt5.QtCore import Qt

def create_text_icon(text: str, size: int = 16, color: str = "#2c3e50") -> QIcon:
    """
    Create a QIcon with the given text drawn as a symbol.
    Useful for using emoji as icons in menus.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setFont(QFont("Segoe UI", size - 2))
    painter.setPen(QColor(color))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)