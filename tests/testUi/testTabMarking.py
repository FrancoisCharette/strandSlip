"""How the program tabs, and the tabs inside a page, show which tab is open."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QStandardItemModel
from PySide6.QtWidgets import QTableView, QVBoxLayout, QWidget

from strandSlip.ui import tabTheme
from strandSlip.ui.widgets import fullWidthTabWidget, pageTabWidget, tabStyling
from strandSlip.ui.widgets.fullWidthTabWidget import FullWidthTabWidget
from strandSlip.ui.widgets.pageTabWidget import PageTabWidget

bothLevels = pytest.mark.parametrize(
    ("tabClass", "module"),
    [(FullWidthTabWidget, fullWidthTabWidget), (PageTabWidget, pageTabWidget)],
    ids=["programTabs", "pageTabs"],
)


def rule(style: str, selector: str) -> str:
    """What one rule of a stylesheet declares."""
    return style.split(selector, 1)[1].split("}", 1)[0]


def withTabs(qtbot, tabClass, *titles: str):
    tabWidget = tabClass()
    qtbot.addWidget(tabWidget)
    for title in titles or ("First", "Second"):
        tabWidget.addTab(QWidget(), title)
    return tabWidget


@bothLevels
def testTheOpenTabIsPaintedLikeThePageBelowIt(qtbot, tabClass, module) -> None:
    """Tab and page share one surface; that is what says the page belongs to the tab."""
    tabWidget = withTabs(qtbot, tabClass)
    style = tabWidget.styleSheet()

    openTab = rule(style, "QTabBar::tab:selected {")
    # Left to Qt to resolve while painting, so the tab cannot drift from its page.
    assert "background: palette(window)" in openTab
    assert "border-bottom: 1px solid palette(window)" in openTab  # it opens into the page
    page, _ink = tabStyling.pageAndInk(tabWidget)
    accent = tabTheme.accentFor(page)
    assert f"border-top: {module.accentBar}px solid {accent}" in openTab
    assert "font-weight: bold" in openTab

    closedTab = rule(style, "> QTabBar::tab {")
    assert "background: palette(window)" not in closedTab  # a ground of its own
    assert "font-weight: normal" in closedTab
    assert "background: palette(window)" in rule(style, "::pane {")


def testThePageTabsAreMarkedMoreQuietlyThanTheProgramTabs() -> None:
    """A page's switch never competes with the window's."""
    assert pageTabWidget.accentBar < fullWidthTabWidget.accentBar
    assert pageTabWidget.scope != fullWidthTabWidget.scope


@bothLevels
def testTheStyleIsScopedToThisTabWidget(qtbot, tabClass, module) -> None:
    """Every rule names this widget's own property, so no other tabs or tables take it."""
    tabWidget = withTabs(qtbot, tabClass)
    style = tabWidget.styleSheet()

    assert tabWidget.property(module.scopeProperty) is True
    rules = [part.split("{", 1)[0].strip() for part in style.split("}") if "{" in part]
    assert rules and all(selector.startswith(module.scope) for selector in rules)


