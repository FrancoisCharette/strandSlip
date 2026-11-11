"""The FUNCTION listings of annex C, sections C.3 to C.5, line by line.

Section C.4 holds the constant-radius versions of DEPAME, ELGAME, FRCAME,
FRICTION, APPBRN, DEPFIL, ELGFIL and FRCFIL (pages 117-124), section C.5 the
sinusoidal ones and VMIN (pages 125-133); `bindRayon` and `bindSinus` give a
Machine the set its program was linked with. DEPH, DR2H, DMACRO, DMICRO and
F1D..F2E (section C.3) are shared.
"""

from __future__ import annotations

import math
from functools import partial

from legacyReference.literalThesisMachine import Machine, dnint, rpow

# -- section C.4: constant radius of curvature --------------------------------


def DEPAME_R(M: Machine, XF):  # page 118, equation A.1
    return (math.cos(M.THETA) - math.cos(2.0 * M.PI * XF + M.THETA)) / (2.0 * M.PI * M.RHOB)


def ELGAME_R(M: Machine, XF):  # page 120, equation A.3
    return math.sin(2.0 * M.PI * XF + M.THETA) / M.RHOB


def FRCAME_R(M: Machine, XF):  # page 122, equation A.5
    return (2.0 * M.PI * math.cos(2.0 * M.PI * XF + M.THETA)) / M.RHOB


def FRICTION_R(M: Machine, XF):  # page 124
    return (math.cos(2.0 * M.PI * XF + M.THETA) / M.RHOB) - M.ICOTE * 1.0


def APPBRN_R(M: Machine, XF):  # page 117
    TMP1 = math.sin(2.0 * M.PI * XF + M.THETA) / M.RHOB
    TMP2 = -(M.ICOTE * 2.0 * M.PI * (M.XM - XF))
    return TMP1 - TMP2


def DEPFIL_R(M: Machine, BXORG, BYORG, ZTA, BTA, TA, XF):  # page 119, equation A.17
    TMP1 = BTA * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3 = M.GAMD1 * math.cos(M.THETA)
    TMP4 = (M.GAMD1 / (M.GAM1 * ZTA + 1)) * math.cos((2.0 * M.PI * XF) + M.THETA)
    return (
        TMP1
        + TMP2
        + TMP3
        - TMP4
        + M.ICOTE * 2.0 * (M.GAM1 / (4.0 * M.PI)) * BXORG
        - M.ICOTE * 2.0 * (M.GAM1 / (4.0 * M.PI)) * ZTA * BYORG
    )


def ELGFIL_R(M: Machine, ZTA, BTA, TA, XF):  # page 121, equation A.23
    TMP1 = BTA * math.sqrt(M.GAMEXP / ZTA) * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * math.sqrt(M.GAMEXP / ZTA) * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3 = (M.GAME1 / (M.GAM1 * ZTA + 1)) * math.sin(2.0 * M.PI * XF + M.THETA)
    return TMP1 - TMP2 + TMP3


def FRCFIL_R(M: Machine, ZTA, BTA, TA, XF):  # page 123, equation A.24
    TMP1 = BTA * (M.GAMEXP / ZTA) * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * (M.GAMEXP / ZTA) * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3 = (M.GAMF1 / (M.GAM1 * ZTA + 1)) * math.cos(2.0 * M.PI * XF + M.THETA)
    return TMP1 + TMP2 + TMP3


# -- section C.5: sinusoid ----------------------------------------------------


def DEPAME_S(M: Machine, XF):  # page 126, equation A.30
    TMP3A = math.sin(XF * M.PN1 + M.THETA) - math.sin(M.THETA)
    TMP3B = math.sin(XF * M.PP1 + M.THETA) - math.sin(M.THETA)
    return ((M.WLBAR * M.ABAR) / (4.0 * M.PI)) * (TMP3A / M.PN - TMP3B / M.PP)


