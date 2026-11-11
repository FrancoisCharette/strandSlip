"""HARDSIN and CONTSIN with their subroutines, line by line (manual pages 39, 42, 63-66,
69-70). The labels 800 (back to the menu), 700 (ask XTOUR) and 900 (next half-pitch)
become a `label` the loop dispatches on.
"""

from __future__ import annotations

import math
from functools import partial

from legacyReference.literalThesisFunctions import DEPH, DMACRO, bindSinus
from legacyReference.literalThesisMachine import Machine, real4
from legacyReference.literalThesisNumerics import GOLDEN, QROMB, RTFLSP
from legacyReference.literalThesisRadius import NEWT, SORTIE

MENU = (
    "////,6X,'1. La dissipation d énergie d un fil sur',' toute la longueur',/,8X,"
    "' d onde (pour THETAi=90 deg).',//,6X,'2. Le rapport relatif de différence maximale de'"
    ",/,9X,'déplacement (pour THETAi=0 deg).',//,6X,"
    "'3. Analyser un demi-pas en particulier (pour THETAi=90 deg).'"
)
NO_MACRO_SLIP = "//,1X,'Pas de macro-glissement dans la demi pas ','XINF=',F5.2,1X,'a XSUP=',F5.2"
AMPLITUDE_LINE = (
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'et un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad. et',/,1X,'pour le demi-pas XINF =',F5.2,"
    "' à XSUP =',F5.2"
)
TOTAL_LINE = (
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'et un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'avec la position initiale THETAi = ',F7.5,' rad.',/////"
)
TOTAL_ENERGY = (
    "3X,'L énergie dissipée adimensionnelle totale',' par ce fil',/,"
    "3X,'tout le long de la longueur d onde = ',E14.8,//"
)
ASK_PROFILE = (
    "////,3X,'Désirez-vous faire calculer le déplacement,',' la déformation et le rapport',/,"
    "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
)


def menuAndWave(M: Machine, amplitudePrompt: str) -> int:
    """ENSNHARD and ENSNCONT (pages 70, 69): the menu, then WLBAR and ABAR."""
    UN = 1.0
    M.PI = math.acos(-UN)
    while True:  # 110
        M.write("/////////,3X,'Ce programme peut déterminer:'")
        M.write(MENU)
        M.write("///,9X,'Entrez votre choix:',\\")  # 100
        ICHOIX = M.readInteger("ICHOIX")
        if not (ICHOIX < 1 or ICHOIX > 3):
            break
    M.THETA = M.PI / 2.0
    if ICHOIX == 2:
        M.THETA = 0.0
    M.write("/,9X,'Entrez un nombre pair de pas par longueur',' d onde:',\\")  # 120
    M.WLBAR = M.readReal("WLBAR")
    while True:  # 130
        M.write(amplitudePrompt)
        M.ABAR = M.readReal("ABAR")
        if not M.ABAR <= 1.0:
            break
    M.PP = M.WLBAR + 1.0
    M.PN = M.WLBAR - 1.0
    M.PPA = M.PP / M.WLBAR
    M.PPB = M.PN / M.WLBAR
    M.PP1 = 2.0 * M.PI * M.PPA
    M.PN1 = 2.0 * M.PI * M.PPB
    return ICHOIX


def ENSNHARD(M: Machine) -> int:
    return menuAndWave(M, "/,9X,'Entrez l amplitude adimensionnelle:',\\")


def ENSNCONT(M: Machine) -> int:
    return menuAndWave(
        M, "/,9X,'Entrez l amplitude adimensionnelle',/,9X,'(Valeurs admissibles 1.0<=>1.5):',\\"
    )


