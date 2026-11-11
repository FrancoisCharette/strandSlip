"""The compliance model's nonlinear system, line by line: COMP (page 53), APPROX (49),
APPSIN (51), VECB (102), JACOB (79), NEWTON (88) and UNRES (100).

The unknowns, in the order of the Jacobian's columns: BETAG(1..N-1), ETAG(1..N-1),
BETAD(1..N-1), ETAD(1..N-1), XK(1..NPOINT), XB1, XB2, BTM, ETM, with N = NPORTION.
"""

from __future__ import annotations

import math

from legacyReference.literalThesisFunctions import DEPH, DR2H, F1D, F1E, F2D, F2E
from legacyReference.literalThesisMachine import Machine, rpow
from legacyReference.literalThesisNumerics import DLUBKSB, DLUDCMP

CONVERGENCE = (
    "///,1X,'!!!PROBLEME DE CONVERGENCE, ',/,1X,'Veuillez recommencer avec une nouvelle approx.',/"
)


def COMP(M: Machine, NPORTION: int) -> None:
    M.XCOMP[1] = 0.0
    M.YCOMP[1] = 0.0
    PORTION = 1.0 / NPORTION
    for I in range(1, NPORTION + 1):
        M.YCOMP[I + 1] = M.YCOMP[I] + PORTION
        if I == NPORTION:
            M.YCOMP[I + 1] = 1.0
    for I in range(1, NPORTION + 1):
        M.YCOMP[I + 1] = (M.YCOMP[I + 1] + (1.5 * I - 1.0)) / (1.5 * I)
        M.XCOMP[I + 1] = (3.0 / 2.0) * (1.0 - rpow(1.0 - M.YCOMP[I + 1], M.EN))
        M.ZETA[I] = (M.XCOMP[I + 1] - M.XCOMP[I]) / (M.YCOMP[I + 1] - M.YCOMP[I])


