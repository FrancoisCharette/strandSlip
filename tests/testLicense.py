"""The licence: one file, named the same way wherever it is shown."""

from __future__ import annotations

import tomllib
from pathlib import Path

from strandSlip import appConfig

projectRoot = Path(__file__).resolve().parents[1]


def testTheLicenceIsMitInTheAboutBoxsName() -> None:
    text = (projectRoot / "LICENSE").read_text(encoding="utf-8")

    assert text.startswith("MIT License")
    assert f"Copyright (c) 2026 {appConfig.copyrightHolder}" in text


def testTheProjectAndTheInstallerShowIt() -> None:
    project = tomllib.loads((projectRoot / "pyproject.toml").read_text(encoding="utf-8"))
    script = (projectRoot / "installer" / "strandSlip.iss").read_text(encoding="utf-8")

    assert project["project"]["license"] == {"text": "MIT"}
    assert r"LicenseFile=..\LICENSE" in script
