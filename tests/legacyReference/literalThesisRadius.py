"""HARDRHOB and CONTRHOB with their subroutines, line by line (manual pages 38, 41, 60-61,
73-74, 78, 86, 91, 94, 101), and the Newton solver of the continuity model shared with
CONTSIN. GOTOs are loops; each program is a function of its keyboard answers.
"""

from __future__ import annotations

import math
from functools import partial

from legacyReference.literalThesisFunctions import DEPH, DMACRO, DR2H, bindRayon
from legacyReference.literalThesisMachine import Machine, real4
from legacyReference.literalThesisNumerics import DLUBKSB, DLUDCMP, QROMB, RTFLSP, RTSEC

NO_MACRO_SLIP = "//,1X,'Pas de macro-glissement dans la demi-pas ','XINF=',F5.2,1X,'a XSUP=',F5.2"
RADIUS_LINE = (
    "1X,'Pour le rayon de courbure constant adimension','nel =',F5.3,/,"
    "1X'avec la position initiale THETAi = ',F7.5,' rad. et',/,"
    "1X,'pour le demi-pas XINF =',F4.2,' à XSUP =',F4.2"
)
RESULTS_41 = (
    "/,3X,'Energie dissipée dans le demi-pas =',E14.8,/, 3X,'Rapport relatif de différence',"
    "' maximale de déplacement =',E14.8"
)
ASK_PROFILE = (
    "/,3X,'Désirez-vous faire calculer le déplacement, la',' déformation et le rapport',/,"
    "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
)
CONVERGENCE = (
    "///,1X,'!!!PROBLEME DE CONVERGENCE, ',/,1X,'Veuillez recommencer avec une nouvelle approx.',/"
)


def firstHalfPitch(M: Machine) -> None:
    """The lines ENTHARD, ENTCONT and ENTZETA share: THETAi = 90 deg, XINF = 0."""
    UN = 1.0
    M.PI = math.acos(-UN)
    M.THETA = M.PI / 2.0
    M.XINF = 0.0
    M.XSUP = M.XINF + 0.5
    M.XM = (M.XINF + M.XSUP) / 2.0
    VCOTE = math.cos(2.0 * M.PI * M.XM + M.THETA)
    M.ICOTE = -1
    if VCOTE > 0.0:
        M.ICOTE = 1


def ENTHARD(M: Machine) -> None:  # page 74
    firstHalfPitch(M)
    while True:  # 100
        M.write("/,1X,'Entrez le rayon de courbure adim.:',\\")
        M.RHOB = M.readReal("RHOB")
        if M.ICOTE * (M.FRICTION(M.XM)) <= 0.0:
            M.write(NO_MACRO_SLIP, M.XINF, M.XSUP)
            M.pause("Pressez ENTER pour continuer")
            continue
        return


def ENTCONT(M: Machine) -> None:  # page 73
    firstHalfPitch(M)
    while True:  # 500
        M.write(
            "/,3X,'Entrez le rayon de courbure adim.',' (Valeur admissible 0.65<=>1.00):',\\"
        )
        M.RHOB = M.readReal("RHOB")
        if M.RHOB < real4(0.65):
            continue
        if M.ICOTE * (M.FRICTION(M.XM)) <= 0.0:
            M.write(NO_MACRO_SLIP, M.XINF, M.XSUP)
            M.pause("Pressez ENTER pour continuer")
            continue
        return


def SORTIE(M: Machine, XB1, XB2, XI, PSI) -> None:  # page 94
    M.openUnit(2, "DEP.DAT")
    M.openUnit(3, "ELG.DAT")
    M.openUnit(4, "FRC.DAT")
    M.write(
        "///,1X,'POSITION EN X',9X,'DEP. FIL',11X,'DEF. FIL',8X,'RAP. DE FRICTION',/"
    )
    X = M.XINF
    DX = 0.001
    while True:  # 1000
        DAME = M.DEPAME(X)
        EAME = M.ELGAME(X)
        FAME = M.FRCAME(X) / (2.0 * M.PI)
        if X > XB1 and X < XB2:
            DFIL = DEPH(M, X, XB1, XI, PSI)
            EFIL = DR2H(M, X, XB1, XI)
            FFIL = M.ICOTE * 1.0
        else:
            DFIL = DAME
            EFIL = EAME
            FFIL = FAME
        M.write("2X,F9.4,2X,3E20.8", X, DFIL, EFIL, FFIL)
        M.writeUnit(2, "1X,F7.4,2X,E16.8,2X,E16.8", X, DAME, DFIL)
        M.writeUnit(3, "1X,F7.4,2X,E16.8,2X,E16.8", X, EAME, EFIL)
        M.writeUnit(4, "1X,F7.4,2X,E16.8,2X,E16.8", X, FAME, FFIL)
        X = X + DX
        if not X <= M.XSUP + 0.1e-8:
            break
    M.closeUnit(2)
    M.closeUnit(3)
    M.closeUnit(4)


