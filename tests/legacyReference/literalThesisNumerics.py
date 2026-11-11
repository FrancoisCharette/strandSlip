"""QROMB, TRAPZD, POLINT, RTSEC, RTFLSP, GOLDEN, DLUDCMP and DLUBKSB, line by line.

Numerical Recipes (1986) routines as the 1992 listings print them (manual
pages 93, 99, 92, 116, 115, 114, 58, 57), with their departures from the book:
EPS, R, C and TINY are REAL*4 constants stored in DOUBLE PRECISION names,
DLUBKSB sets II=1 where the book has II=I, and POLINT receives the REAL*4
constant 0. for its DOUBLE PRECISION X (read here as 0).

Arrays are 1-based Python lists (element 0 unused); A(I,J) is A[I][J].
"""

from __future__ import annotations

from legacyReference.literalThesisMachine import Machine, real4


def TRAPZD(M: Machine, XCP, YCP, ZT, BT, ET, FUNC, A, B, S, N):
    if N == 1:
        S = 0.5 * (B - A) * (FUNC(XCP, YCP, ZT, BT, ET, A) + FUNC(XCP, YCP, ZT, BT, ET, B))
        M.IT = 1
    else:
        TNM = float(M.IT)
        DEL = (B - A) / TNM
        X = A + 0.5 * DEL
        SUM = 0.0
        for _J in range(1, M.IT + 1):
            SUM = SUM + FUNC(XCP, YCP, ZT, BT, ET, X)
            X = X + DEL
        S = 0.5 * (S + (B - A) * SUM / TNM)
        M.IT = 2 * M.IT
    return S


def POLINT(M: Machine, XA, YA, N, X):
    """XA and YA are 1-based lists; returns (Y, DY)."""
    NNMAX = 10
    C = [0.0] * (NNMAX + 1)
    D = [0.0] * (NNMAX + 1)
    NS = 1
    DIF = abs(X - XA[1])
    for I in range(1, N + 1):
        DIFT = abs(X - XA[I])
        if DIFT < DIF:
            NS = I
            DIF = DIFT
        C[I] = YA[I]
        D[I] = YA[I]
    Y = YA[NS]
    NS = NS - 1
    DY = 0.0
    for MM in range(1, N):
        for I in range(1, N - MM + 1):
            HO = XA[I] - X
            HP = XA[I + MM] - X
            W = C[I + 1] - D[I]
            DEN = HO - HP
            if DEN == 0.0:
                M.pause("Pause")
            DEN = W / DEN
            D[I] = HP * DEN
            C[I] = HO * DEN
        if 2 * NS < N - MM:
            DY = C[NS + 1]
        else:
            DY = D[NS]
            NS = NS - 1
        Y = Y + DY
    return Y, DY


def QROMB(M: Machine, XCP, YCP, ZT, BT, ET, FUNC, A, B):
    """Returns SS."""
    EPS = real4(1.0e-6)
    JJMAX = 20
    KK = 5
    KKM = 4
    S = M.QROMB_S
    H = M.QROMB_H
    SS = float("nan")
    H[1] = 1.0
    for J in range(1, JJMAX + 1):
        S[J] = TRAPZD(M, XCP, YCP, ZT, BT, ET, FUNC, A, B, S[J], J)
        if J >= KK:
            L = J - KKM
            SS, DSS = POLINT(M, [0.0] + H[L : L + KK], [0.0] + S[L : L + KK], KK, 0.0)
            if abs(DSS) < EPS * abs(SS):
                return SS
        S[J + 1] = S[J]
        H[J + 1] = 0.25 * H[J]
    M.pause("Too many steps.")
    return SS


def RTSEC(M: Machine, FUNC, X1, X2, XACC):
    MAXIT = 30
    FL = FUNC(X1)
    F = FUNC(X2)
    if abs(FL) < abs(F):
        RTSEC = X1
        XL = X2
        SWAP = FL
        FL = F
        F = SWAP
    else:
        XL = X1
        RTSEC = X2
    for _J in range(1, MAXIT + 1):
        DX = (XL - RTSEC) * F / (F - FL)
        XL = RTSEC
        FL = F
        RTSEC = RTSEC + DX
        F = FUNC(RTSEC)
        if abs(DX) < XACC or F == 0.0:
            return RTSEC
    M.pause("RTSEC exceed maximum iterations")
    return RTSEC