def screen(M, title, firstBlank, letters, ICHOIX, XB1, XB2, XI, PSI, DSP, DSPTOTAL, RDEP):
    """ECSNHARD and ECSNCONT (pages 65, 63); they differ in the title and one blank run."""
    if DSPTOTAL == 0.0:
        if ICHOIX == 2 or ICHOIX == 3:
            M.write(title)
            M.write("24X,'pour la flèche sinusoidale'")
            M.write("/,26X,'****** SOLUTION ******',//")
        if ICHOIX == 1 and DSPTOTAL == 0.0:
            M.write(firstBlank)
        M.write(AMPLITUDE_LINE, M.ABAR, M.WLBAR, M.THETA, M.XINF, M.XSUP)
        M.write("/,1X,'Les 4 inconnues sont:',/")
        M.write(
            f"3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'{letters[0]}=',D14.8,2X,'{letters[1]}=',D14.8",
            XB1,
            XB2,
            XI,
            PSI,
        )
        if ICHOIX == 2:
            M.write(
                "//, 1X,'et le rapport relatif de différence',' maximale de déplacement =',E14.8,//",
                RDEP,
            )
            return 4
        M.write("/,3X,'Energie dissipée dans le demi-pas =',E14.8,/", DSP)
        if ICHOIX == 1 and DSPTOTAL == 0.0:
            M.write("///")
        if ICHOIX == 3:
            M.write(ASK_PROFILE)
            ISORTIE = M.readInteger("ISORTIE")
            if ISORTIE < 0.5:
                SORTIE(M, XB1, XB2, XI, PSI)
            ICHOIX = 4
    if DSPTOTAL != 0.0:  # 800
        M.write("///" + title.lstrip("/"))
        M.write("24X,'pour la flèche sinusoidale'")
        M.write("//,26X,'****** SOLUTION ******',///")
        M.write(TOTAL_LINE, M.ABAR, M.WLBAR, M.THETA)
        M.write(TOTAL_ENERGY, DSPTOTAL)
    return ICHOIX


def ECSNHARD(M, ICHOIX, XB1, XB2, XIH, PSIH, DSP, DSPTOTAL, RDEP):
    return screen(
        M, "/,29X,'MODELE DE HARDY'", "////", ("XIH", "PSIH"),
        ICHOIX, XB1, XB2, XIH, PSIH, DSP, DSPTOTAL, RDEP,
    )  # fmt: skip


def ECSNCONT(M, ICHOIX, XB1, XB2, XIC, PSIC, DSP, DSPTOTAL, RDEP):
    return screen(
        M, "/,18X,'MODELE AVEC CONTINUITE DE DEFORMATION'", "//////", ("XIC", "PSIC"),
        ICHOIX, XB1, XB2, XIC, PSIC, DSP, DSPTOTAL, RDEP,
    )  # fmt: skip


def halfPitchStart(M: Machine, XTOUR: float) -> None:
    """Label 900 onwards: place the half-pitch and read its side of the neutral plane."""
    M.XINF = XTOUR
    M.XSUP = M.XINF + 0.5
    M.XM = (M.XINF + M.XSUP) / 2.0
    VCOTE = math.cos(2.0 * M.PI * M.XM + M.THETA)
    M.ICOTE = -1
    if VCOTE > 0.0:
        M.ICOTE = 1


def HARDSIN(answers: dict[str, list[str]]) -> Machine:  # page 42
    M = Machine(answers)
    bindSinus(M)
    XACC = 1.0e-9
    XTOL = 1.0e-6
    DUM0 = DUM1 = 0.0
    RDEP = 0.0
    DSPTOTAL = 0.0
    label = 800
    while True:
        if label == 800:
            DSPTMP = 0.0
            ICHOIX = ENSNHARD(M)
            XTOUR = 0.0 - 0.5
            if ICHOIX == 2:
                XTOUR = ((M.WLBAR / 4.0) - 0.25) - 0.5
            label = 700
        if label == 700:
            if ICHOIX == 3:
                M.write("/,9X,'Nombre de tour de l origine (XTOUR) :',\\")
                XTOUR = M.readReal("XTOUR")
                XTOUR = XTOUR - 0.5
        XTOUR = XTOUR + 0.5  # 900
        halfPitchStart(M, XTOUR)
        FRCMIN, XMIN = GOLDEN(M, M.XINF, M.XM, M.XSUP, M.VMIN, XTOL)
        if abs(FRCMIN) <= 1.0:
            M.write(NO_MACRO_SLIP, M.XINF, M.XSUP)
            M.pause("Pressez ENTER pour continuer")
            label = 900 if ICHOIX == 1 else 700 if ICHOIX == 3 else 800
            continue
        XB1 = RTFLSP(M, M.FRICTION, M.XINF, XMIN, XACC)
        XB2 = RTFLSP(M, M.FRICTION, XMIN, M.XSUP, XACC)
        PSIH = M.DEPAME(XB1)
        XIH = (M.DEPAME(XB2) - M.DEPAME(XB1)) / (XB2 - XB1) - M.ICOTE * M.PI * (XB2 - XB1)
        if ICHOIX == 2:
            RDEP = (M.DEPAME(XMIN) - DEPH(M, XMIN, XB1, XIH, PSIH)) / M.DEPAME(XMIN)
        DSP = QROMB(M, DUM0, DUM1, XB1, XIH, PSIH, partial(DMACRO, M), XB1, XB2)
        DSPTMP = DSPTMP + DSP
        ICHOIX = ECSNHARD(M, ICHOIX, XB1, XB2, XIH, PSIH, DSP, DSPTOTAL, RDEP)
        if ICHOIX == 4:
            return M
        M.pause("Pressez ENTER pour continuer")
        if M.XM < M.WLBAR / 4.0 - real4(0.6) and ICHOIX == 1:
            label = 900
            continue
        DSPTOTAL = 4.0 * DSPTMP
        ECSNHARD(M, ICHOIX, XB1, XB2, XIH, PSIH, DSP, DSPTOTAL, RDEP)
        return M


