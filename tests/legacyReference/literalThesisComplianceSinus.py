"""ZETASIN with ENSNZETA and ECSNZETA, line by line (manual pages 46, 67 and 71).

The routines it shares with ZETARHOB are in literalThesisCompliance.
"""

from __future__ import annotations

import math

from legacyReference.literalThesisCompliance import (
    DISPENRG,
    INCONNUS,
    NMAX,
    SORTZETA,
    Unknowns,
)
from legacyReference.literalThesisFunctions import DEPH, bindSinus
from legacyReference.literalThesisMachine import Machine, real4, rpow
from legacyReference.literalThesisSinus import MENU, TOTAL_ENERGY, halfPitchStart
from legacyReference.literalThesisSystem import APPSIN, COMP, UNRES


def ENSNZETA(M: Machine) -> int:  # page 71
    UN = 1.0
    M.PI = math.acos(-UN)
    while True:  # 110
        M.write("/////////,3X,'Ce programme peut déterminer:'")
        M.write(MENU)
        M.write("///,9X,'Entrez votre choix:',\\")
        ICHOIX = M.readInteger("ICHOIX")
        if not (ICHOIX < 1 or ICHOIX > 3):
            break
    M.THETA = M.PI / 2.0
    if ICHOIX == 2:
        M.THETA = 0.0
    M.write("/,9X,'Entrez un nombre pair de pas par longueur',' d onde:',\\")
    M.WLBAR = M.readReal("WLBAR")
    M.write("/,9X,'Entrez l amplitude adimensionnelle:',\\")
    M.ABAR = M.readReal("ABAR")
    M.write("/,9X,'Entrez le facteur de complaisance GAMMA1:',\\")
    M.GAM1 = M.readReal("GAM1")
    M.PP = M.WLBAR + 1.0
    M.PN = M.WLBAR - 1.0
    M.PPA = M.PP / M.WLBAR
    M.PPB = M.PN / M.WLBAR
    M.PP1 = 2.0 * M.PI * M.PPA
    M.PN1 = 2.0 * M.PI * M.PPB
    M.GAMEXP = (4.0 * rpow(M.PI, 2.0)) / M.GAM1
    M.GAMD1 = (M.ABAR * M.WLBAR) / (4.0 * M.PI)
    M.GAME1 = M.GAMD1 * ((2.0 * M.PI) / M.WLBAR)
    M.GAMF1 = M.GAME1 * ((2.0 * M.PI) / M.WLBAR)
    return ICHOIX


PARAMETERS = (
    "1X,'Pour l amplitude adimensionnelle =',F5.2,/,"
    "1X,'un nombre de pas dans la longueur d onde =',F5.1,/,1X,"
    "'et un facteur de complaisance GAMMA1 =',F5.3,/,1X,'avec la position initiale THETAi = ',"
)


def ECSNZETA(M: Machine, ICHOIX, U: Unknowns, DSP, DSPTOTAL, RDEP) -> int:  # page 67
    if DSPTOTAL == 0.0:
        if ICHOIX == 2 or ICHOIX == 3:
            M.write("/,25X,'MODELE AVEC COMPLAISANCE'")
            M.write("24X,'pour la flèche sinusoidale'")
            M.write("/,26X,'****** SOLUTION ******',/")
        if ICHOIX == 1 and DSPTOTAL == 0.0:
            M.write("//////")
        M.write(
            PARAMETERS + "F7.5,' rad. et',/,1X,'pour le demi-pas XINF =',F5.2,' à XSUP =',F5.2",
            M.ABAR, M.WLBAR, M.GAM1, M.THETA, M.XINF, M.XSUP,
        )  # fmt: skip
        M.write("/,1X,'Les 4 inconnues de la région centrale sont:',/")
        M.write(
            "3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'BTM=',D14.8,2X,'ETM=',D14.8",
            U.XB1, U.XB2, U.BTM, U.ETM,
        )  # fmt: skip
        if ICHOIX == 2:
            M.write("3X,'-> les valeurs des autres inconnues sont ','sauvegardées dans INCONNUS.DAT'")
            M.write(
                "/, 1X,'et le rapport relatif de différence',' maximale de déplacement =',E14.8,//",
                RDEP,
            )
            INCONNUS(M, U, rayon=False)
            return 4
        M.write("/,3X,'Energie dissipée dans le demi-pas =',E14.8", DSP)
        if ICHOIX == 1 and DSPTOTAL == 0.0:
            M.write("////")
        if ICHOIX == 3:
            INCONNUS(M, U, rayon=False)
            M.write("3X,'(Voir ENERGY.DAT pour details)'")
            M.write("/,3X,'-> les valeurs des autres inconnues sont ','sauvegardées dans INCONNUS.DAT'")
            M.write(
                "//,3X,'Désirez-vous faire calculer le déplacement,',' la déformation et le rapport'"
                ",/,3X,'de friction le',' long du demi-pas (0=>OUI, 1=>NON):',\\"
            )
            ISORTIE = M.readInteger("ISORTIE")
            if ISORTIE < 0.5:
                SORTZETA(M, U)
            ICHOIX = 4
    if DSPTOTAL != 0.0:  # 800
        M.write("///,25X,'MODELE AVEC COMPLAISANCE'")
        M.write("24X,'pour la flèche sinusoidale'")
        M.write("//,26X,'****** SOLUTION ******',///")
        M.write(PARAMETERS + "F7.5,' rad.',////", M.ABAR, M.WLBAR, M.GAM1, M.THETA)
        M.write(TOTAL_ENERGY, DSPTOTAL)
    return ICHOIX


