"""The screen, keyboard and files of one run of a 1992 program.

The six thesis programs were interactive: they printed prompts, read answers
typed at the keyboard, paused, and wrote .DAT files. A run here is the same
dialogue with the answers given in advance: `ThesisInput` holds the values
the program asks for at the start, and `approximations` the ones it asks for
when an automatic approximation fails, consumed in the order it asks. When it
asks for something the run was not given, it stops (`ProgramWaits`) and the
screen so far is kept, ending with the question.

Records are kept as the programs wrote them, carriage-control column
included; `legacyOutputService.screenText` drops it for display, as the 1990
port does.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from strandSlip.services.analysisErrors import ProgressHook
from strandSlip.services.fortranFormat import formatRecord, keepsLineOpen


class ProgramWaits(Exception):
    """The program asks a question the run's inputs do not answer."""

    def __init__(self, question: str) -> None:
        super().__init__(question)
        self.question = question


def typedText(value: float | int) -> str:
    """An answer as someone would have typed it: the shortest text that reads back the same."""
    if isinstance(value, int):
        return str(value)
    text = repr(float(value))
    return text[:-2] if text.endswith(".0") else text


class ThesisSession:
    def __init__(self, approximations: Iterable[float] = (), hook: ProgressHook | None = None):
        self.records: list[str] = []
        self.openLine: str | None = None  # a prompt written with a backslash, awaiting its answer
        self.files: dict[str, list[str]] = {}
        self.approximations = deque(approximations)
        self.approximationsUsed: list[float] = []
        self.hook = hook

    # -- screen and keyboard --------------------------------------------------

    def write(self, spec: str, *values: float | int) -> None:
        lines = formatRecord(spec, values).split("\n")
        if self.openLine is not None:
            lines[0] = self.openLine + lines[0]
            self.openLine = None
        if keepsLineOpen(spec):
            self.openLine = lines.pop()
        self.records.extend(lines)

    def typed(self, value: float | int) -> None:
        """READ(*,*): the answer appears after the prompt, then the line ends."""
        text = typedText(value)
        if self.openLine is not None:
            self.records.append(self.openLine + text)
            self.openLine = None
        else:
            self.records.append(text)

    def ask(self, prompt: str, value: float | int) -> float | int:
        """A prompt and the answer the run provides for it."""
        self.write(prompt)
        self.typed(value)
        return value

    def askApproximation(self, prompt: str, question: str) -> float:
        """A prompt answered from `approximations`, or the end of the run."""
        self.write(prompt)
        if not self.approximations:
            raise ProgramWaits(question)
        value = self.approximations.popleft()
        self.approximationsUsed.append(value)
        self.typed(value)
        return value

    def waitFor(self, prompt: str, question: str) -> ProgramWaits:
        """The program asks again for a value it was given (it refused it): stop there."""
        self.write(prompt)
        return ProgramWaits(question)

    def pause(self, message: str) -> None:
        self.closeLine()
        self.records.append(message)

    def closeLine(self) -> None:
        if self.openLine is not None:
            self.records.append(self.openLine)
            self.openLine = None

    # -- files -----------------------------------------------------------------

    def openFile(self, name: str) -> None:
        """OPEN ... STATUS='UNKNOWN' followed by writes: the file starts again."""
        self.files[name] = []

    def writeFile(self, name: str, spec: str, *values: float | int) -> None:
        self.files[name].extend(formatRecord(spec, values).split("\n"))

    # -- progress ------------------------------------------------------------

    def progress(self, done: int, total: int) -> None:
        if self.hook is not None:
            self.hook.advance(done, total)
