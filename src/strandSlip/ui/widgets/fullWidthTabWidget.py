"""Tab widget whose tabs share the full width, labels centered.

These are the window's switch between programs, so the open one carries the
thicker accent bar; how a tab is marked is in tabStyling. The labels keep the
interface's own size, where Wager Book makes its two 15% larger: seven labels
this long would then need some 1250 of the 1320 px the window opens at, and
be cut short in any window much narrower.

Equal shares while every label fits in one; otherwise each tab gets the full
width in proportion to its label, so a long label is not cut short by a short
neighbour's spare room. A label is measured as the open tab draws it, in bold,
whichever tab is open, so the widths hold still when another tab is opened.
In a window too narrow for all of them a label ends in an ellipsis rather
than being cut at both ends.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QFontMetrics, QResizeEvent
from PySide6.QtWidgets import QTabBar, QWidget

from strandSlip.ui.widgets.markedTabWidget import MarkedTabWidget, scopeFor

accentBar = 3  # px of accent along the top of the open tab
sidePadding = 10  # px either side of a label
padding = f"5px {sidePadding}px"
labelRoom = 2 * (sidePadding + 1) + 4  # px beside a label: padding, edges and a little air
scopeProperty = "topLevelTabs"
# The scope of this widget's own style, so the tabs inside its pages keep theirs.
scope = scopeFor(scopeProperty)


class FullWidthTabBar(QTabBar):
    def tabSizeHint(self, index: int) -> QSize:
        size = super().tabSizeHint(index)
        tabWidget = self.parentWidget()
        if self.count() and tabWidget is not None:
            share = tabWidget.width() // self.count()
            room = [self.roomFor(i) for i in range(self.count())]
            if max(room) <= share:
                size.setWidth(share)
            else:
                size.setWidth(tabWidget.width() * room[index] // sum(room))
        return size

    def roomFor(self, index: int) -> int:
        """What a label needs as the open tab, in bold."""
        font = QFont(self.font())
        font.setBold(True)
        return QFontMetrics(font).horizontalAdvance(self.tabText(index)) + labelRoom


class FullWidthTabWidget(MarkedTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(scopeProperty, accentBar, padding, parent)
        tabBar = FullWidthTabBar(self)
        # Qt elides with the tab bar's own font: bold, as the open tab is drawn,
        # so what is left of its label fits. The style sheet still draws the
        # closed tabs in the normal weight.
        font = QFont(tabBar.font())
        font.setBold(True)
        tabBar.setFont(font)
        tabBar.setElideMode(Qt.TextElideMode.ElideRight)
        self.setTabBar(tabBar)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # Tab widths derive from the widget width, so a resize must make the
        # tab bar re-query its size hints. QTabBar has no public relayout;
        # re-setting the icon size is the standard way to force one.
        super().resizeEvent(event)
        tabBar = self.tabBar()
        tabBar.setIconSize(tabBar.iconSize())