def ECRHARD(M: Machine, XB1, XB2, XIH, PSIH, DSP, RDEP) -> None:  # page 61
    M.write("/,29X,'MODELE DE HARDY'")
    M.write("12X,'pour la flèche ayant un rayon de courbure ','constant'")
    M.write("//,26X,'****** SOLUTION ******',/")
    M.write(RADIUS_LINE, M.RHOB, M.THETA, M.XINF, M.XSUP)
    M.write("//,1X,'Les 4 inconnues sont:',/")
    M.write("3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'XIH=',D14.8,2X,'PSIH=',D14.8", XB1, XB2, XIH, PSIH)
    M.write("//,1X,'Les résultats sont:'")
    M.write(RESULTS_41, DSP, RDEP)
    M.write(ASK_PROFILE)
    ISORTIE = M.readInteger("ISORTIE")
    if ISORTIE < 0.5:
        SORTIE(M, XB1, XB2, XIH, PSIH)


def HARDRHOB(answers: dict[str, list[str]]) -> Machine:  # page 41
    M = Machine(answers)
    bindRayon(M)
    XACC = 1e-10
    DUM0 = DUM1 = 0.0
    ENTHARD(M)
    XB1 = RTSEC(M, M.FRICTION, M.XINF, M.XM, XACC)
    XB2 = RTSEC(M, M.FRICTION, M.XM, M.XSUP, XACC)
    PSIH = M.DEPAME(XB1)
    XIH = -(M.ICOTE * M.PI * (XB2 - XB1))
    RDEP = (M.DEPAME(M.XM) - DEPH(M, M.XM, XB1, XIH, PSIH)) / M.DEPAME(M.XM)
    DSP = QROMB(M, DUM0, DUM1, XB1, XIH, PSIH, partial(DMACRO, M), XB1, XB2)
    ECRHARD(M, XB1, XB2, XIH, PSIH, DSP, RDEP)
    return M


# -- the continuity model's Newton solver (NEWT, VCB, JACO) -------------------


def VCB(M: Machine, XB1, XB2, XIC, PSIC, B) -> None:  # page 101
    JDIM = 4
    for I in range(1, JDIM + 1):
        B[I] = 0.0
    B[JDIM - 3] = -(M.DEPAME(XB1) - PSIC)
    B[JDIM - 2] = -(M.ELGAME(XB1) - XIC)
    B[JDIM - 1] = -(M.DEPAME(XB2) - DEPH(M, XB2, XB1, XIC, PSIC))
    B[JDIM] = -(M.ELGAME(XB2) - DR2H(M, XB2, XB1, XIC))


def JACO(M: Machine, XB1, XB2, XIC, A) -> None:  # page 78
    JDIM = 4
    for I in range(1, JDIM + 1):
        for J in range(1, JDIM + 1):
            A[I][J] = 0.0
    A[1][1] = M.ELGAME(XB1)
    A[1][2] = 0.0
    A[1][3] = 0.0
    A[1][4] = -1.0
    A[2][1] = M.FRCAME(XB1)
    A[2][2] = 0.0
    A[2][3] = -1.0
    A[2][4] = 0.0
    A[3][1] = -(M.ICOTE * 2.0 * M.PI * (XB1 - XB2)) + XIC
    A[3][2] = M.ELGAME(XB2) - DR2H(M, XB2, XB1, XIC)
    A[3][3] = XB1 - XB2
    A[3][4] = -1.0
    A[4][1] = M.ICOTE * 2.0 * M.PI
    A[4][2] = M.FRCAME(XB2) - M.ICOTE * 2.0 * M.PI
    A[4][3] = -1.0
    A[4][4] = 0.0


