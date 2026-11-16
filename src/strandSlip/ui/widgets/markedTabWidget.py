"""A tab widget whose open tab is set apart and joined to its page.

What the tabs look like is in tabStyling; this keeps one tab widget's style in
step with the application's palette, for the program tabs and the tabs inside
a page alike, each under its own property so neither takes the other's style.

Rebuilding the style when the palette changes re-polishes every page under
the tabs, which is also what carries a theme switch into a page with a style
sheet of its own: before, Help > Theme > Light from dark left the whole Input
tab dark until the app was restarted.
"""

from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QTabWidget, QWidget

from strandSlip.ui.widgets.tabStyling import styleKey, tabStyleSheet


def scopeFor(propertyName: str) -> str:
    """The selector that keeps a style to the tab widgets carrying this property."""
    return f'QTabWidget[{propertyName}="true"]'


class MarkedTabWidget(QTabWidget):
    def __init__(
        self,
        propertyName: str,
        accentBar: int,
        padding: str,
        parent: QWidget | None = None,
    ) -> None:
        """accentBar: px of accent along the top of the open tab; padding: around each label."""
        super().__init__(parent)
        # Scoped on a property, not the object name, which a window may set.
        self.setProperty(propertyName, True)
        self.scope = scopeFor(propertyName)
        self.accentBar = accentBar
        self.padding = padding
        self.styledFor: tuple[str, str] | None = None
        self.applyTheme()
        application = QApplication.instance()
        if application is not None:
            # Deprecated in Qt 6 but still the one signal that carries the new
            # palette; a test fails loudly if a future PySide6 drops it.
            application.paletteChanged.connect(self.onPaletteChanged)

    def onPaletteChanged(self, *_args: object) -> None:
        self.applyTheme()
        # Once more after Qt has finished handing the new palette round the
        # window: the re-inherit in applyTheme must come after that hand-off.
        QTimer.singleShot(0, self, self.reinheritPalette)

    def applyTheme(self, *_args: object) -> None:
        """Set the open tab apart, and join it to the page it belongs to."""
        self.reinheritPalette()
        built = styleKey(self)
        if built == self.styledFor:
            return
        self.styledFor = built
        self.setStyleSheet(tabStyleSheet(self, self.scope, self.accentBar, self.padding))

    def reinheritPalette(self) -> None:
        """The safeguard Wager Book needed against a Qt quirk, kept here as it was.

        There a tab widget whose tabs carried a style sheet stopped taking
        palette changes, and after Help > Theme > Light the tables under it
        stayed dark. Not reproduced here on Qt 6.12. An empty palette tells the
        widget to inherit from its parent again; it fixes nothing in place, so
        the next switch is inherited the same way.
        """
        self.setPalette(QPalette())
