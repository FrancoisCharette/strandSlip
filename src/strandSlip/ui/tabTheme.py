"""The accent the open tab is marked with, for the light and the dark theme.

The indigo the Charette AI Group's other apps mark their open tab with (Wager
Book, The One Assets): deep on a light page, lifted on a dark one, where the
deep shade would sink into the background. Everything else about a tab's
colour comes from the window's own palette; see ui/widgets/tabStyling.
"""

from __future__ import annotations

from PySide6.QtGui import QColor

lightAccent = "#4a3aa7"
darkAccent = "#9085e9"


def accentFor(page: QColor) -> str:
    """The accent that reads on this page colour.

    Decided from the page itself rather than the colour-scheme setting, so it
    can never be a theme behind the palette it is drawn against.
    """
    return darkAccent if page.lightnessF() < 0.5 else lightAccent
