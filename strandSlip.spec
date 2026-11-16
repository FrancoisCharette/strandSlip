# -*- mode: python ; coding: utf-8 -*-
r"""PyInstaller build of the application, as Wager Book builds its own. Driven by tools\buildExe.py.

A one-folder build rather than one-file, on purpose:

  - It starts immediately. A one-file build unpacks the whole Qt runtime,
    numpy and matplotlib to a temporary folder on every launch, which for a
    bundle this size is a wait before anything appears, every single time.
  - The installer wants a folder anyway, and an uninstaller that removes a
    folder is easier to reason about than one chasing a self-extractor.

What ships is the read-only half: the package and its icon, the manual and
the legacy Fortran sources that Help falls back to when there is no network.
Everything the app writes - its settings - lives under APPDATA and is created
on first run.
"""

import sys
from pathlib import Path

projectRoot = Path(SPECPATH)

# The one place the version comes from, here as everywhere else. appConfig
# imports nothing but the standard library, so reading it costs nothing and
# a bundle can never claim a version the application does not report.
sys.path.insert(0, str(projectRoot / "src"))
sys.path.insert(0, str(projectRoot / "tools"))
from strandSlip import appConfig  # noqa: E402
from windowsVersionInfo import versionInfo  # noqa: E402

# The version, company and copyright that Explorer's Properties > Details
# shows, built from appConfig so the file cannot disagree with the About box.
windowsVersion = versionInfo(appConfig)
appIcon = str(projectRoot / "src" / "strandSlip" / "resources" / "strandSlip.ico")

# PyInstaller does not collect package data on its own, and appConfig looks
# for the icon inside the package. Without this the executable wears the icon
# while the running window does not.
datas = [
    (str(projectRoot / "src" / "strandSlip" / "resources"), "strandSlip/resources"),
    (str(projectRoot / "docs" / "manual"), "docs/manual"),
    (str(projectRoot / "legacy"), "legacy"),
]

# Development-only, or simply never reached, and large enough to be worth
# refusing. The plots are matplotlib on QtAgg; nothing plays a video, renders
# a web page or talks QtNetwork (the manual check is urllib's). QtSvg stays:
# matplotlib's toolbar draws its icons with it.
excludes = [
    "pytest",
    "_pytest",
    "pytest_qt",
    "ruff",
    "tkinter",
    "PyInstaller",
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends._backend_tk",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtCharts",
    "PySide6.Qt3DCore",
    "PySide6.QtDataVisualization",
    "PySide6.QtMultimedia",
    "PySide6.QtQuick",
    "PySide6.QtQml",
    "PySide6.QtNetwork",
    "PySide6.QtSql",
    "PySide6.QtTest",
]

analysis = Analysis(
    [str(projectRoot / "src" / "strandSlip" / "main.py")],
    pathex=[str(projectRoot / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={"matplotlib": {"backends": ["QtAgg"]}},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

executable = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=appConfig.executableName,
    icon=appIcon,
    version=windowsVersion,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # No console: this is a windowed app, and a console behind a GUI is a
    # thing users close by accident, taking the app with it. --selftest
    # writes to a file for the same reason.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

collected = COLLECT(
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=appConfig.executableName,
)
