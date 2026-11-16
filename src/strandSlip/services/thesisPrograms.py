"""The six 1992 programs, step for step: what they ask, compute, print and write.

Each `run...` function follows its main program and the input and output
routines it calls (ENT*/ENSN*, ECR*/ECSN*), writing to a ThesisSession and
collecting the results. Where the program would ask again for a value it
refused, the run stops there with `ProgramWaits`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from strandSlip.models.thesisInput import ThesisInput
from strandSlip.models.thesisResults import HalfPitchResult, SlipProfile
from strandSlip.services import thesisScreens as screens
from strandSlip.services.analysisErrors import AnalysisError
from strandSlip.services.complianceModel import dissipation, solveHalfPitch
from strandSlip.services.complianceSystem import Problem, complianceCurve
from strandSlip.services.macroSlipModels import (
    MacroSlipSolution,
    continuityGuess,
    continuityNewton,
    displacementRatio,
    hardyRadius,
    macroDissipation,
)
from strandSlip.services.thesisDeflections import ConstantRadius, HalfPitch, pi
from strandSlip.services.thesisNumerics import real4
from strandSlip.services.thesisProfiles import complianceProfile, macroSlipProfile
from strandSlip.services.thesisSession import ThesisSession

continuityMinimumRadius = real4(0.65)  # ENTCONT: IF(RHOB.LT.0.65) GOTO 500
lastHalfPitchMargin = real4(0.6)  # IF(XM.LT.WLBAR/4.0D0-.6...): a REAL*4 constant


@dataclass
class ProgramRun:
    """What a program computed, gathered as it goes."""

    halfPitches: list[HalfPitchResult] = field(default_factory=list)
    skipped: list[tuple[float, float]] = field(default_factory=list)
    totalEnergy: float | None = None
    profile: SlipProfile | None = None


def macroResult(half: HalfPitch, s: MacroSlipSolution, energy: float, ratio) -> HalfPitchResult:
    return HalfPitchResult(
        half.start, half.end, half.side, s.lowerBound, s.upperBound, s.slope, s.offset,
        energy, ratio,
    )  # fmt: skip


def askProfile(session: ThesisSession, prompt: str, value: ThesisInput) -> bool:
    session.ask(prompt, 0 if value.profile else 1)
    return value.profile


def noMacroSlipRadius(session: ThesisSession, half: HalfPitch, prompt: str, radius: float):
    session.write(screens.noMacroSlipRadius, half.start, half.end)
    session.pause(screens.pressEnter)
    return session.waitFor(
        prompt,
        f"With ρ/ρc = {radius:g} the friction needed never exceeds the limit: no macro-slip "
        "in this half lay length, and the program asks for another radius of curvature "
        "(below 1.0).",
    )


# -- constant radius of curvature ----------------------------------------------------


def runHardRhob(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    theta = pi / 2.0
    deflection = ConstantRadius(value.radius, theta)
    half = HalfPitch.starting(0.0, theta)
    session.ask(screens.radiusPrompt, value.radius)
    if half.side * deflection.frictionMargin(half.middle, half.side) <= 0.0:
        raise noMacroSlipRadius(session, half, screens.radiusPrompt, value.radius)
    solution = hardyRadius(deflection, half, session)
    ratio = displacementRatio(deflection, solution, half.middle, half.side)
    energy = macroDissipation(deflection, solution, half.side, session)
    run.halfPitches.append(macroResult(half, solution, energy, ratio))
    header = (value.radius, theta, half.start, half.end)
    values = (solution.lowerBound, solution.upperBound, solution.slope, solution.offset)
    screens.radiusResultScreen(
        session, screens.hardyTitle, screens.hardyUnknowns, (*values, energy, ratio), header
    )
    if askProfile(session, screens.profilePrompt, value):
        run.profile = macroSlipProfile(deflection, solution, half, session)


def continuitySolve(deflection, half, session, accuracy, bothBounds: bool):
    """CONTRHOB / CONTSIN from the approximations to NEWT, with the keyboard's help."""
    guess = continuityGuess(deflection, half, session, accuracy)
    question = (
        f"The approximation of the macro-slip bounds failed for the half lay length "
        f"{half.start:g} to {half.end:g}, or Newton did not converge from it. The program "
        f"asks for an approximation of XB1{' and then of XB2' if bothBounds else ''}."
    )
    while True:
        if guess is None:
            session.write(screens.boundsLine, half.start, half.end)
            lower = session.askApproximation(screens.lowerBoundPrompt, question)
            if bothBounds:
                upper = session.askApproximation(screens.upperBoundPrompt, question)
            else:
                upper = half.end - lower
            guess = (lower, upper)
        solution = continuityNewton(deflection, half, *guess, session)
        if solution is not None:
            return solution
        guess = None