def CONTSIN(answers: dict[str, list[str]]) -> Machine:  # page 39
    M = Machine(answers)
    bindSinus(M)
    XACC = 1.0e-9
    XTOL = 1.0e-6
    DUM0 = DUM1 = 0.0
    RDEP = 0.0
    XB2 = 0.0
    DSPTOTAL = 0.0
    label = 800
    while True:
        if label == 800:
            DSPTMP = 0.0
            ICHOIX = ENSNCONT(M)
            XTOUR = 0.0 - 0.5
            if ICHOIX == 2:
                XTOUR = ((M.WLBAR / 4.0) - 0.25) - 0.5
            label = 700
        if label == 700:
            if ICHOIX == 3:
                M.write("/,9X,'Nombre de tour de l origine (XTOUR) :',\\")
                XTOUR = M.readReal("XTOUR")
                XTOUR = XTOUR - 0.5
        XTOUR = XTOUR + 0.5  # 900
        halfPitchStart(M, XTOUR)
        FRCMIN, XMIN = GOLDEN(M, M.XINF, M.XM, M.XSUP, M.VMIN, XTOL)
        if abs(FRCMIN) <= 1.0:
            M.write(NO_MACRO_SLIP, M.XINF, M.XSUP)
            M.pause("Pressez ENTER pour continuer")
            label = 900 if ICHOIX == 1 else 700 if ICHOIX == 3 else 800
            continue
        XB1 = RTFLSP(M, M.APPBRN, M.XINF, M.XM - real4(0.03), XACC)
        if M.ICONVERG != 1:
            XB2 = RTFLSP(M, M.APPBRN, M.XM + real4(0.03), M.XSUP, XACC)
        while True:  # 910
            if M.ICONVERG == 1:
                M.ICONVERG = 0
                M.write("3X,'XINF= ',F5.2,3X,'XSUP=',F5.2,/", M.XINF, M.XSUP)
                M.write("/,3X,'Entrez l approx. de XB1:',\\")
                XB1 = M.readReal("XB1")
                M.write("/,3X,'Entrez l approx. de XB2:',\\")
                XB2 = M.readReal("XB2")
            XIC = 0.0
            PSIC = 0.0
            XB1, XB2, XIC, PSIC = NEWT(M, XB1, XB2, XIC, PSIC)
            if M.ICONVERG != 1:
                break
        if ICHOIX == 2:
            RDEP = (M.DEPAME(XMIN) - DEPH(M, XMIN, XB1, XIC, PSIC)) / M.DEPAME(XMIN)
        DSP = QROMB(M, DUM0, DUM1, XB1, XIC, PSIC, partial(DMACRO, M), XB1, XB2)
        DSPTMP = DSPTMP + DSP
        ICHOIX = ECSNCONT(M, ICHOIX, XB1, XB2, XIC, PSIC, DSP, DSPTOTAL, RDEP)
        if ICHOIX == 4:
            return M
        M.pause("Pressez ENTER pour continuer")
        if M.XM < M.WLBAR / 4.0 - real4(0.6) and ICHOIX == 1:
            label = 900
            continue
        DSPTOTAL = 4.0 * DSPTMP
        ECSNCONT(M, ICHOIX, XB1, XB2, XIC, PSIC, DSP, DSPTOTAL, RDEP)
        return M
