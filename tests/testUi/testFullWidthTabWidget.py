"""Tests for the full-width tab widget."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from masterRebuild.ui.widgets.fullWidthTabWidget import FullWidthTabWidget


def tabsFillHalves(tabWidget: FullWidthTabWidget) -> bool:
    tabBar = tabWidget.tabBar()
    share = tabWidget.width() // tabBar.count()
    return all(
        abs(tabBar.tabRect(i).width() - share) <= 1 for i in range(tabBar.count())
    )


def testTabsShareWidthEqually(qtbot) -> None:
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    tabWidget.addTab(QWidget(), "First")
    tabWidget.addTab(QWidget(), "Second")
    tabWidget.resize(600, 400)
    tabWidget.show()

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)


def testTabsKeepEqualShareAfterResize(qtbot) -> None:
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    tabWidget.addTab(QWidget(), "First")
    tabWidget.addTab(QWidget(), "Second")
    tabWidget.resize(600, 400)
    tabWidget.show()
    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)

    tabWidget.resize(840, 400)

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)


def testALongLabelGetsTheRoomItNeeds(qtbot) -> None:
    """When an equal share would cut a label, widths follow the labels instead."""
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    long = "Sinusoid · SINUS BSINUS NSINUS and a few more words"
    for title in ("A", "B", long):
        tabWidget.addTab(QWidget(), title)
    tabWidget.resize(420, 300)
    tabWidget.show()
    tabBar = tabWidget.tabBar()

    def longIsWidest() -> bool:
        widths = [tabBar.tabRect(i).width() for i in range(tabBar.count())]
        return widths[2] > widths[0] and sum(widths) >= tabWidget.width() - tabBar.count()

    qtbot.waitUntil(longIsWidest, timeout=5000)


def testThreeTabsShareThirds(qtbot) -> None:
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    for title in ("One", "Two", "Three"):
        tabWidget.addTab(QWidget(), title)
    tabWidget.resize(600, 400)
    tabWidget.show()

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)
