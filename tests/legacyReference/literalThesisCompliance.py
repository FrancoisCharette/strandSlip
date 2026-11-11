"""ZETARHOB with its subroutines, line by line: pages 44, 54 (DISPENRG), 62, 75,
76 (INCONNUS) and 95 (SORTZETA); ZETASIN is in literalThesisComplianceSinus.

INCONNUS is printed set up for the sinusoid; its commented-out block for the constant
radius (GAM1, RHOB, THETAi) is the one ZETARHOB writes (`rayon=True`).
"""

from __future__ import annotations

from functools import partial

from legacyReference.literalThesisFunctions import (
    DEPH,
    DMACRO,
    DMICRO,
    DR2H,
    bindRayon,
)
from legacyReference.literalThesisMachine import Machine, rpow
from legacyReference.literalThesisNumerics import QROMB
from legacyReference.literalThesisRadius import firstHalfPitch
from legacyReference.literalThesisSystem import APPROX, COMP, NEWTON

NMAX = 10
JMAX = 62
REG = "1X,'REG.',I3,'=',E16.8"
ENERGY_45 = (
    "//,1X,'Energie dissipe dans tout le demi-pas=',E14.8,/,1X,'Total due au macro=',E14.8,/,"
    "1X,'Total due au micro=',E14.8,/,1X,'% due au macro=',F5.2,/,"
    "1X,'Energie dissipe dans la region de macro-glissement=',E14.8,/,"
    "1X,'Energie due au micro dans cette region=',E14.8,/1X,"
    "'% due au micro dans la region de macro=',F5.2"
)
ENERGY_46 = (
    "//,1X,'Il n y a que du micro-glissement dans ce demi-pas',/,"
    "1X,'Energie dissipe dans tout le demi-pas=',E14.8"
)


class Unknowns:
    """The arrays and scalars ZETARHOB and ZETASIN pass from routine to routine."""

    def __init__(self) -> None:
        self.BETAG = [0.0] * (NMAX + 1)
        self.ETAG = [0.0] * (NMAX + 1)
        self.BETAD = [0.0] * (NMAX + 1)
        self.ETAD = [0.0] * (NMAX + 1)
        self.XK = [0.0] * (2 * NMAX + 1)
        self.B = [0.0] * (JMAX + 1)
        self.A = [[0.0] * (JMAX + 1) for _ in range(JMAX + 1)]
        self.XB1 = self.XB2 = self.BTM = self.ETM = 0.0  # static: zero until assigned

    def clear(self) -> None:  # label 500
        for I in range(1, JMAX + 1):
            self.B[I] = 0.0
            for J in range(1, JMAX + 1):
                self.A[I][J] = 0.0
        for I in range(1, 2 * NMAX + 1):
            self.XK[I] = 0.0
        for I in range(1, NMAX + 1):
            self.BETAG[I] = self.ETAG[I] = self.BETAD[I] = self.ETAD[I] = 0.0
        self.BTM = 0.0
        self.ETM = 0.0

    def newton(self, M: Machine) -> None:
        U = self
        U.XB1, U.XB2, U.BTM, U.ETM = NEWTON(
            M, U.BETAG, U.ETAG, U.BETAD, U.ETAD, U.XK, U.XB1, U.XB2, U.BTM, U.ETM, U.A, U.B
        )


