"""The version is written in several places; these keep them saying the same thing.

appConfig.appVersion is the one the app reports, the builds are named after
and the release workflow checks the tag against. The others are copies, and a
copy left behind is how an About box and an installer end up naming two
different versions of one release.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import strandSlip
from strandSlip import appConfig

projectRoot = Path(__file__).resolve().parents[1]


def testTheProjectFileAgrees() -> None:
    project = tomllib.loads((projectRoot / "pyproject.toml").read_text(encoding="utf-8"))

    assert project["project"]["version"] == appConfig.appVersion


def testThePackageAgrees() -> None:
    assert strandSlip.__version__ == appConfig.appVersion
