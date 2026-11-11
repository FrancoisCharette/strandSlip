"""HARDSIN, CONTSIN and ZETASIN: the three models along a sinusoidal deflection.

All three open on the same menu (ENSN*): 1 sums the energy of every half lay
length from the origin to λ/4 and multiplies by four (THETAi = 90 deg), 2
solves the half lay length centred on λ/4 for the relative displacement
difference (THETAi = 0), 3 analyses the half lay length starting XTOUR turns
from the origin. Choice 1 ends after the first half lay length whose centre
is past λ/4 - 0.6 (a REAL*4 0.6).
"""

from __future__ import annotations

from masterRebuild.models.thesisInput import ThesisInput
from masterRebuild.services import thesisScreens as screens
from masterRebuild.services.complianceModel import dissipation, solveHalfPitch
from masterRebuild.services.complianceSystem import Problem, complianceCurve
from masterRebuild.services.macroSlipModels import (
    displacementRatio,
    hardySinusoid,
    macroDissipation,
    peakDemand,
)
from masterRebuild.services.thesisDeflections import HalfPitch, Sinusoid, pi
from masterRebuild.services.thesisProfiles import complianceProfile, macroSlipProfile
from masterRebuild.services.thesisPrograms import (
    ProgramRun,
    askProfile,
    complianceResult,
    continuitySolve,
    lastHalfPitchMargin,
    macroResult,
    raiseIfUnbracketed,
)
from masterRebuild.services.thesisSession import ThesisSession


def _menu(value: ThesisInput, session: ThesisSession, amplitudePrompt: str, compliance: bool):
    """ENSNHARD, ENSNCONT, ENSNZETA: the choice, Λ, Ā (and γ1); returns (choice, deflection)."""
    session.write(screens.menuTitle)
    session.write(screens.menu)
    choice = int(session.ask(screens.choicePrompt, int(value.choice)))
    theta = 0.0 if choice == 2 else pi / 2.0
    session.ask(screens.wavelengthPrompt, value.wavelength)
    session.ask(amplitudePrompt, value.amplitude)
    if not compliance and value.amplitude <= 1.0:
        raise session.waitFor(
            amplitudePrompt,
            f"With A/Ac = {value.amplitude:g} there is no macro-slip anywhere: the program "
            "refuses an amplitude of 1.0 or less and asks again.",
        )
    if compliance:
        session.ask(screens.gammaPromptSinusoid, value.compliance)
    return choice, Sinusoid(value.amplitude, value.wavelength, theta)


def _firstTurns(value: ThesisInput, choice: int, deflection: Sinusoid, session) -> float:
    """XTOUR before the first XTOUR=XTOUR+0.5D0."""
    turns = 0.0 - 0.5
    if choice == 2:
        turns = ((deflection.wavelength / 4.0) - 0.25) - 0.5
    if choice == 3:
        turns = float(session.ask(screens.turnsPrompt, value.turns))
        turns = turns - 0.5
    return turns


def _halfPitchCount(deflection: Sinusoid) -> int:
    return max(1, int(deflection.wavelength / 2.0))


def _noMacroSlip(session: ThesisSession, run: ProgramRun, half: HalfPitch, choice: int):
    """HARDSIN / CONTSIN without macro-slip: next half lay length, or a question."""
    session.write(screens.noMacroSlipSinusoid, half.start, half.end)
    session.pause(screens.pressEnter)
    if choice == 1:
        run.skipped.append((half.start, half.end))
        return None
    if choice == 3:
        return session.waitFor(
            screens.turnsPrompt,
            f"There is no macro-slip in the half lay length {half.start:g} to {half.end:g}: "
            "the program asks for another XTOUR.",
        )
    session.write(screens.menuTitle)
    session.write(screens.menu)
    return session.waitFor(
        screens.choicePrompt,
        "There is no macro-slip in the half lay length at λ/4: the program goes back to "
        "its menu. Try a larger amplitude.",
    )