def transitionGuesses(M: Machine, XK, XB1C, NPORTEMP) -> None:
    """The DO loop APPROX and APPSIN end with."""
    for I in range(1, M.NPOINT // 2 + 1):
        JPOINT = M.NPOINT - (I - 1)
        XKTEMP = (M.XCOMP[I + 1] / M.XCOMP[NPORTEMP + 1]) * XB1C
        XK[I] = XKTEMP + M.XINF
        XK[JPOINT] = M.XSUP - XKTEMP


def APPROX(M: Machine, XK):
    NPORTEMP = M.NPORTION
    if M.NPORTION == 11:
        NPORTEMP = M.NPORTION - 1
    ZETAPRIME = M.XCOMP[NPORTEMP] / M.YCOMP[NPORTEMP]
    XB1A = (M.GAM1 * ZETAPRIME + 1.0) / M.GAME1
    XB1B = -M.YCOMP[NPORTEMP]
    XB1C = (math.acos(XB1A * XB1B) - M.PI / 2.0) / (2.0 * M.PI)
    if M.ICONVERG == 1:
        M.ICONVERG = 0
        M.write(
            "3X,'Valeur approximative de XB1C qui a ete ','essayee =',D16.8,/,"
            "3X,'Veuillez en rentrer une autre',' (devrait probablement etre inferieur)'",
            XB1C,
        )
        M.write("/,3X,'Entrez la nouvelle approximation de XB1C:',\\")
        XB1C = M.readReal("XB1C")
    XB1 = XB1C + M.XINF
    XB2 = M.XSUP - XB1C
    transitionGuesses(M, XK, XB1C, NPORTEMP)
    return XB1, XB2


def APPSIN(M: Machine, XK):
    NPORTEMP = M.NPORTION
    if M.NPORTION == 11:
        NPORTEMP = M.NPORTION - 1
    V1 = (2.0 * M.PI) / M.WLBAR
    VDEN = abs(-(M.ABAR * math.sin(V1 * M.XSUP)))
    if M.XINF < 1:  # IF(XINF.LT.0001): 0001 is the INTEGER constant 1
        RHOBINF = 1.0
    else:
        VDENINF = abs(-(M.ABAR * math.sin(V1 * M.XINF)))
        RHOBINF = 1.0 / VDENINF
    RHOB = 1.0 / VDEN  # 900
    ZETAPRIME = M.XCOMP[NPORTEMP] / M.YCOMP[NPORTEMP]
    XB1A = RHOB * (M.GAM1 * ZETAPRIME + 1.0)
    XB1B = -M.YCOMP[NPORTEMP]
    XB1C = (math.acos(XB1A * XB1B) - M.PI / 2.0) / (2.0 * M.PI)
    if M.ICONVERG == 1:
        M.ICONVERG = 0
        M.write(
            "3X,'Valeur approximative de XB1C qui a été ','essayée =',D16.8,/,"
            "3X,'Veuillez en rentrer une autre',' (devrait probablement être inférieur)'",
            XB1C,
        )
        M.write("/,3X,'Entrez la nouvelle approximation de XB1C:',\\")  # 100
        XB1C = M.readReal("XB1C")
    XB1 = XB1C + M.XINF
    XB2 = M.XSUP - (XB1C * (RHOB / RHOBINF))
    transitionGuesses(M, XK, XB1C, NPORTEMP)
    return XB1, XB2


def VECB(M: Machine, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, B) -> None:
    X, Y, Z = M.XCOMP, M.YCOMP, M.ZETA
    N, JDIM, NPOINT = M.NPORTION, M.JDIM, M.NPOINT
    C = 2.0 * M.ICOTE * (M.GAM1 / (4.0 * M.PI))  # written out in each B(J) below
    for I in range(1, JDIM + 1):
        B[I] = 0.0
    B[1] = -(M.DEPAME(M.XINF) - M.DEPFIL(X[1], Y[1], Z[1], BETAG[1], ETAG[1], M.XINF))  # 3.51
    B[2] = -(M.DEPAME(M.XSUP) - M.DEPFIL(X[1], Y[1], Z[1], BETAD[1], ETAD[1], M.XSUP))  # 3.52
    J = 2
    if N >= 3:
        IPOINT = 0
        for I in range(1, N - 1):
            J = J + 1
            IPOINT = IPOINT + 1
            XKP = XK[IPOINT]
            B[J] = -(
                M.DEPFIL(X[I], Y[I], Z[I], BETAG[I], ETAG[I], XKP)
                - M.DEPFIL(X[I + 1], Y[I + 1], Z[I + 1], BETAG[I + 1], ETAG[I + 1], XKP)
            )  # 3.36
            J = J + 1
            B[J] = -(
                M.ELGFIL(Z[I], BETAG[I], ETAG[I], XKP)
                - M.ELGFIL(Z[I + 1], BETAG[I + 1], ETAG[I + 1], XKP)
            )  # 3.37
            J = J + 1
            B[J] = -(
                M.DEPAME(XKP) - M.DEPFIL(X[I], Y[I], Z[I], BETAG[I], ETAG[I], XKP) + C * X[I + 1]
            )  # 3.38
        IPOINT = 0
        for I in range(1, N - 1):
            J = J + 1
            IPOINT = IPOINT + 1
            JPOINT = NPOINT - (IPOINT - 1)
            XKP = XK[JPOINT]
            B[J] = -(
                M.DEPFIL(X[I], Y[I], Z[I], BETAD[I], ETAD[I], XKP)
                - M.DEPFIL(X[I + 1], Y[I + 1], Z[I + 1], BETAD[I + 1], ETAD[I + 1], XKP)
            )
            J = J + 1
            B[J] = -(
                M.ELGFIL(Z[I], BETAD[I], ETAD[I], XKP)
                - M.ELGFIL(Z[I + 1], BETAD[I + 1], ETAD[I + 1], XKP)
            )
            J = J + 1
            B[J] = -(
                M.DEPAME(XKP) - M.DEPFIL(X[I], Y[I], Z[I], BETAD[I], ETAD[I], XKP) + C * X[I + 1]
            )
    L = N - 1  # 920
    left = (X[L], Y[L], Z[L], BETAG[L], ETAG[L])
    right = (X[L], Y[L], Z[L], BETAD[L], ETAD[L])
    if N != 11:  # micro-slip in the central region (3.39-3.44)
        B[JDIM - 5] = -(M.DEPFIL(*left, XB1) - M.DEPFIL(X[N], Y[N], Z[N], BTM, ETM, XB1))
        B[JDIM - 4] = -(M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1) - M.ELGFIL(Z[N], BTM, ETM, XB1))
        B[JDIM - 3] = -(M.DEPAME(XB1) - M.DEPFIL(*left, XB1) + C * X[N])
        B[JDIM - 2] = -(M.DEPFIL(*right, XB2) - M.DEPFIL(X[N], Y[N], Z[N], BTM, ETM, XB2))
        B[JDIM - 1] = -(M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2) - M.ELGFIL(Z[N], BTM, ETM, XB2))
        B[JDIM] = -(M.DEPAME(XB2) - M.DEPFIL(*right, XB2) + C * X[N])
        return
    B[JDIM - 5] = -(M.DEPFIL(*left, XB1) - DEPH(M, XB1, XB1, BTM, ETM))  # 900: 3.45-3.50
    B[JDIM - 4] = -(M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1) - DR2H(M, XB1, XB1, BTM))
    B[JDIM - 3] = -(M.DEPAME(XB1) - M.DEPFIL(*left, XB1) + C * X[N])
    B[JDIM - 2] = -(M.DEPFIL(*right, XB2) - DEPH(M, XB2, XB1, BTM, ETM))
    B[JDIM - 1] = -(M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2) - DR2H(M, XB2, XB1, BTM))
    B[JDIM] = -(M.DEPAME(XB2) - M.DEPFIL(*right, XB2) + C * X[N])


