"""The worker thread that keeps runs off the interface thread."""

from __future__ import annotations

from masterRebuild.models.legacyProgram import SINUS
from masterRebuild.models.strandPresets import reportStrandSinusoid
from masterRebuild.services.analysisErrors import AnalysisCancelled, InputError
from masterRebuild.services.analysisWorker import AnalysisWorker
from masterRebuild.services.stiffnessService import runStiffness


def testSuccessCarriesTheResult(qtbot) -> None:
    worker = AnalysisWorker(lambda hook: runStiffness(reportStrandSinusoid.input, SINUS, hook))
    with qtbot.waitSignal(worker.succeeded, timeout=10000) as blocker:
        worker.start()
    worker.wait(5000)
    assert blocker.args[0].program is SINUS


def testAnInputErrorBecomesAMessage(qtbot) -> None:
    def job(hook):
        raise InputError(["Wavelength (WL) must be positive."])

    worker = AnalysisWorker(job)
    with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
        worker.start()
    worker.wait(5000)
    assert blocker.args == ["Wavelength (WL) must be positive."]


def testAnUnexpectedErrorIsReportedNotSwallowed(qtbot) -> None:
    def job(hook):
        raise ZeroDivisionError("float division by zero")

    worker = AnalysisWorker(job)
    with qtbot.waitSignal(worker.failed, timeout=5000) as blocker:
        worker.start()
    worker.wait(5000)
    assert "ZeroDivisionError" in blocker.args[0]


def testCancelling(qtbot) -> None:
    def job(hook):
        raise AnalysisCancelled()

    worker = AnalysisWorker(job)
    with qtbot.waitSignal(worker.cancelled, timeout=5000):
        worker.start()
    worker.wait(5000)
