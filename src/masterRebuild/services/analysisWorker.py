"""Runs one analysis off the interface thread.

A fine slip search (NSINUS) or a long span can take seconds; the window
stays responsive and the run can be stopped between chunks.

Progress is read, not signalled: the job records how far it is on its
ProgressHook and the view polls `percent`. A hook holding this thread's own
bound `progressed.emit` made a reference cycle that aborted the process when
the finished thread was deleted (PySide6 6.12, Python 3.14); polling has no
such cycle and costs one timer.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QThread, Signal

from masterRebuild.services.analysisErrors import AnalysisCancelled, AnalysisError, ProgressHook

logger = logging.getLogger(__name__)


class AnalysisWorker(QThread):
    """Calls `job(hook)` on a worker thread and reports how it went."""

    succeeded = Signal(object)  # the result object
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, job: Callable[[ProgressHook], object], parent: object | None = None) -> None:
        super().__init__(parent)
        self.job: Callable[[ProgressHook], object] | None = job
        self.hook = ProgressHook()

    @property
    def percent(self) -> int:
        return max(0, self.hook.lastPercent)

    def cancel(self) -> None:
        self.hook.cancel()

    def run(self) -> None:
        job, self.job = self.job, None
        if job is None:
            return
        try:
            result = job(self.hook)
        except AnalysisCancelled:
            self.cancelled.emit()
        except AnalysisError as error:
            self.failed.emit(str(error))
        except OSError as error:
            where = f" ({error.filename})" if error.filename else ""
            self.failed.emit(f"{error.strerror or error}{where}")
        except Exception as error:  # an escaping exception would kill the thread silently
            logger.exception("Analysis crashed")
            self.failed.emit(f"The run stopped on an unexpected error: {error!r}")
        else:
            self.succeeded.emit(result)