def JACOB(M: Machine, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, A) -> None:
    Z = M.ZETA
    N, JDIM, NPOINT = M.NPORTION, M.JDIM, M.NPOINT
    for I in range(1, JDIM + 1):
        for J in range(1, JDIM + 1):
            A[I][J] = 0.0
    I = 1
    J = 1
    A[I][J] = -F1D(M, M.XINF, Z[1])
    A[I][J + N - 1] = -F2D(M, M.XINF, Z[1])
    I = I + 1
    J = 2 * (N - 1) + 1
    A[I][J] = -F1D(M, M.XSUP, Z[1])
    A[I][J + N - 1] = -F2D(M, M.XSUP, Z[1])
    if N >= 3:
        for right in (False, True):  # the 700 loop (left side), then the 600 loop (right)
            BET, ETA = (BETAD, ETAD) if right else (BETAG, ETAG)
            IPOINT = 0
            IPOR = -1
            while True:
                IPOINT = IPOINT + 1
                POINT = NPOINT - (IPOINT - 1) if right else IPOINT
                IPOR = IPOR + 1
                FIRST = IPOR + 2 * (N - 1) if right else IPOR
                for F1, F2, DERIVED in ((F1D, F2D, M.ELGFIL), (F1E, F2E, M.FRCFIL)):
                    J = FIRST  # 710 / 720 (610 / 620)
                    IPORTION = IPOR
                    INF = 0
                    I = I + 1
                    while True:
                        J = J + 1
                        INF = INF + 1
                        IPORTION = IPORTION + 1
                        ISIGNE = 1 if INF == 1 else -1
                        A[I][J] = ISIGNE * F1(M, XK[POINT], Z[IPORTION])
                        A[I][J + N - 1] = ISIGNE * F2(M, XK[POINT], Z[IPORTION])
                        if not INF < 2:
                            break
                    A[I][POINT + 4 * (N - 1)] = DERIVED(
                        Z[IPOINT], BET[IPOINT], ETA[IPOINT], XK[POINT]
                    ) - DERIVED(Z[IPOINT + 1], BET[IPOINT + 1], ETA[IPOINT + 1], XK[POINT])
                J = FIRST
                IPORTION = IPOR
                I = I + 1
                J = J + 1
                IPORTION = IPORTION + 1
                A[I][J] = -F1D(M, XK[POINT], Z[IPORTION])
                A[I][J + N - 1] = -F2D(M, XK[POINT], Z[IPORTION])
                A[I][POINT + 4 * (N - 1)] = M.ELGAME(XK[POINT]) - M.ELGFIL(
                    Z[IPORTION], BET[IPORTION], ETA[IPORTION], XK[POINT]
                )
                if not IPOR < (N - 3):
                    break
    L = N - 1  # 900
    if N != 11:
        I = I + 1
        A[I][L] = F1D(M, XB1, Z[L])
        A[I][2 * L] = F2D(M, XB1, Z[L])
        A[I][JDIM - 3] = M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1) - M.ELGFIL(Z[N], BTM, ETM, XB1)
        A[I][JDIM - 1] = -F1D(M, XB1, Z[N])
        A[I][JDIM] = -F2D(M, XB1, Z[N])
        I = I + 1
        A[I][L] = F1E(M, XB1, Z[L])
        A[I][2 * L] = F2E(M, XB1, Z[L])
        A[I][JDIM - 3] = M.FRCFIL(Z[L], BETAG[L], ETAG[L], XB1) - M.FRCFIL(Z[N], BTM, ETM, XB1)
        A[I][JDIM - 1] = -F1E(M, XB1, Z[N])
        A[I][JDIM] = -F2E(M, XB1, Z[N])
        I = I + 1
        A[I][L] = -F1D(M, XB1, Z[L])
        A[I][2 * L] = -F2D(M, XB1, Z[L])
        A[I][JDIM - 3] = M.ELGAME(XB1) - M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1)
        I = I + 1
        A[I][3 * L] = F1D(M, XB2, Z[L])
        A[I][4 * L] = F2D(M, XB2, Z[L])
        A[I][JDIM - 2] = M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2) - M.ELGFIL(Z[N], BTM, ETM, XB2)
        A[I][JDIM - 1] = -F1D(M, XB2, Z[N])
        A[I][JDIM] = -F2D(M, XB2, Z[N])
        I = I + 1
        A[I][3 * L] = F1E(M, XB2, Z[L])
        A[I][4 * L] = F2E(M, XB2, Z[L])
        A[I][JDIM - 2] = M.FRCFIL(Z[L], BETAD[L], ETAD[L], XB2) - M.FRCFIL(Z[N], BTM, ETM, XB2)
        A[I][JDIM - 1] = -F1E(M, XB2, Z[N])
        A[I][JDIM] = -F2E(M, XB2, Z[N])
        I = I + 1
        A[I][3 * L] = -F1D(M, XB2, Z[L])
        A[I][4 * L] = -F2D(M, XB2, Z[L])
        A[I][JDIM - 2] = M.ELGAME(XB2) - M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2)
        return
    I = I + 1  # 950: the central region slips (macro-slip)
    A[I][L] = F1D(M, XB1, Z[L])
    A[I][2 * L] = F2D(M, XB1, Z[L])
    A[I][JDIM - 3] = M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1)
    A[I][JDIM] = -1.0
    I = I + 1
    A[I][L] = F1E(M, XB1, Z[L])
    A[I][2 * L] = F2E(M, XB1, Z[L])
    A[I][JDIM - 3] = M.FRCFIL(Z[L], BETAG[L], ETAG[L], XB1)
    A[I][JDIM - 1] = -1.0
    I = I + 1
    A[I][L] = -F1D(M, XB1, Z[L])
    A[I][2 * L] = -F2D(M, XB1, Z[L])
    A[I][JDIM - 3] = M.ELGAME(XB1) - M.ELGFIL(Z[L], BETAG[L], ETAG[L], XB1)
    I = I + 1
    A[I][3 * L] = F1D(M, XB2, Z[L])
    A[I][4 * L] = F2D(M, XB2, Z[L])
    A[I][JDIM - 3] = M.ICOTE * (2.0 * M.PI) * (XB2 - XB1) + BTM
    A[I][JDIM - 2] = M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2) - DR2H(M, XB2, XB1, BTM)
    A[I][JDIM - 1] = -(XB2 - XB1)
    A[I][JDIM] = -1.0
    I = I + 1
    A[I][3 * L] = F1E(M, XB2, Z[L])
    A[I][4 * L] = F2E(M, XB2, Z[L])
    A[I][JDIM - 3] = M.ICOTE * 2.0 * M.PI
    A[I][JDIM - 2] = M.FRCFIL(Z[L], BETAD[L], ETAD[L], XB2) - M.ICOTE * 2.0 * M.PI
    A[I][JDIM - 1] = -1.0
    I = I + 1
    A[I][3 * L] = -F1D(M, XB2, Z[L])
    A[I][4 * L] = -F2D(M, XB2, Z[L])
    A[I][JDIM - 2] = M.ELGAME(XB2) - M.ELGFIL(Z[L], BETAD[L], ETAD[L], XB2)