def runContRhob(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    theta = pi / 2.0
    deflection = ConstantRadius(value.radius, theta)
    half = HalfPitch.starting(0.0, theta)
    prompt = screens.radiusPromptContinuity
    session.ask(prompt, value.radius)
    if value.radius < continuityMinimumRadius:
        raise session.waitFor(
            prompt,
            "CONTRHOB refuses a radius of curvature below 0.65 (the macro-slip region "
            "would take the whole half lay length) and asks again.",
        )
    if half.side * deflection.frictionMargin(half.middle, half.side) <= 0.0:
        raise noMacroSlipRadius(session, half, prompt, value.radius)
    solution = continuitySolve(deflection, half, session, 1e-10, bothBounds=False)
    ratio = displacementRatio(deflection, solution, half.middle, half.side)
    energy = macroDissipation(deflection, solution, half.side, session)
    run.halfPitches.append(macroResult(half, solution, energy, ratio))
    header = (value.radius, theta, half.start, half.end)
    values = (solution.lowerBound, solution.upperBound, solution.slope, solution.offset)
    screens.radiusResultScreen(
        session,
        screens.continuityTitle,
        screens.continuityUnknowns,
        (*values, energy, ratio),
        header,
    )
    if askProfile(session, screens.profilePrompt, value):
        run.profile = macroSlipProfile(deflection, solution, half, session)


def complianceResult(half, solved, energy) -> HalfPitchResult:
    u = solved.unknowns
    return HalfPitchResult(
        half.start, half.end, half.side, u.lowerBound, u.upperBound, u.centerBeta, u.centerEta,
        energy.total, solved.ratio, u.regions, solved.centerDifference, energy.regions,
        energy.macroRegion, energy.microInMacro,
    )  # fmt: skip


def runZetaRhob(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    theta = pi / 2.0
    deflection = ConstantRadius(value.radius, theta)
    half = HalfPitch.starting(0.0, theta)
    session.ask(screens.gammaPromptRadius, value.compliance)
    session.ask(screens.radiusPromptCompliance, value.radius)
    curve = complianceCurve(2.0 / 3.0)
    p = Problem(deflection, deflection.compliance(value.compliance), curve, half)
    solved = solveHalfPitch(p, session, sinusoid=False)
    u = solved.unknowns
    energy = dissipation(p, u, session)
    screens.writeEnergyFile(session, energy, u.regions)
    run.halfPitches.append(complianceResult(half, solved, energy))
    session.write(screens.complianceTitle)
    session.write(screens.radiusSubtitle)
    session.write(screens.solutionRadius)
    session.write(
        screens.radiusParametersCompliance, value.radius, value.compliance, theta,
        half.start, half.end,
    )  # fmt: skip
    screens.writeUnknownsFile(
        session,
        (screens.unknownsRadius, (value.compliance, value.radius, theta)),
        (u.regions, solved.printedPoints, half.start, half.end),
        curve,
        u,
    )
    session.write(screens.resultsHeadingCompliance)
    session.write(screens.radiusResultsCompliance, energy.total, solved.ratio)
    if askProfile(session, screens.profilePromptCompliance, value):
        run.profile = complianceProfile(p, u, session)


def raiseIfUnbracketed(solution, half: HalfPitch) -> MacroSlipSolution:
    if solution is None:
        raise AnalysisError(
            f"False position found no sign change for a macro-slip bound in the half lay "
            f"length {half.start:g} to {half.end:g}. HARDSIN went on with the undefined value "
            "RTFLSP returned; the port stops instead."
        )
    return solution