def runMacroSinusoid(
    value: ThesisInput, session: ThesisSession, run: ProgramRun, continuity: bool
) -> None:
    """HARDSIN (`continuity` False) or CONTSIN."""
    if continuity:
        title, blank, unknowns = screens.continuityTitle, "//////", screens.continuityUnknowns
        amplitudePrompt = screens.amplitudePromptContinuity
    else:
        title, blank, unknowns = screens.hardyTitle, "////", screens.hardyUnknowns
        amplitudePrompt = screens.amplitudePrompt
    choice, deflection = _menu(value, session, amplitudePrompt, compliance=False)
    turns = _firstTurns(value, choice, deflection, session)
    energySum = 0.0
    while True:
        turns = turns + 0.5
        half = HalfPitch.starting(turns, deflection.theta)
        session.progress(len(run.halfPitches) + len(run.skipped), _halfPitchCount(deflection))
        peak, peakAt = peakDemand(deflection, half)
        if abs(peak) <= 1.0:
            waiting = _noMacroSlip(session, run, half, choice)
            if waiting is not None:
                raise waiting
            continue
        if continuity:
            solution = continuitySolve(deflection, half, session, 1.0e-9, bothBounds=True)
        else:
            solution = raiseIfUnbracketed(hardySinusoid(deflection, half, peakAt, session), half)
        ratio = displacementRatio(deflection, solution, peakAt, half.side) if choice == 2 else None
        energy = macroDissipation(deflection, solution, half.side, session)
        energySum = energySum + energy
        run.halfPitches.append(macroResult(half, solution, energy, ratio))
        header = (
            deflection.amplitude,
            deflection.wavelength,
            deflection.theta,
            half.start,
            half.end,
        )
        values = (solution.lowerBound, solution.upperBound, solution.slope, solution.offset)
        screens.sinusoidHalfPitchScreen(
            session, title, blank, unknowns, choice, header, (*values, energy, ratio or 0.0)
        )
        if choice == 2:
            return
        if choice == 3:
            if askProfile(session, screens.profilePromptSinusoid, value):
                run.profile = macroSlipProfile(deflection, solution, half, session)
            return
        session.pause(screens.pressEnter)
        if half.middle < deflection.wavelength / 4.0 - lastHalfPitchMargin:
            continue
        run.totalEnergy = 4.0 * energySum
        screens.sinusoidTotalScreen(
            session, title, (deflection.amplitude, deflection.wavelength, deflection.theta),
            run.totalEnergy,
        )  # fmt: skip
        return


def runHardSin(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    runMacroSinusoid(value, session, run, continuity=False)


def runContSin(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    runMacroSinusoid(value, session, run, continuity=True)


def runZetaSin(value: ThesisInput, session: ThesisSession, run: ProgramRun) -> None:
    curve = complianceCurve(2.0 / 3.0)  # COMP, called before the menu
    choice, deflection = _menu(value, session, screens.amplitudePrompt, compliance=True)
    compliance = deflection.compliance(value.compliance)
    turns = _firstTurns(value, choice, deflection, session)
    energySum = 0.0
    regions = 0
    while True:
        turns = turns + 0.5
        half = HalfPitch.starting(turns, deflection.theta)
        session.progress(len(run.halfPitches), _halfPitchCount(deflection))
        p = Problem(deflection, compliance, curve, half)
        solved = solveHalfPitch(p, session, sinusoid=True, startRegions=regions)
        u = solved.unknowns
        energy = dissipation(p, u, session)
        screens.writeEnergyFile(session, energy, u.regions)
        energySum = energySum + energy.total
        run.halfPitches.append(complianceResult(half, solved, energy))
        if choice in (2, 3):
            session.write(screens.complianceTitle)
            session.write(screens.sinusoidSubtitle)
            session.write(screens.solutionSinusoidCompliance)
        if choice == 1:
            session.write("//////")
        header = (deflection.amplitude, deflection.wavelength, value.compliance, deflection.theta)
        session.write(screens.complianceParameters, *header, half.start, half.end)
        session.write(screens.centralUnknowns)
        session.write(
            screens.complianceUnknowns, u.lowerBound, u.upperBound, u.centerBeta, u.centerEta
        )
        unknownsFile = (
            (screens.unknownsSinusoid, header),
            (u.regions, solved.printedPoints, half.start, half.end),
            curve,
            u,
        )
        if choice == 2:
            session.write(screens.otherUnknowns)
            session.write(screens.displacementRatioCompliance, solved.ratio)
            screens.writeUnknownsFile(session, *unknownsFile)
            return
        session.write(screens.halfPitchEnergyCompliance, energy.total)
        if choice == 1:
            session.write("////")
        if choice == 3:
            screens.writeUnknownsFile(session, *unknownsFile)
            session.write(screens.seeEnergyFile)
            session.write("/," + screens.otherUnknowns)
            if askProfile(session, screens.profilePromptCompliance, value):
                run.profile = complianceProfile(p, u, session)
            return
        session.pause(screens.pressEnter)
        if half.middle < deflection.wavelength / 4.0 - lastHalfPitchMargin:
            regions = u.regions - 1  # NPORTION=NPORTION-1: the next half lay length starts here
            continue
        run.totalEnergy = 4.0 * energySum
        session.write("///" + screens.complianceTitle.removeprefix("/"))
        session.write(screens.sinusoidSubtitle)
        session.write(screens.solutionTotal)
        session.write(screens.complianceTotalParameters, *header)
        session.write(screens.totalEnergy, run.totalEnergy)
        return
