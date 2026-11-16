"""The tabs within a page - Table, Summary, Screen Output - marked the same way, more quietly.

Same rule as the program tabs above them, at the interface's own text size
and under a thinner accent bar, so a page's switch never competes with the
window's - as The One Assets marks its page tabs. How a tab is marked is in
tabStyling.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from strandSlip.ui.widgets.markedTabWidget import MarkedTabWidget, scopeFor

accentBar = 2  # px of accent along the top of the open tab, thinner than the window's
padding = "4px 14px"
scopeProperty = "pageTabs"
# The scope of this widget's own style, so the program tabs keep theirs.
scope = scopeFor(scopeProperty)


class PageTabWidget(MarkedTabWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(scopeProperty, accentBar, padding, parent)