def ELGAME_S(M: Machine, XF):  # page 128, equation A.31
    return M.ABAR * math.sin(2.0 * M.PI * XF + M.THETA) * math.sin((2 * M.PI * XF) / M.WLBAR)


def FRCAME_S(M: Machine, XF):  # page 130, equation A.32
    TMP1 = math.cos(2.0 * M.PI * XF + M.THETA) * math.sin((2.0 * M.PI * XF) / M.WLBAR)
    TMP2 = math.sin(2.0 * M.PI * XF + M.THETA) * math.cos((2.0 * M.PI * XF) / M.WLBAR)
    return ((2.0 * M.PI * M.ABAR) / M.WLBAR) * (M.WLBAR * TMP1 + TMP2)


def FRICTION_S(M: Machine, XF):  # page 132
    TMP1 = math.cos(2.0 * M.PI * XF + M.THETA) * math.sin((2.0 * M.PI * XF) / M.WLBAR)
    TMP2 = math.sin(2.0 * M.PI * XF + M.THETA) * math.cos((2.0 * M.PI * XF) / M.WLBAR)
    return (M.ABAR / M.WLBAR) * (M.WLBAR * TMP1 + TMP2) - M.ICOTE * 1.0


def VMIN(M: Machine, XF):  # page 133
    TMP1 = math.cos(2.0 * M.PI * XF + M.THETA) * math.sin((2.0 * M.PI * XF) / M.WLBAR)
    TMP2 = math.sin(2.0 * M.PI * XF + M.THETA) * math.cos((2.0 * M.PI * XF) / M.WLBAR)
    return -(M.ICOTE * (M.ABAR / M.WLBAR) * (M.WLBAR * TMP1 + TMP2))


def APPBRN_S(M: Machine, XF):  # page 125
    TMP1 = M.ABAR * math.sin(2.0 * M.PI * XF + M.THETA) * math.sin((2 * M.PI * XF) / M.WLBAR)
    TMP2 = M.ICOTE * 2.0 * M.PI * (M.XM - XF)
    return TMP1 + TMP2


def DEPFIL_S(M: Machine, BXORG, BYORG, ZTA, BTA, TA, XF):  # page 127, equation A.39
    TMP1 = BTA * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3A = math.sin(XF * M.PN1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPB, 2.0) + 1.0) - math.sin(
        M.THETA
    )
    TMP3B = math.sin(XF * M.PP1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPA, 2.0) + 1.0) - math.sin(
        M.THETA
    )
    TMP3 = M.GAMD1 * (TMP3A / M.PN - TMP3B / M.PP)
    return (
        TMP1
        + TMP2
        + TMP3
        + 2.0 * (M.GAM1 / (4.0 * M.PI)) * M.ICOTE * BXORG
        - 2.0 * (M.GAM1 / (4.0 * M.PI)) * M.ICOTE * ZTA * BYORG
    )


def ELGFIL_S(M: Machine, ZTA, BTA, TA, XF):  # page 129, equation A.40
    TMP1 = BTA * math.sqrt(M.GAMEXP / ZTA) * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * math.sqrt(M.GAMEXP / ZTA) * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3A = math.cos(XF * M.PN1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPB, 2.0) + 1.0)
    TMP3B = math.cos(XF * M.PP1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPA, 2.0) + 1.0)
    TMP3 = M.GAME1 * (TMP3A - TMP3B)
    return TMP1 - TMP2 + TMP3


def FRCFIL_S(M: Machine, ZTA, BTA, TA, XF):  # page 131, equation A.41
    TMP1 = BTA * (M.GAMEXP / ZTA) * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))
    TMP2 = TA * (M.GAMEXP / ZTA) * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))
    TMP3A = -(M.PN * math.sin(XF * M.PN1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPB, 2.0) + 1.0))
    TMP3B = M.PP * math.sin(XF * M.PP1 + M.THETA) / (M.GAM1 * ZTA * rpow(M.PPA, 2.0) + 1.0)
    TMP3 = M.GAMF1 * (TMP3A + TMP3B)
    return TMP1 + TMP2 + TMP3


