"""Tests for the check that decides whether a build is shippable.

This one gates a release, so it has to fail when something is genuinely
missing. A self-test that passes unconditionally is worse than none: it turns
a broken build into a signed-off one.
"""

from __future__ import annotations

from strandSlip import appConfig, selftest


def failures() -> list[str]:
    return [name for name, found, _ in selftest.resourceChecks() if not found]


def testEveryBundledThingIsChecked(qapp) -> None:
    names = [name for name, _, _ in selftest.resourceChecks()]

    assert names == ["applicationIcon", "manual", "legacySources"]


def testACheckoutPassesItsOwnCheck(qapp) -> None:
    assert failures() == []


def testAMissingIconIsCaught(qapp, monkeypatch, tmp_path) -> None:
    """The failure this exists for: packaging dropped the icon."""
    monkeypatch.setattr(appConfig, "iconFile", tmp_path / "gone.ico")

    assert failures() == ["applicationIcon"]


def testAMissingManualIsCaught(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(appConfig, "manualPath", tmp_path / "gone.md")

    assert failures() == ["manual"]


def testMissingLegacySourcesAreCaught(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(appConfig, "legacySourcesDir", tmp_path / "gone")

    assert failures() == ["legacySources"]


def testTheWindowIsBuiltWithItsTabsAndIcon(qapp, monkeypatch) -> None:
    monkeypatch.setattr(appConfig, "settingsFile", appConfig.settingsFile)  # restored after
    ok, detail = selftest.windowCheck()

    assert ok, detail
    assert detail == appConfig.windowTitle


def testTheWindowCheckNeverTouchesTheRealSettings(qapp, monkeypatch, tmp_path) -> None:
    """It points the app at a scratch folder before building anything."""
    realSettings = tmp_path / "real" / "settings.ini"
    monkeypatch.setattr(appConfig, "settingsFile", realSettings)

    ok, _detail = selftest.windowCheck()

    assert ok
    assert not realSettings.exists()
    assert appConfig.settingsFile != realSettings


def testTheEnginesGiveTheReportsNumbers() -> None:
    ok, detail = selftest.engineCheck()

    assert ok, detail
    assert "XB1 = 0.14758" in detail


def testTheReportNamesTheVersionAndPasses(qapp, monkeypatch) -> None:
    monkeypatch.setattr(appConfig, "settingsFile", appConfig.settingsFile)
    text, passed = selftest.report()

    assert passed, text
    assert f"app={appConfig.appName} {appConfig.appVersion}" in text
    assert "result=ok" in text
    assert "MISSING" not in text


def testAFailedCheckShowsUpInTheReportAndTheExitCode(qapp, monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(appConfig, "settingsFile", appConfig.settingsFile)
    monkeypatch.setattr(appConfig, "iconFile", tmp_path / "gone.ico")

    text, passed = selftest.report()

    assert not passed
    assert "applicationIcon=MISSING" in text
    assert "result=FAILED" in text
    assert selftest.runSelfTest(str(tmp_path / "report.txt")) == 1


def testTheReportIsWrittenWhereItIsAsked(qapp, monkeypatch, tmp_path) -> None:
    """A windowed build has no console, so the file is the whole output."""
    monkeypatch.setattr(appConfig, "settingsFile", appConfig.settingsFile)
    target = tmp_path / "selftest.txt"

    code = selftest.runSelfTest(str(target))

    assert code == 0
    assert "result=ok" in target.read_text(encoding="utf-8")


def testFromSourceTheBundleIsTheCheckout() -> None:
    assert not appConfig.isFrozen
    assert appConfig.bundleRoot == appConfig.projectRoot
    assert appConfig.manualPath == appConfig.projectRoot / "docs" / "manual" / "README.md"
    assert appConfig.legacySourcesDir == appConfig.projectRoot / "legacy"