def NEWTON(M: Machine, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, A, B):
    """Returns XB1, XB2, BTM, ETM; the arrays are updated in place."""
    JMAX = 62
    INDX = [0] * (JMAX + 1)
    N, JDIM, NPOINT = M.NPORTION, M.JDIM, M.NPOINT
    for I in range(1, JDIM + 1):
        B[I] = 0.0
    K = 0
    TOL = 1.0e-10
    IERROR = 0
    while True:  # 1000
        for I in range(1, N):
            BETAG[I] = BETAG[I] + B[I]
            ETAG[I] = ETAG[I] + B[I + N - 1]
            BETAD[I] = BETAD[I] + B[I + 2 * (N - 1)]
            ETAD[I] = ETAD[I] + B[I + 3 * (N - 1)]
        for I in range(1, NPOINT + 1):  # (IF(NPORTION.LT.2) GOTO 910 never jumps)
            XK[I] = XK[I] + B[I + 4 * (N - 1)]
            if XK[I] < 0.0:
                IERROR = 1
                break  # GOTO 750
        if IERROR == 0:
            XB1 = XB1 + B[JDIM - 3]  # 910
            XB2 = XB2 + B[JDIM - 2]
            BTM = BTM + B[JDIM - 1]
            ETM = ETM + B[JDIM]
            VECB(M, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, B)
            JACOB(M, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, A)
            DLUDCMP(M, A, JDIM, JMAX, INDX)
            DLUBKSB(A, JDIM, JMAX, INDX, B)
            C1 = XB1 - M.XINF
            C2 = M.XSUP - XB2
            C3 = M.XSUP - XB1
            C4 = XB2 - M.XINF
            if C1 < 0 or C2 < 0 or C3 < 0 or C4 < 0 or XB1 > XB2 or K == 14:
                M.write(CONVERGENCE)
                M.ICONVERG = 1
                return XB1, XB2, BTM, ETM
        for I in range(1, NPOINT // 2 + 1):  # 750
            JPOINT = NPOINT - (I - 1)
            CR1 = XK[I] - M.XINF
            CR2 = M.XSUP - XK[JPOINT]
            CR3 = M.XSUP - XK[JPOINT]
            CR4 = XK[JPOINT] - M.XINF
            if (
                CR1 < 0 or CR2 < 0 or CR3 < 0 or CR4 < 0
                or XK[I] > XK[JPOINT] or IERROR == 1
            ):  # fmt: skip
                M.write(CONVERGENCE)
                M.ICONVERG = 1
                IERROR = 0
                return XB1, XB2, BTM, ETM
        M.write("/,3X,'Iteration #',I2", K)
        M.write("1X,'XB1='D16.8,5X,'XB2=',D16.8", XB1, XB2)
        for I in range(1, NPOINT // 2 + 1):
            JPOINT = NPOINT - (I - 1)
            M.write("1X,'XK(',I2,')=',D16.8,5X,'XK(',I2,')=',D16.8", I, XK[I], JPOINT, XK[JPOINT])
        M.write("/,1X,'XB1-XINF='D14.8,4X,'XSUP-XB2=',D14.8", XB1 - M.XINF, M.XSUP - XB2)
        for I in range(1, NPOINT // 2 + 1):
            JPOINT = NPOINT - (I - 1)
            M.write(
                "1X,'XK(',I2,')-XINF=',D14.8,4X,'XSUP-XK(',I2,')=',D14.8",
                I, XK[I] - M.XINF, JPOINT, M.XSUP - XK[JPOINT],
            )  # fmt: skip
        if not notConverged(
            B, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, N, NPOINT, JDIM, K, TOL
        ):
            return XB1, XB2, BTM, ETM  # 990
        K = K + 1  # 980
        if K > 15:
            return XB1, XB2, BTM, ETM


def notConverged(
    B, BETAG, ETAG, BETAD, ETAD, XK, XB1, XB2, BTM, ETM, N, NPOINT, JDIM, K, TOL
) -> bool:
    """The tolerance block: True where the listing says GOTO 980."""
    if K == 0:
        return True
    for I in range(1, N):
        if abs(B[I] / BETAG[I]) >= TOL:
            return True
        if abs(B[I + N - 1] / ETAG[I]) >= TOL:
            return True
        if abs(B[I + 2 * (N - 1)] / BETAD[I]) >= TOL:
            return True
        if abs(B[I + 3 * (N - 1)] / ETAD[I]) >= TOL:
            return True
    for I in range(1, NPOINT + 1):
        if abs(B[I + 4 * (N - 1)] / XK[I]) >= TOL:
            return True
    return (
        abs(B[JDIM - 3] / XB1) >= TOL
        or abs(B[JDIM - 2] / XB2) >= TOL
        or abs(B[JDIM - 1] / BTM) >= TOL
        or abs(B[JDIM] / ETM) >= TOL
    )


def UNRES(M: Machine, A, B):
    """Returns BTM, ETM for a half-pitch that is one micro-slip region."""
    JMAX = 62
    INDX = [0] * (JMAX + 1)
    JDIM = 2
    X, Y, Z = M.XCOMP, M.YCOMP, M.ZETA
    A[1][1] = F1D(M, M.XINF, Z[1])
    A[1][2] = F2D(M, M.XINF, Z[1])
    A[2][1] = F1D(M, M.XSUP, Z[1])
    A[2][2] = F2D(M, M.XSUP, Z[1])
    B[1] = M.DEPAME(M.XINF) - M.DEPFIL(X[1], Y[1], Z[1], X[1], Y[1], M.XINF)
    B[2] = M.DEPAME(M.XSUP) - M.DEPFIL(X[1], Y[1], Z[1], X[1], Y[1], M.XSUP)
    DLUDCMP(M, A, JDIM, JMAX, INDX)
    DLUBKSB(A, JDIM, JMAX, INDX, B)
    return B[1], B[2]