def RTFLSP(M: Machine, FUNC, X1, X2, XACC):
    MAXIT = 100
    FL = FUNC(X1)
    FH = FUNC(X2)
    if FL * FH > 0.0:
        M.pause("Problème d approximation de la borne (Pressez ENTER)!!!")
        M.ICONVERG = 1
        return float("nan")  # RTFLSP is never assigned on this path
    if FL < 0.0:
        XL = X1
        XH = X2
    else:
        XL = X2
        XH = X1
        SWAP = FL
        FL = FH
        FH = SWAP
    DX = XH - XL
    RTFLSP = float("nan")
    for _J in range(1, MAXIT + 1):
        RTFLSP = XL + DX * FL / (FL - FH)
        F = FUNC(RTFLSP)
        if F < 0.0:
            DEL = XL - RTFLSP
            XL = RTFLSP
            FL = F
        else:
            DEL = XH - RTFLSP
            XH = RTFLSP
            FH = F
        DX = XH - XL
        if abs(DEL) < XACC or F == 0.0:
            return RTFLSP
    return RTFLSP


def GOLDEN(M: Machine, AX, BX, CX, F, TOL):
    """Returns (GOLDEN, XMIN)."""
    R = real4(0.61803399)
    C = real4(0.38196602)
    X0 = AX
    X3 = CX
    if abs(CX - BX) > abs(BX - AX):
        X1 = BX
        X2 = BX + C * (CX - BX)
    else:
        X2 = BX
        X1 = BX - C * (BX - AX)
    F1 = F(X1)
    F2 = F(X2)
    while abs(X3 - X0) > TOL * (abs(X1) + abs(X2)):
        if F2 < F1:
            X0 = X1
            X1 = X2
            X2 = R * X1 + C * X3
            F1 = F2
            F2 = F(X2)
        else:
            X3 = X2
            X2 = X1
            X1 = R * X2 + C * X0
            F2 = F1
            F1 = F(X1)
    if F1 < F2:
        return F1, X1
    return F2, X2


def DLUDCMP(M: Machine, A, N, NP, INDX):
    """Crout LU with implicit pivoting, in place; returns D."""
    NMMAX = 100
    TINY = real4(1.0e-20)
    VV = [0.0] * (NMMAX + 1)
    D = 1.0
    for I in range(1, N + 1):
        AAMAX = 0.0
        for J in range(1, N + 1):
            if abs(A[I][J]) > AAMAX:
                AAMAX = abs(A[I][J])
        if AAMAX == 0.0:
            M.pause("Singular matrix")
        VV[I] = 1.0 / AAMAX
    IMAX = 0
    for J in range(1, N + 1):
        for I in range(1, J):
            SUM = A[I][J]
            for K in range(1, I):
                SUM = SUM - A[I][K] * A[K][J]
            A[I][J] = SUM
        AAMAX = 0.0
        for I in range(J, N + 1):
            SUM = A[I][J]
            for K in range(1, J):
                SUM = SUM - A[I][K] * A[K][J]
            A[I][J] = SUM
            DUM = VV[I] * abs(SUM)
            if DUM >= AAMAX:
                IMAX = I
                AAMAX = DUM
        if J != IMAX:
            for K in range(1, N + 1):
                DUM = A[IMAX][K]
                A[IMAX][K] = A[J][K]
                A[J][K] = DUM
            D = -D
            VV[IMAX] = VV[J]
        INDX[J] = IMAX
        if A[J][J] == 0.0:
            A[J][J] = TINY
        if J != N:
            DUM = 1.0 / A[J][J]
            for I in range(J + 1, N + 1):
                A[I][J] = A[I][J] * DUM
    return D


def DLUBKSB(A, N, NP, INDX, B):
    II = 0
    for I in range(1, N + 1):
        LL = INDX[I]
        SUM = B[LL]
        B[LL] = B[I]
        if II != 0:
            for J in range(II, I):
                SUM = SUM - A[I][J] * B[J]
        elif SUM != 0.0:
            II = 1  # Numerical Recipes: II=I
        B[I] = SUM
    for I in range(N, 0, -1):
        SUM = B[I]
        if I < N:
            for J in range(I + 1, N + 1):
                SUM = SUM - A[I][J] * B[J]
        B[I] = SUM / A[I][I]