# -- section C.3: shared ------------------------------------------------------


def DEPH(M: Machine, XH, XH1, H1, H2):  # page 106
    return (M.ICOTE * M.PI) * ((XH - XH1) * (XH - XH1)) + (H1 * (XH - XH1)) + H2


def DR2H(M: Machine, XH, XH1, H1):  # page 109
    return (M.ICOTE * 2.0 * M.PI) * (XH - XH1) + H1


def DMACRO(M: Machine, DUM0, DUM1, XB1, BTA, TA, XF):  # page 107
    DIFDEP = abs(M.DEPAME(XF) - DEPH(M, XF, XB1, BTA, TA))
    return 4.0 * DIFDEP


def DMICRO(M: Machine, BXORG, BYORG, ZTA, BTA, TA, XF):  # page 108, equation A.51
    DIFDEP = abs(M.DEPAME(XF) - M.DEPFIL(BXORG, BYORG, ZTA, BTA, TA, XF))
    CSTMP1 = (4.0 * M.PI * DIFDEP) / (3.0 * M.GAM1)
    CSTMP2 = (6.0 * M.GAM1) / ((M.EN + 1.0) * M.PI)
    if CSTMP1 > 1.0:
        CSTMP1 = dnint(CSTMP1)
    if CSTMP1 > 1.0:
        M.write(
            "///,1X,'ATTENTION! FUNCTION DMICRO:',2X,'la valeur =>',5X,F20.18,/,24X,"
            "'est change pour =>',5X,F20.18",
            CSTMP1,
            1.0,
        )
        M.pause("Pressez ENTER pour continuer")
        CSTMP1 = 1.0
    TMP1 = 1.0 - rpow(1.0 - CSTMP1, (M.EN + 1.0) / M.EN)
    TMP2A = (M.EN + 1.0) - (((M.EN + 1.0) / 2.0) * CSTMP1)
    TMP2B = 1.0 - rpow(1.0 - CSTMP1, 1.0 / M.EN)
    TMP2 = TMP2A * TMP2B
    return CSTMP2 * (TMP1 - TMP2)


def F1D(M: Machine, XF, ZTA):  # page 110
    return math.exp(XF * math.sqrt(M.GAMEXP / ZTA))


def F1E(M: Machine, XF, ZTA):  # page 111
    return math.sqrt(M.GAMEXP / ZTA) * math.exp(XF * math.sqrt(M.GAMEXP / ZTA))


def F2D(M: Machine, XF, ZTA):  # page 112
    return math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA)))


def F2E(M: Machine, XF, ZTA):  # page 113
    return -(math.sqrt(M.GAMEXP / ZTA) * math.exp(-(XF * math.sqrt(M.GAMEXP / ZTA))))


def bindRayon(M: Machine) -> None:
    M.DEPAME, M.ELGAME = partial(DEPAME_R, M), partial(ELGAME_R, M)
    M.FRCAME, M.FRICTION = partial(FRCAME_R, M), partial(FRICTION_R, M)
    M.APPBRN = partial(APPBRN_R, M)
    M.DEPFIL, M.ELGFIL, M.FRCFIL = partial(DEPFIL_R, M), partial(ELGFIL_R, M), partial(FRCFIL_R, M)


def bindSinus(M: Machine) -> None:
    M.DEPAME, M.ELGAME = partial(DEPAME_S, M), partial(ELGAME_S, M)
    M.FRCAME, M.FRICTION = partial(FRCAME_S, M), partial(FRICTION_S, M)
    M.APPBRN, M.VMIN = partial(APPBRN_S, M), partial(VMIN, M)
    M.DEPFIL, M.ELGFIL, M.FRCFIL = partial(DEPFIL_S, M), partial(ELGFIL_S, M), partial(FRCFIL_S, M)