def ZETASIN(answers: dict[str, list[str]]) -> Machine:  # page 46
    M = Machine(answers)
    bindSinus(M)
    U = Unknowns()
    M.ICONVERG = 0
    DSPTOTAL = 0.0
    DSPTMP = 0.0
    M.NPORTION = 0
    M.EN = 2.0 / 3.0
    COMP(M, NMAX)
    ICHOIX = ENSNZETA(M)
    XTOUR = 0.0 - 0.5
    if ICHOIX == 2:
        XTOUR = ((M.WLBAR / 4.0) - 0.25) - 0.5
    if ICHOIX == 3:  # 700
        M.write("/,9X,'Nombre de tour de l origine (XTOUR) :',\\")
        XTOUR = M.readReal("XTOUR")
        XTOUR = XTOUR - 0.5
    while True:
        XTOUR = XTOUR + 0.5  # 900
        halfPitchStart(M, XTOUR)
        while True:  # 1000
            M.NPORTION = M.NPORTION + 1
            M.JDIM = 6 * M.NPORTION - 4
            M.NPOINT = 2 * (M.NPORTION - 2)
            while True:  # 500
                U.clear()
                if M.NPORTION == 1:
                    U.BTM, U.ETM = UNRES(M, U.A, U.B)
                    break
                U.XB1, U.XB2 = APPSIN(M, U.XK)
                U.newton(M)
                if M.ICONVERG != 1:
                    break
            N = M.NPORTION  # 990
            NPORTEMP = N
            if N < 11:
                DEPF = M.DEPFIL(M.XCOMP[N], M.YCOMP[N], M.ZETA[N], U.BTM, U.ETM, M.XM)
                DFDEP = ((M.DEPAME(M.XM) - DEPF) / M.GAM1) * 4.0 * M.PI
                RDEP = (M.DEPAME(M.XM) - DEPF) / M.DEPAME(M.XM)
            else:
                NPORTEMP = N - 1
                DFDEP = ((M.DEPAME(M.XM) - DEPH(M, M.XM, U.XB1, U.BTM, U.ETM)) / M.GAM1) * 4.0 * M.PI
                RDEP = (M.DEPAME(M.XM) - DEPH(M, M.XM, U.XB1, U.BTM, U.ETM)) / M.DEPAME(M.XM)
            M.write(
                "//,3X,'Modele a',I3,' port. lin.; 2 delta max.=',F7.4,3X,'Valeur max adm.=',F7.4",
                N, abs(DFDEP), M.XCOMP[NPORTEMP + 1] * (2.0),
            )  # fmt: skip
            if not ((abs(DFDEP) - 2.0 * M.XCOMP[NPORTEMP + 1]) > 0.0 and N < 11):
                break
        DSP = DISPENRG(M, U)
        DSPTMP = DSPTMP + DSP
        ICHOIX = ECSNZETA(M, ICHOIX, U, DSP, DSPTOTAL, RDEP)
        if ICHOIX == 4:
            return M
        M.pause("Pressez ENTER pour continuer")
        if M.XM < M.WLBAR / 4.0 - real4(0.6) and ICHOIX == 1:
            M.NPORTION = M.NPORTION - 1
            continue
        DSPTOTAL = 4.0 * DSPTMP
        ECSNZETA(M, ICHOIX, U, DSP, DSPTOTAL, RDEP)
        return M