@bothLevels
def testTheDerivedTonesFollowTheApplicationsPalette(qtbot, qapp, tabClass, module) -> None:
    """The closed tabs' ground is worked out here, so it has to follow a theme change.

    A colour no real theme uses, so this cannot pass on the palette the suite
    happens to run under. The palette is in place by the time the application
    says it changed - the colour scheme signal comes too early to read.
    """
    tabWidget = withTabs(qtbot, tabClass)
    original = qapp.palette()
    try:
        palette = QPalette(original)
        palette.setColor(QPalette.ColorRole.Window, QColor("#123456"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#ffffff"))

        qapp.setPalette(palette)  # as the system does when it switches theme
        qtbot.wait(20)

        ground = tabStyling.blend(
            QColor("#123456"), QColor("#ffffff"), tabStyling.closedGround
        ).name()
        assert f"background: {ground}" in rule(tabWidget.styleSheet(), "> QTabBar::tab {")
        # A dark page takes the lifted accent, which still reads against it.
        assert tabTheme.darkAccent in rule(tabWidget.styleSheet(), "QTabBar::tab:selected {")
    finally:
        qapp.setPalette(original)


@bothLevels
def testAnUnchangedPaletteDoesNotRebuildTheStyle(qtbot, monkeypatch, tabClass, module) -> None:
    tabWidget = withTabs(qtbot, tabClass)
    rebuilt: list[str] = []
    monkeypatch.setattr(tabWidget, "setStyleSheet", rebuilt.append)

    tabWidget.applyTheme()

    assert rebuilt == []


def testTheAccentReadsOnEitherPage() -> None:
    assert tabTheme.accentFor(QColor("#f3f3f3")) == tabTheme.lightAccent
    assert tabTheme.accentFor(QColor("#202020")) == tabTheme.darkAccent
    assert tabTheme.lightAccent != tabTheme.darkAccent


def nestedTabsWithTable() -> tuple[QWidget, FullWidthTabWidget, PageTabWidget, QTableView]:
    """The window's shape: a table on a page's tabs, on the program tabs, in a window."""
    parent = QWidget()
    layout = QVBoxLayout(parent)
    programTabs = FullWidthTabWidget()
    pageTabs = PageTabWidget()
    table = QTableView()
    table.setModel(QStandardItemModel(2, 2))
    pageTabs.addTab(table, "Table")
    programTabs.addTab(pageTabs, "Sinusoid")
    layout.addWidget(programTabs)
    return parent, programTabs, pageTabs, table


def testAThemeSwitchReachesTheTablesUnderTheTabs(qtbot, qapp, observableColorScheme) -> None:
    """Wager Book met a Qt quirk where a nested tab widget with styled tabs
    stopped taking palette changes, leaving its tables dark after Help > Theme >
    Light. Not seen here on Qt 6.12; this keeps it that way, two levels deep.
    Only a real scheme change shows it, so this skips on the offscreen plugin
    and runs under a plain `pytest` on Windows."""
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    hints = qapp.styleHints()
    hints.setColorScheme(Qt.ColorScheme.Dark)
    parent, _programTabs, _pageTabs, table = nestedTabsWithTable()
    qtbot.addWidget(parent)
    parent.show()
    qtbot.wait(200)

    for scheme in (Qt.ColorScheme.Light, Qt.ColorScheme.Dark, Qt.ColorScheme.Light):
        hints.setColorScheme(scheme)
        qtbot.waitUntil(
            lambda: table.palette().base().color() == qapp.palette().base().color(),
            timeout=3000,
        )


@bothLevels
def testAThemeSwitchRestylesTheTabsForTheNewPage(
    qtbot, qapp, observableColorScheme, tabClass, module
) -> None:
    """Help > Theme: the closed tabs' ground and the accent follow the new page."""
    if not observableColorScheme:
        pytest.skip("this platform plugin does not report a forced colour scheme")
    hints = qapp.styleHints()
    hints.setColorScheme(Qt.ColorScheme.Light)
    tabWidget = withTabs(qtbot, tabClass)
    tabWidget.show()
    qtbot.wait(200)

    hints.setColorScheme(Qt.ColorScheme.Dark)

    qtbot.waitUntil(lambda: tabTheme.darkAccent in tabWidget.styleSheet(), timeout=3000)


def testRestylingLeavesNoFixedPaletteBehind(qtbot) -> None:
    """A fixed palette would stop the next theme switch reaching the tables."""
    parent, programTabs, pageTabs, _table = nestedTabsWithTable()
    qtbot.addWidget(parent)

    programTabs.applyTheme()
    pageTabs.applyTheme()

    assert not programTabs.testAttribute(Qt.WidgetAttribute.WA_SetPalette)
    assert not pageTabs.testAttribute(Qt.WidgetAttribute.WA_SetPalette)
