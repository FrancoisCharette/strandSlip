"""Tab widget whose tabs share the full width, labels centered.

Equal shares while every label fits in one; otherwise each tab gets the full
width in proportion to its label, so a long label is not cut short by a short
neighbour's spare room.
"""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QTabBar, QTabWidget, QWidget


class FullWidthTabBar(QTabBar):
    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        tabWidget = self.parentWidget()
        if self.count() and tabWidget is not None:
            share = tabWidget.width() // self.count()
            natural = [
                super(FullWidthTabBar, self).tabSizeHint(i).width() for i in range(self.count())
            ]
            if max(natural) <= share:
                size.setWidth(share)
            else:
                size.setWidth(tabWidget.width() * natural[index] // sum(natural))
        return size


class FullWidthTabWidget(QTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTabBar(FullWidthTabBar(self))

    def resizeEvent(self, event: QResizeEvent) -> None:
        # Tab widths derive from the widget width, so a resize must make the
        # tab bar re-query its size hints. QTabBar has no public relayout;
        # re-setting the icon size is the standard way to force one.
        super().resizeEvent(event)
        tabBar = self.tabBar()
        tabBar.setIconSize(tabBar.iconSize())
