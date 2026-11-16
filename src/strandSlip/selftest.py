"""Check that a build has everything it needs, and say so.

Worth having because what packaging loses, it loses quietly. A missing icon
gives a blank tile, a missing manual or legacy folder gives a Help item that
opens nothing offline, and a missing piece of numpy or matplotlib shows up
only when a program is run. None of them crashes at start. A build can look
fine from the outside and be broken in exactly the ways nobody checks by hand.

So the build runs this and refuses to publish a bundle that fails it:

    StrandSlip.exe --selftest report.txt

Everything here is read-only. The window is built against a throwaway
settings file, so it never reads or writes the user's settings. It makes no
network request.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from strandSlip import appConfig

expectedTabs = 5


def resourceChecks() -> list[tuple[str, bool, str]]:
    """Every bundled file the app reaches for, and whether it is there."""
    sources = appConfig.legacySourcesDir
    listing = sources / "manuel1992" / "README.md"
    return [
        ("applicationIcon", appConfig.iconFile.is_file(), str(appConfig.iconFile)),
        ("manual", appConfig.manualPath.is_file(), str(appConfig.manualPath)),
        ("legacySources", listing.is_file(), str(sources)),
    ]


def engineCheck() -> tuple[bool, str]:
    """Run SINUS and HARDRHOB on the examples: numpy and both engines came along."""
    try:
        from strandSlip.models.legacyProgram import SINUS
        from strandSlip.models.strandPresets import defaultPreset
        from strandSlip.models.thesisInput import ThesisInput
        from strandSlip.models.thesisProgram import thesisProgramByKey
        from strandSlip.services.analysisRunner import runAndPresent
        from strandSlip.services.thesisTables import runAndPresentThesis

        stiffness = runAndPresent(SINUS, defaultPreset.input).result
        thesis = runAndPresentThesis(thesisProgramByKey["HARDRHOB"], ThesisInput()).result
    except Exception as exc:  # a build that cannot compute must say why
        return False, f"{type(exc).__name__}: {exc}"
    positions = len(stiffness.positions)
    bound = thesis.halfPitches[0].lowerBound if thesis.halfPitches else None
    if positions != 102 or bound is None or round(bound, 5) != 0.14758:
        return False, f"unexpected results: {positions} positions, XB1 = {bound}"
    return True, f"SINUS {positions} positions, HARDRHOB XB1 = {bound:.5f}"


def windowCheck() -> tuple[bool, str]:
    """Build the window offscreen: proof that Qt, matplotlib and every import came up.

    The heaviest thing a packaged build can drop is a Qt plugin, and that
    shows up here rather than as a window that never appears on a machine
    with no console to print the reason to.
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    scratch = Path(tempfile.mkdtemp(prefix="strandSlipSelftest"))
    appConfig.settingsFile = scratch / "settings.ini"
    try:
        from PySide6.QtWidgets import QApplication

        from strandSlip.main import setAppIdentity
        from strandSlip.ui.mainWindow import MainWindow

        application = QApplication.instance() or QApplication([])
        setAppIdentity(application)
        window = MainWindow()
        title = window.windowTitle()
        wornIcon = not window.windowIcon().isNull()
        tabs = window.tabs.count()
        window.close()
        del application
    except Exception as exc:  # a build that cannot start must say why
        return False, f"{type(exc).__name__}: {exc}"
    if not title:
        return False, "the window has no title"
    if not wornIcon:
        return False, "the window is not wearing its icon"
    if tabs != expectedTabs:
        return False, f"expected {expectedTabs} tabs, found {tabs}"
    return True, title


def report() -> tuple[str, bool]:
    """The whole report, and whether the build is shippable."""
    lines = [
        f"app={appConfig.appName} {appConfig.appVersion}",
        f"platform={sys.platform}",
        f"frozen={appConfig.isFrozen}",
        f"bundleRoot={appConfig.bundleRoot}",
        f"resourcesDir={appConfig.resourcesDir}",
    ]
    passed = True
    for name, found, detail in resourceChecks():
        lines.append(f"{name}={'ok' if found else 'MISSING'}  {detail}")
        passed = passed and found
    for name, check in (("window", windowCheck), ("engines", engineCheck)):
        ok, detail = check()
        lines.append(f"{name}={'ok' if ok else 'FAILED'}  {detail}")
        passed = passed and ok
    lines.append(f"result={'ok' if passed else 'FAILED'}")
    return "\n".join(lines), passed


def runSelfTest(reportPath: str | None = None) -> int:
    text, passed = report()
    if reportPath:
        Path(reportPath).write_text(text, encoding="utf-8")
    print(text)
    return 0 if passed else 1
