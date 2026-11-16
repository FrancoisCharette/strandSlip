"""Application configuration — paths, defaults, and metadata."""

from __future__ import annotations

import os
from pathlib import Path

appName = "Strand Slip"
appVersion = "0.1.0"
organizationName = "Charette-AI-Group"

# Help > About contents
editorName = "Francois Charette, PhD"
aiAgentName = "Claude - Opus 5"
copyrightHolder = "Charette AI Group, LLC"
# createNewApp rewrites the package name throughout, so this follows the repo
# it actually creates without anyone having to remember to edit it.
repoUrl = "https://github.com/FrancoisCharette/strandSlip"

# Donate button, shared across the Charette AI Group applications so they look
# like they come from the same place.
donateUrl = "https://www.paypal.com/donate/?hosted_button_id=FEM4WLD7LHY36"
donateColour = "#f0b232"
donateTextColour = "#1f1e1b"
donatePressedColour = "#d9991f"

projectRoot = Path(__file__).resolve().parents[2]
resourcesDir = Path(__file__).resolve().parent / "resources"
# Drawn by tools/makeIcons.py. The app runs without one if it is missing.
iconFile = resourcesDir / "strandSlip.ico"
# Windows groups taskbar buttons by this ID. Without one, a window started by
# pythonw.exe is filed under Python and shows Python's icon, not this app's.
appUserModelId = f"{organizationName}.StrandSlip"

# Help > User Manual. The copy in the checkout is what a new app has, and it is
# enough: the menu item works from the first run rather than being a promise.
manualPath = projectRoot / "docs" / "manual" / "README.md"
# The published copy, preferred: GitHub renders the screenshots that a local
# .md opened in an editor does not. The local copy is the offline fallback.
# Empty would keep it local with no network request at all.
manualUrl = f"{repoUrl}/blob/main/docs/manual/README.md"
# How long to wait for a published page before falling back to the local copy.
manualTimeoutSeconds = 3.0

# The seven 1990 Fortran programs this app revives, kept as they were found
# (legacy/programmes), and the 1992 thesis programs recovered from the printed
# manual (legacy/manuel1992). Help > Legacy Fortran Sources opens both: on
# GitHub, which shows the READMEs beside the listings, or this folder offline.
legacySourcesDir = projectRoot / "legacy"
legacySourcesUrl = f"{repoUrl}/tree/main/legacy"

appDataDir = Path(os.environ.get("APPDATA", str(Path.home()))) / appName
settingsFile = appDataDir / "settings.ini"
windowTitle = f"{appName} — The 1990 and 1992 Strand Programs"
defaultWindowWidth = 1320
defaultWindowHeight = 860
