"""Errors and progress reporting shared by the analysis services."""

from __future__ import annotations

from collections.abc import Callable


class AnalysisError(Exception):
    """A run that cannot produce results; the message says what to change."""


class InputError(AnalysisError):
    """ENTRE.DAT values a program cannot run on."""

    def __init__(self, issues: list[str]) -> None:
        self.issues = list(issues)
        super().__init__("\n".join(self.issues))


class AnalysisCancelled(Exception):
    """The user stopped the run."""


class ProgressHook:
    """Lets a long run report how far it is and notice a request to stop.

    Services call `advance` between chunks of work; it raises
    AnalysisCancelled once `cancel` has been called, so a run stops at the
    next chunk boundary rather than mid-array.
    """

    def __init__(self, onProgress: Callable[[int], None] | None = None) -> None:
        self.onProgress = onProgress
        self.cancelled = False
        self.lastPercent = -1

    def cancel(self) -> None:
        self.cancelled = True

    def advance(self, done: int, total: int) -> None:
        if self.cancelled:
            raise AnalysisCancelled()
        percent = 100 if total <= 0 else int(100 * done / total)
        if percent != self.lastPercent:
            self.lastPercent = percent  # read by AnalysisWorker.percent
            if self.onProgress is not None:
                self.onProgress(percent)


def advance(hook: ProgressHook | None, done: int, total: int) -> None:
    if hook is not None:
        hook.advance(done, total)