def NEWT(M: Machine, XB1, XB2, XIC, PSIC):  # page 86
    JDIM = 4
    B = [0.0] * (JDIM + 1)
    INDX = [0] * (JDIM + 1)
    A = [[0.0] * (JDIM + 1) for _ in range(JDIM + 1)]
    K = 0
    TOL = 1.0e-8
    while True:  # 1000
        XB1 = XB1 + B[JDIM - 3]
        XB2 = XB2 + B[JDIM - 2]
        XIC = XIC + B[JDIM - 1]
        PSIC = PSIC + B[JDIM]
        VCB(M, XB1, XB2, XIC, PSIC, B)
        JACO(M, XB1, XB2, XIC, A)
        DLUDCMP(M, A, JDIM, JDIM, INDX)
        DLUBKSB(A, JDIM, JDIM, INDX, B)
        C1 = XB1 - M.XINF
        C2 = M.XSUP - XB2
        if C1 < 0 or C2 < 0 or XB1 > XB2 or K >= 15:
            M.write(CONVERGENCE)
            M.ICONVERG = 1
            return XB1, XB2, XIC, PSIC
        M.write("/,3X,'Iteration #',I2", K)
        M.write("3X,'XB1='D14.8,8X,'XB2=',D14.8,8X", XB1, XB2)
        M.write("3X,'XIC='D14.8,8X,'PSIC=',D14.8", XIC, PSIC)
        if not (
            K == 0
            or abs(B[JDIM - 3] / XB1) >= TOL
            or abs(B[JDIM - 2] / XB2) >= TOL
            or abs(B[JDIM - 1] / XIC) >= TOL
            or abs(B[JDIM] / PSIC) >= TOL
        ):
            return XB1, XB2, XIC, PSIC  # 990
        K = K + 1  # 980


def PBCONV(M: Machine):  # page 91
    M.ICONVERG = 0
    M.write("3X,'XINF= ',F5.2,3X,'XSUP=',F5.2,/", M.XINF, M.XSUP)
    M.write("/,3X,'Entrez l approx. de XB1:',\\")
    XB1 = M.readReal("XB1")
    XB2 = M.XSUP - XB1
    return XB1, XB2


def ECRCONT(M: Machine, XB1, XB2, XIC, PSIC, DSP, RDEP) -> None:  # page 60
    M.write("/,18X,'MODELE AVEC CONTINUITE DE DEFORMATION'")
    M.write("12X,'pour la flèche ayant un rayon de courbure ','constant'")
    M.write("//,26X,'****** SOLUTION ******',/")
    M.write(RADIUS_LINE, M.RHOB, M.THETA, M.XINF, M.XSUP)
    M.write("//,1X,'Les 4 inconnues sont:',/")
    M.write("3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'XIC=',D14.8,2X,'PSIC=',D14.8", XB1, XB2, XIC, PSIC)
    M.write("//,1X,'Les résultats sont:'")
    M.write(RESULTS_41, DSP, RDEP)
    M.write(ASK_PROFILE)
    ISORTIE = M.readInteger("ISORTIE")
    if ISORTIE < 0.5:
        SORTIE(M, XB1, XB2, XIC, PSIC)


def CONTRHOB(answers: dict[str, list[str]]) -> Machine:  # page 38
    M = Machine(answers)
    bindRayon(M)
    XACC = 1e-10
    DUM0 = DUM1 = 0.0
    XB2 = 0.0
    ENTCONT(M)
    XB1 = RTFLSP(M, M.APPBRN, M.XINF, M.XM - real4(0.03), XACC)
    if M.ICONVERG != 1:
        XB2 = RTFLSP(M, M.APPBRN, M.XM + real4(0.03), M.XSUP, XACC)
    while True:  # 910
        if M.ICONVERG == 1:
            XB1, XB2 = PBCONV(M)
        XIC = 0.0
        PSIC = 0.0
        XB1, XB2, XIC, PSIC = NEWT(M, XB1, XB2, XIC, PSIC)
        if M.ICONVERG != 1:
            break
    RDEP = (M.DEPAME(M.XM) - DEPH(M, M.XM, XB1, XIC, PSIC)) / M.DEPAME(M.XM)
    DSP = QROMB(M, DUM0, DUM1, XB1, XIC, PSIC, partial(DMACRO, M), XB1, XB2)
    ECRCONT(M, XB1, XB2, XIC, PSIC, DSP, RDEP)
    return M
