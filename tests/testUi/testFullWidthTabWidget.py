"""Tests for the full-width tab widget; how it marks the open tab is in testTabMarking."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from strandSlip.ui.widgets.fullWidthTabWidget import FullWidthTabWidget


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


def testTheWidthsHoldStillWhenAnotherTabIsOpened(qtbot) -> None:
    """The open tab's label is bold; each label is measured that way whichever is open.

    Measured as drawn, the bold label would take room from its neighbours and
    every tab would shift each time another was opened.
    """
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    for title in ("A", "B", "Sinusoid · SINUS BSINUS NSINUS and a few more words"):
        tabWidget.addTab(QWidget(), title)
    tabWidget.resize(420, 300)
    tabWidget.show()
    tabBar = tabWidget.tabBar()
    qtbot.waitUntil(lambda: tabBar.tabRect(2).width() > tabBar.tabRect(0).width(), timeout=5000)
    widths = [tabBar.tabRect(i).width() for i in range(tabBar.count())]

    for index in (2, 1, 0):
        tabWidget.setCurrentIndex(index)
        qtbot.wait(20)
        assert [tabBar.tabRect(i).width() for i in range(tabBar.count())] == widths


def testALabelTooLongForItsTabEndsInAnEllipsis(qtbot) -> None:
    """Rather than being cut at both ends; elided in bold, so the open tab's fits."""
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)

    assert tabWidget.tabBar().elideMode() == Qt.TextElideMode.ElideRight
    assert tabWidget.tabBar().font().bold()


def testThreeTabsShareThirds(qtbot) -> None:
    tabWidget = FullWidthTabWidget()
    qtbot.addWidget(tabWidget)
    for title in ("One", "Two", "Three"):
        tabWidget.addTab(QWidget(), title)
    tabWidget.resize(600, 400)
    tabWidget.show()

    qtbot.waitUntil(lambda: tabsFillHalves(tabWidget), timeout=5000)
