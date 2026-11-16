"""Background thread for asking whether a published page is reachable.

A network probe can hang until its timeout, which must not happen on the
interface thread for something as small as a menu click. Help > User Manual
asks about the manual, Help > Legacy Fortran Sources about the sources.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QThread, Signal

from strandSlip.services.manualService import ManualService

logger = logging.getLogger(__name__)


class ManualWorker(QThread):
    """Reports whether a published page is reachable: the manual unless told otherwise."""

    # True when the online copy answered; False to use the local one.
    resolved = Signal(bool)

    def __init__(
        self,
        manualService: ManualService | None = None,
        parent: object | None = None,
        url: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.manualService = manualService or ManualService()
        self.url = url

    def run(self) -> None:
        self.resolved.emit(self.manualService.isOnlineCopyAvailable(self.url))