def DISPENRG(M: Machine, U: Unknowns) -> float:  # page 54
    X, Y, Z = M.XCOMP, M.YCOMP, M.ZETA
    N, NPOINT = M.NPORTION, M.NPOINT
    micro = partial(DMICRO, M)
    BETAG, ETAG, BETAD, ETAD, XK = U.BETAG, U.ETAG, U.BETAD, U.ETAD, U.XK
    M.openUnit(1, "ENERGY.DAT")
    M.writeUnit(1, "1X,'Energie dissipe dans chacune des regions du',' demi-pas:'")
    DSP = 0.0
    IREGION = 1
    DUM0 = 0.0
    DUM1 = 1.0
    if N == 1:
        DSP = QROMB(M, X[1], Y[1], Z[1], U.BTM, U.ETM, micro, M.XINF, M.XSUP)
        M.writeUnit(1, REG, IREGION, DSP)
        M.closeUnit(1)
        return DSP
    if N == 2:
        DSPTMP = QROMB(M, X[1], Y[1], Z[1], BETAG[1], ETAG[1], micro, M.XINF, U.XB1)
        DSP = DSP + DSPTMP
        M.writeUnit(1, REG, IREGION, DSPTMP)
        DSPTMP = QROMB(M, X[2], Y[2], Z[2], U.BTM, U.ETM, micro, U.XB1, U.XB2)
        DSP = DSP + DSPTMP
        IREGION = IREGION + 1
        M.writeUnit(1, REG, IREGION, DSPTMP)
        DSPTMP = QROMB(M, X[1], Y[1], Z[1], BETAD[1], ETAD[1], micro, U.XB2, M.XSUP)
        DSP = DSP + DSPTMP
        IREGION = IREGION + 1
        M.writeUnit(1, REG, IREGION, DSPTMP)
        M.closeUnit(1)
        return DSP
    DSPTMP = QROMB(M, X[1], Y[1], Z[1], BETAG[1], ETAG[1], micro, M.XINF, XK[1])
    DSP = DSP + DSPTMP
    M.writeUnit(1, REG, IREGION, DSPTMP)
    for I in range(1, NPOINT // 2):
        IREGION = IREGION + 1
        DSPTMP = QROMB(
            M, X[I + 1], Y[I + 1], Z[I + 1], BETAG[I + 1], ETAG[I + 1], micro, XK[I], XK[I + 1]
        )
        DSP = DSP + DSPTMP
        M.writeUnit(1, REG, IREGION, DSPTMP)
    H = NPOINT // 2 + 1
    DSPTMP = QROMB(M, X[H], Y[H], Z[H], BETAG[H], ETAG[H], micro, XK[H - 1], U.XB1)
    DSP = DSP + DSPTMP
    IREGION = IREGION + 1
    M.writeUnit(1, REG, IREGION, DSPTMP)
    DSPMAC = DMICMAC = 0.0
    if N < 11:
        DSPTMP = QROMB(M, X[N], Y[N], Z[N], U.BTM, U.ETM, micro, U.XB1, U.XB2)
        DSP = DSP + DSPTMP
        M.writeUnit(1, REG, N, DSPTMP)
    else:
        DSPTMP = QROMB(M, DUM0, DUM1, U.XB1, U.BTM, U.ETM, partial(DMACRO, M), U.XB1, U.XB2)
        DSPMAC = DSPTMP + ((6.0 * M.GAM1) / M.PI) * (1.0 / (M.EN + 1.0) - 1) * (U.XB2 - U.XB1)
        DMICMAC = ((6.0 * M.GAM1) / M.PI) * (1.0 / (M.EN + 1.0) - 0.5) * (U.XB2 - U.XB1)
        DSP = DSP + DSPMAC
        M.writeUnit(1, REG, N, DSPMAC)
    DSPTMP = QROMB(M, X[H], Y[H], Z[H], BETAD[H], ETAD[H], micro, U.XB2, XK[H])
    DSP = DSP + DSPTMP
    IREGION = IREGION + 2
    M.writeUnit(1, REG, IREGION, DSPTMP)
    for I in range(NPOINT // 2 + 1, NPOINT):
        IREGION = IREGION + 1
        JPOINT = NPOINT - (I - 1)
        DSPTMP = QROMB(
            M, X[JPOINT], Y[JPOINT], Z[JPOINT], BETAD[JPOINT], ETAD[JPOINT], micro, XK[I], XK[I + 1]
        )
        DSP = DSP + DSPTMP
        M.writeUnit(1, REG, IREGION, DSPTMP)
    DSPTMP = QROMB(M, X[1], Y[1], Z[1], BETAD[1], ETAD[1], micro, XK[NPOINT], M.XSUP)
    DSP = DSP + DSPTMP
    M.writeUnit(1, REG, IREGION + 1, DSPTMP)
    if N == 11:
        DMIC = DSP - DSPMAC + DMICMAC
        DMAC = DSPMAC - DMICMAC
        DSPRAP = (DMAC / DSP) * 100
        RAPMICMAC = (DMICMAC / DSPMAC) * 100
        M.writeUnit(1, ENERGY_45, DSP, DMAC, DMIC, DSPRAP, DSPMAC, DMICMAC, RAPMICMAC)
    else:
        M.writeUnit(1, ENERGY_46, DSP)
    M.closeUnit(1)
    return DSP


def INCONNUS(M: Machine, U: Unknowns, rayon: bool) -> None:  # page 76
    M.openUnit(2, "INCONNUS.DAT")
    M.writeUnit(2, "1X,'Les paramètres imposés sont:'")
    if rayon:
        M.writeUnit(
            2, "1X,'GAM1=',E14.8,3X,'RHOB=',F9.6,3X,'THETAi=',F9.6", M.GAM1, M.RHOB, M.THETA
        )
    else:
        M.writeUnit(
            2,
            "1X,'ABAR=',E14.8,2X,'WLBAR=',F9.6,2X,'GAM1=',E14.8,2X,'THETAi=',F9.6",
            M.ABAR, M.WLBAR, M.GAM1, M.THETA,
        )  # fmt: skip
    M.writeUnit(
        2,
        "1X,'NPORTION=',I2,3X,'NPOINT=',I2,3X,'XINF=',D16.10,2X,'XSUP=',D16.10",
        M.NPORTION, M.NPOINT, M.XINF, M.XSUP,
    )  # fmt: skip
    M.writeUnit(2, "/,1X,'Les paramètres de complaisance sont:'")
    for I in range(1, M.NPORTION):
        M.writeUnit(
            2,
            "1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9,2X,'ZETA(',I2,')=',D14.9",
            I, M.XCOMP[I], I, M.YCOMP[I], I, M.ZETA[I],
        )  # fmt: skip
    N = M.NPORTION
    M.writeUnit(
        2, "1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9", N, M.XCOMP[N], N, M.YCOMP[N]
    )
    M.writeUnit(2, "/,1X,'Les inconnues sont:'")
    for I in range(1, N):
        M.writeUnit(2, "1X,'BETAG(',I2,')=',D16.10,2X,'ETAG(',I2,')=',D16.10", I, U.BETAG[I], I, U.ETAG[I])
    M.writeUnit(2, "/")
    for I in range(1, N):
        M.writeUnit(2, "1X,'BETAD(',I2,')=',D16.10,2X,'ETAD(',I2,')=',D16.10", I, U.BETAD[I], I, U.ETAD[I])
    M.writeUnit(2, "/")
    for I in range(1, M.NPOINT + 1):
        M.writeUnit(2, "1X,'XK(',I2,')=',D16.10", I, U.XK[I])
    M.writeUnit(2, "/")
    M.writeUnit(
        2,
        "1X,'XB1=',D14.8,2X,'XB2=',D14.8,/,1X,'BTM=',D14.8,2X,'ETM=',D14.8",
        U.XB1, U.XB2, U.BTM, U.ETM,
    )  # fmt: skip
    M.closeUnit(2)


def profileAt(M: Machine, U: Unknowns, X, portion, side):
    """DEPFIL, ELGFIL and FRCFIL/(2 PI) of one micro-slip region (the blocks of SORTZETA)."""
    Z = M.ZETA
    if side == "center":
        BTA, TA = U.BTM, U.ETM
    elif side == "left":
        BTA, TA = U.BETAG[portion], U.ETAG[portion]
    else:
        BTA, TA = U.BETAD[portion], U.ETAD[portion]
    DFIL = M.DEPFIL(M.XCOMP[portion], M.YCOMP[portion], Z[portion], BTA, TA, X)
    EFIL = M.ELGFIL(Z[portion], BTA, TA, X)
    FFIL = M.FRCFIL(Z[portion], BTA, TA, X) / (2.0 * M.PI)
    return DFIL, EFIL, FFIL


def SORTZETA(M: Machine, U: Unknowns) -> None:  # page 95
    names = ("ZETADEP.DAT", "ZETAELG.DAT", "ZETAFRC.DAT", "ZETADEPX.DAT", "ZETAELGX.DAT")
    for unit, name in zip((2, 3, 4, 6, 7, 8), (*names, "ZETAFRCX.DAT"), strict=True):
        M.openUnit(unit, name)
    M.write("///,1X,'POSITION EN X',9X,'DEP. FIL',11X,'DEF. FIL',8X,'RAP. DE FRICTION',/")
    N, NPOINT, XK, XB1, XB2 = M.NPORTION, M.NPOINT, U.XK, U.XB1, U.XB2
    H = NPOINT // 2
    X = M.XINF
    DX = 0.001
    DFIL = EFIL = FFIL = 0.0

    def transition(values) -> None:
        for unit, value in zip((6, 7, 8), values, strict=True):
            M.writeUnit(unit, "2X,2E20.8", X, value)

    while True:  # 1000
        DAME = M.DEPAME(X)
        EAME = M.ELGAME(X)
        FAME = M.FRCAME(X) / (2.0 * M.PI)
        if N == 1:
            DFIL, EFIL, FFIL = profileAt(M, U, X, 1, "center")
        elif N == 2:
            if X < XB1:
                DFIL, EFIL, FFIL = profileAt(M, U, X, 1, "left")
                if X > XB1 - DX and X < XB1:
                    transition((DFIL, EFIL, FFIL))
            if X >= XB1 and X <= XB2:
                DFIL, EFIL, FFIL = profileAt(M, U, X, 2, "center")
            if X > XB2:
                DFIL, EFIL, FFIL = profileAt(M, U, X, 1, "right")
                if X > XB2 and X < XB2 + DX:
                    transition((DFIL, EFIL, FFIL))
        else:
            if X >= M.XINF and X < XK[1]:
                DFIL, EFIL, FFIL = profileAt(M, U, X, 1, "left")
                if X > XK[1] - DX and X < XK[1]:
                    transition((DFIL, EFIL, FFIL))
                M.write("2X,'PORTION #1'")
            for I in range(1, H):
                if X >= XK[I] and X < XK[I + 1]:
                    DFIL, EFIL, FFIL = profileAt(M, U, X, I + 1, "left")
                    if X > XK[I + 1] - DX and X < XK[I + 1]:
                        transition((DFIL, EFIL, FFIL))
                    M.write("2X,'PORTION #:',I2", I + 1)
            if X >= XK[H] and X < XB1:
                DFIL, EFIL, FFIL = profileAt(M, U, X, H + 1, "left")
                if X > XB1 - DX and X < XB1:
                    transition((DFIL, EFIL, FFIL))
                M.write("2X,'PORTION #:',I2", H + 1)
            if X >= XB1 and X < XB2:
                if N < 11:
                    DFIL, EFIL, FFIL = profileAt(M, U, X, N, "center")
                else:
                    DFIL = DEPH(M, X, XB1, U.BTM, U.ETM)
                    EFIL = DR2H(M, X, XB1, U.BTM)
                    FFIL = -1.0
                    M.write("2X,'REGION MACRO-GLISSMENT'")
            if X >= XB2 and X < XK[H + 1]:
                DFIL, EFIL, FFIL = profileAt(M, U, X, H + 1, "right")
                M.write("2X,'PORTION #:',I2", H + 1)
                if X > XB2 and X < XB2 + DX:
                    transition((DFIL, EFIL, FFIL))
            for I in range(H + 1, NPOINT):
                JPOINT = NPOINT - (I - 1)
                if X >= XK[I] and X < XK[I + 1]:
                    DFIL, EFIL, FFIL = profileAt(M, U, X, JPOINT, "right")
                    if X > XK[I] and X < XK[I] + DX:
                        transition((DFIL, EFIL, FFIL))
                    M.write("2X,'PORTION #:',I2", JPOINT)
            if X >= XK[NPOINT] and X <= M.XSUP:
                DFIL, EFIL, FFIL = profileAt(M, U, X, 1, "right")
                if X > XK[NPOINT] and X < XK[NPOINT] + DX:
                    transition((DFIL, EFIL, FFIL))
                M.write("2X,'PORTION #1'")
        DIFDEP = DAME - DFIL  # 995
        DIFELG = EAME - EFIL
        DIFFRC = FAME - FFIL
        M.write("2X,F9.4,2X,3E20.8", X, DFIL, EFIL, FFIL)
        M.writeUnit(2, "2X,F9.4,2X,3E20.8", X, DAME, DFIL, DIFDEP)
        M.writeUnit(3, "2X,F9.4,2X,3E20.8", X, EAME, EFIL, DIFELG)
        M.writeUnit(4, "2X,F9.4,2X,3E20.8", X, FAME, FFIL, DIFFRC)
        X = X + DX
        if not X <= M.XSUP:
            break
    for unit in (2, 3, 4, 6, 7, 8):
        M.closeUnit(unit)


def ENTZETA(M: Machine) -> None:  # page 75
    firstHalfPitch(M)
    M.EN = 2.0 / 3.0
    M.write("/,3X,'Entrez le facteur complaisance GAM1:',\\")
    M.GAM1 = M.readReal("GAM1")
    M.write("/,3X,'Entrez le rayon de courbure adim.:',\\")
    M.RHOB = M.readReal("RHOB")
    M.GAMEXP = (4.0 * rpow(M.PI, 2.0)) / (M.GAM1)
    M.GAMD1 = 1.0 / (2.0 * M.PI * M.RHOB)
    M.GAME1 = 2.0 * M.PI * M.GAMD1
    M.GAMF1 = 2.0 * M.PI * M.GAME1


def ECRZETA(M: Machine, U: Unknowns, DSP, RDEP) -> None:  # page 62
    M.write("/,25X,'MODELE AVEC COMPLAISANCE'")
    M.write("12X,'pour la flèche ayant un rayon de courbure ','constant'")
    M.write("//,26X,'****** SOLUTION ******',/")
    M.write(
        "1X,'Pour le rayon de courbure constant adimension','nel =',F5.3,/,"
        "1X,'avec un facteur de complaisance GAM1 =',F5.3,/,"
        "1X,'pour la position initiale THETAi = ',F7.4,' rad. et',/,"
        "1X,'le demi-pas XINF =',F4.2,' à XSUP =',F4.2",
        M.RHOB, M.GAM1, M.THETA, M.XINF, M.XSUP,
    )  # fmt: skip
    INCONNUS(M, U, rayon=True)
    M.write("///,1X,'Les résultats sont:'")
    M.write(
        "/,3X,'Energie dissipée dans le demi-pas =',E14.8,2X,'(Détails dans ENERGY.DAT)',/, "
        "3X,'Rapport relatif de différence',' maximale de déplacement =',E14.8,//,"
        "3X,'Les valeurs des '       'inconnues sont sauvegardées dans INCONNUS.DAT',/,",
        DSP, RDEP,
    )  # fmt: skip
    M.write(
        "//,3X,'Désirez-vous faire calculer le déplacement,',' la déformation et le rapport',/,"
        "3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
    )
    ISORTIE = M.readInteger("ISORTIE")
    if ISORTIE < 0.5:
        SORTZETA(M, U)


def ZETARHOB(answers: dict[str, list[str]]) -> Machine:  # page 44
    M = Machine(answers)
    bindRayon(M)
    U = Unknowns()
    M.ICONVERG = 0
    M.NPORTION = 0
    ENTZETA(M)
    COMP(M, NMAX)
    while True:  # 1000
        M.NPORTION = M.NPORTION + 1
        if M.NPORTION != 1:
            M.JDIM = 6 * M.NPORTION - 4
            M.NPOINT = 2 * (M.NPORTION - 2)
            while True:  # 500
                U.clear()
                U.XB1, U.XB2 = APPROX(M, U.XK)
                U.newton(M)
                if M.ICONVERG != 1:
                    break
        N = M.NPORTION  # 990
        NPORTEMP = N
        if N < 11:
            DEPF = M.DEPFIL(M.XCOMP[N], M.YCOMP[N], M.ZETA[N], U.BTM, U.ETM, M.XM)
            DFDEP = abs(((M.DEPAME(M.XM) - DEPF) / M.GAM1) * 4.0 * M.PI)
            RDEP = (M.DEPAME(M.XM) - DEPF) / M.DEPAME(M.XM)
        else:
            NPORTEMP = N - 1
            DFDEP = abs(((M.DEPAME(M.XM) - DEPH(M, M.XM, U.XB1, U.BTM, U.ETM)) / M.GAM1) * 4.0 * M.PI)
            RDEP = (M.DEPAME(M.XM) - DEPH(M, M.XM, U.XB1, U.BTM, U.ETM)) / M.DEPAME(M.XM)
        M.write(
            "//,3X,'Modèle à',I3,' port. liné; 2 delta max.=',F7.4,3X,'Valeur max adm.=',F7.4",
            N, DFDEP, M.XCOMP[NPORTEMP + 1] * (2.0),
        )  # fmt: skip
        if not ((DFDEP - 2.0 * M.XCOMP[NPORTEMP + 1]) > 0.0 and N < 11):
            break
    DSP = DISPENRG(M, U)
    ECRZETA(M, U, DSP, RDEP)
    return M
