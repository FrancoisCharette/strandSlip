"""Line-by-line Python transcriptions of the 1990 Fortran programs.

An oracle for the vectorized services: scalar `math`, one wire at a time, the
GOTO loops as while loops, every expression in source order, variables named
as in the .FOR files. Nothing here is shared with the application code.
"""

from __future__ import annotations

import math
import struct


def real4(value: float) -> float:
    """Store into a REAL*4 variable (GAM is one: G is outside IMPLICIT D.P.)."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


def ipow(x: float, n: int) -> float:
    """X**N for an integer N: the compiler multiplied, it did not call pow()."""
    result = x
    for _ in range(n - 1):
        result = result * x
    return result


def _thetas(NFIL: int, PI: float) -> list[float]:
    THETA = [0.0] * (NFIL + 1)  # 1-based like the Fortran
    THETA[1] = 0
    for I in range(2, NFIL + 1):
        M = I - 1
        THETA[I] = THETA[M] + (2 * PI) / NFIL
    return THETA


def sinus(CL, NFIL, ALPHA, RF, EF, TI, RA, EA, CPN, CFL, WL, AMP, NPAS, XDEPART, XFINAL,
          divisor=1000, trace=None):
    """SINUS.FOR; BSINUS.FOR is the same with RT/ET/RN/EN; NSINUS.FOR uses divisor 10000."""
    PI = math.acos(-1.0)
    THETA = _thetas(NFIL, PI)
    DXPAS = CL / NPAS
    X = XDEPART
    F = (1 - CPN * ipow(math.tan(ALPHA), 2)) * ipow(math.cos(ALPHA), 2)
    PITCH = (2 * PI * RA) / math.tan(ALPHA)
    AF = PI * ipow(RF, 2)
    Q = (TI * ipow(math.sin(ALPHA), 2)) / RA
    AMPC = (ipow(WL / (2 * PI), 2) * TI * math.sin(ALPHA) * CFL) / (RA * F * EF * AF)
    AMPR = AMP / AMPC
    GAM = real4((TI * math.sin(ALPHA) * CFL) / (EF * AF))
    CST9 = ((RA * AMP * F * EF * AF * math.cos(ALPHA)) / Q) * ipow((2 * PI) / WL, 3)
    DX = 0.0  # never assigned unless some CFX < 0 or > CFL; static storage reads zero

    def cfx(XX, TH):
        CA = (WL / PITCH) * (math.cos((2 * PI * XX) / PITCH + TH)) * (math.sin((2 * PI * XX) / WL))
        CB = (math.sin((2 * PI * XX) / PITCH + TH)) * (math.cos((2 * PI * XX) / WL))
        return CST9 * (CA + CB)

    def deplacement(XB, TH):
        CST19 = (AMPR * GAM * WL * PITCH) / (4 * PI * math.cos(ALPHA))
        CA = (math.sin(2 * PI * XB * (1 / PITCH - 1 / WL) + TH) - math.sin(TH)) / (WL - PITCH)
        CB = (math.sin(2 * PI * XB * (1 / PITCH + 1 / WL) + TH) - math.sin(TH)) / (WL + PITCH)
        return CST19 * (CA - CB)

    rows = []
    while True:  # 370
        FX, FY, FZ = [0.0] * (NFIL + 1), [0.0] * (NFIL + 1), [0.0] * (NFIL + 1)
        FMXZ, FMXY, TMX = [0.0] * (NFIL + 1), [0.0] * (NFIL + 1), [0.0] * (NFIL + 1)
        for I in range(1, NFIL + 1):
            TH = THETA[I]
            CFX = cfx(X, TH)
            if CFX < 0:  # GOTO 300
                DX = PITCH / divisor
                CFLN = 0 - CFL
                if CFX >= CFLN:
                    EX = AMPR * GAM * math.sin((2 * PI * X) / PITCH + TH) * math.sin((2 * PI * X) / WL)
                    if trace is not None:
                        trace.append(("stickBelow", X, I, EX))
                else:
                    X2 = X
                    while True:  # 350
                        X2 = X2 + DX
                        if not (cfx(X2, TH) < CFLN):
                            break
                    X1 = X
                    while True:  # 360
                        X1 = X1 - DX
                        if not (cfx(X1, TH) < CFLN):
                            break
                    DX1 = deplacement(X1, TH)
                    DX2 = deplacement(X2, TH)
                    EOG = (math.cos(ALPHA) * (DX2 - DX1)) / (X2 - X1) + (GAM * PI * (X2 - X1)) / PITCH
                    EX = (Q * CFLN * (X - X1)) / (math.cos(ALPHA) * EF * AF) + EOG
                    if trace is not None:
                        trace.append(("slipBelow", X, I, X1, X2, DX1, DX2, EX))
            elif CFX <= CFL:
                EX = AMPR * GAM * math.sin((2 * PI * X) / PITCH + TH) * math.sin((2 * PI * X) / WL)
                if trace is not None:
                    trace.append(("stickAbove", X, I, EX))
            else:
                DX = PITCH / divisor
                X4 = X
                while True:  # 320
                    X4 = X4 + DX
                    if not (cfx(X4, TH) > CFL):
                        break
                X3 = X
                while True:  # 330
                    X3 = X3 - DX
                    if not (cfx(X3, TH) > CFL):
                        break
                DX3 = deplacement(X3, TH)
                DX4 = deplacement(X4, TH)
                EOD = (math.cos(ALPHA) * (DX4 - DX3)) / (X4 - X3) - (GAM * PI * (X4 - X3)) / PITCH
                EX = (Q * CFL * (X - X3)) / (math.cos(ALPHA) * EF * AF) + EOD
                if trace is not None:
                    trace.append(("slipAbove", X, I, X3, X4, DX3, DX4, EX))
            # 310
            FYZ = EX * EF * AF * math.sin(ALPHA)
            FX[I] = EX * EF * AF * math.cos(ALPHA)
            FY[I] = FYZ * math.cos((2 * PI * X) / PITCH + TH)
            FZ[I] = FYZ * math.sin((2 * PI * X) / PITCH + TH)
            FMXZ[I] = FX[I] * RA * math.sin((2 * PI * X) / PITCH + TH)
            FMXY[I] = FX[I] * RA * math.cos((2 * PI * X) / PITCH + TH)
            TMX[I] = FYZ * RA
        FXT = FYT = FZT = FMXZT = FMXYT = TMXT = 0.0
        for I in range(1, NFIL + 1):
            FXT = FXT + FX[I]
            FYT = FYT + FY[I]
            FZT = FZT + FZ[I]
            FMXZT = FMXZT + FMXZ[I]
            FMXYT = FMXYT + FMXY[I]
            TMXT = TMXT + TMX[I]
        if X != 0.0:  # IF(X.EQ.O) GOTO 125
            RIG = (FMXZT * ipow(WL / (2 * PI), 2)) / (AMP * math.sin((2 * PI * X) / WL))
            rows.append((X, RIG, TMXT, FMXYT, FMXZT, FXT, FYT, FZT))
        if X < XFINAL:  # 125
            X = X + DXPAS
        else:
            break
    info = dict(F=F, PITCH=PITCH, AF=AF, Q=Q, AMPC=AMPC, AMPR=AMPR, GAM=GAM, CST9=CST9,
                DXPAS=DXPAS, DX=DX)
    return rows, info


def rayon(CL, NFIL, ALPHA, RF, EF, TI, RA, EA, CPN, CFL, RIEN, RHO, NPAS, XDEPART, XFINAL):
    """RAYON.FOR"""
    PI = math.acos(-1.0)
    THETA = _thetas(NFIL, PI)
    DXPAS = CL / NPAS
    X = XDEPART
    F = (1 - CPN * ipow(math.tan(ALPHA), 2)) * ipow(math.cos(ALPHA), 2)
    PITCH = (2 * PI * RA) / math.tan(ALPHA)
    AF = PI * ipow(RF, 2)
    Q = (TI * ipow(math.sin(ALPHA), 2)) / RA
    RHOC = (RA * F * EF * AF) / (TI * math.sin(ALPHA) * CFL)
    RHOR = RHO / RHOC
    GAM = real4((TI * math.sin(ALPHA) * CFL) / (EF * AF))
    CST9 = (RA * F * EF * AF * math.cos(ALPHA) * 2 * PI) / (Q * RHO * PITCH)
    DX = 0.0
    rows = []
    while True:  # 370
        FX, FY, FZ = [0.0] * (NFIL + 1), [0.0] * (NFIL + 1), [0.0] * (NFIL + 1)
        FMXZ, FMXY, TMX = [0.0] * (NFIL + 1), [0.0] * (NFIL + 1), [0.0] * (NFIL + 1)
        for I in range(1, NFIL + 1):
            TH = THETA[I]
            CFX = CST9 * math.cos((2 * PI * X) / PITCH + TH)
            if CFX < 0:
                DX = PITCH / 1000
                CFLN = 0 - CFL
                if CFX >= CFLN:
                    EX = (GAM / RHOR) * math.sin((2 * PI * X) / PITCH + TH)
                else:
                    X2 = X
                    while True:
                        X2 = X2 + DX
                        if not (CST9 * math.cos((2 * PI * X2) / PITCH + TH) < CFLN):
                            break
                    X1 = X
                    while True:
                        X1 = X1 - DX
                        if not (CST9 * math.cos((2 * PI * X1) / PITCH + TH) < CFLN):
                            break
                    CST19 = (GAM * PITCH) / (2 * PI * math.cos(ALPHA) * RHOR)
                    DX1 = CST19 * (math.cos(TH) - math.cos((2 * PI * X1) / PITCH + TH))
                    DX2 = CST19 * (math.cos(TH) - math.cos((2 * PI * X2) / PITCH + TH))
                    EOG = (math.cos(ALPHA) * (DX2 - DX1)) / (X2 - X1) + (GAM * PI * (X2 - X1)) / PITCH
                    EX = (Q * CFLN * (X - X1)) / (math.cos(ALPHA) * EF * AF) + EOG
            elif CFX <= CFL:
                EX = (GAM / RHOR) * math.sin((2 * PI * X) / PITCH + TH)
            else:
                DX = PITCH / 1000
                X4 = X
                while True:
                    X4 = X4 + DX
                    if not (CST9 * math.cos((2 * PI * X4) / PITCH + TH) > CFL):
                        break
                X3 = X
                while True:
                    X3 = X3 - DX
                    if not (CST9 * math.cos((2 * PI * X3) / PITCH + TH) > CFL):
                        break
                CST19 = (GAM * PITCH) / (2 * PI * math.cos(ALPHA) * RHOR)
                DX3 = CST19 * (math.cos(TH) - math.cos((2 * PI * X3) / PITCH + TH))
                DX4 = CST19 * (math.cos(TH) - math.cos((2 * PI * X4) / PITCH + TH))
                EOD = (math.cos(ALPHA) * (DX4 - DX3)) / (X4 - X3) - (GAM * PI * (X4 - X3)) / PITCH
                EX = (Q * CFL * (X - X3)) / (math.cos(ALPHA) * EF * AF) + EOD
            FYZ = EX * EF * AF * math.sin(ALPHA)
            FX[I] = EX * EF * AF * math.cos(ALPHA)
            FY[I] = FYZ * math.cos((2 * PI * X) / PITCH + TH)
            FZ[I] = FYZ * math.sin((2 * PI * X) / PITCH + TH)
            FMXZ[I] = FX[I] * RA * math.sin((2 * PI * X) / PITCH + TH)
            FMXY[I] = FX[I] * RA * math.cos((2 * PI * X) / PITCH + TH)
            TMX[I] = FYZ * RA
        FXT = FYT = FZT = FMXZT = FMXYT = TMXT = 0.0
        for I in range(1, NFIL + 1):
            FXT = FXT + FX[I]
            FYT = FYT + FY[I]
            FZT = FZT + FZ[I]
            FMXZT = FMXZT + FMXZ[I]
            FMXYT = FMXYT + FMXY[I]
            TMXT = TMXT + TMX[I]
        if X != 0.0:
            RIG = FMXZT * RHO
            rows.append((X, RIG, TMXT, FMXYT, FMXZT, FXT, FYT, FZT))
        if X < XFINAL:
            X = X + DXPAS
        else:
            break
    info = dict(F=F, PITCH=PITCH, AF=AF, Q=Q, RHOC=RHOC, RHOR=RHOR, GAM=GAM, CST9=CST9,
                DXPAS=DXPAS, DX=DX)
    return rows, info


def friction(CL, NFIL, ALPHA, RT, ET, TI, RN, EN, CPN, CFL, WL, AMP, NPAS, XDEPART, XFINAL):
    """FRICTION.FOR"""
    PI = math.acos(-1.0)
    THETA = _thetas(NFIL, PI)
    DXPAS = CL / NPAS
    X = XDEPART
    F = (1 - CPN * ipow(math.tan(ALPHA), 2)) * ipow(math.cos(ALPHA), 2)
    PITCH = (2 * PI * RN) / math.tan(ALPHA)
    AT = PI * ipow(RT, 2)
    Q = (TI * ipow(math.sin(ALPHA), 2)) / RN
    CST9 = ((RN * AMP * F * ET * AT * math.cos(ALPHA)) / Q) * ipow((2 * PI) / WL, 3)
    rows = []
    while True:  # 119
        for I in range(1, NFIL + 1):
            CA9 = (WL / PITCH) * (math.cos((2 * PI * X) / PITCH + THETA[I])) * (math.sin((2 * PI * X) / WL))
            CB9 = (math.sin((2 * PI * X) / PITCH + THETA[I])) * (math.cos((2 * PI * X) / WL))
            CFX = CST9 * (CA9 + CB9)
            rows.append((X, CFX, I))
        X = X + DXPAS
        if not (X < XFINAL):
            break
    info = dict(F=F, PITCH=PITCH, AT=AT, Q=Q, CST9=CST9, DXPAS=DXPAS)
    return rows, info


def deplace(CL, NFIL, ALPHA, RT, ET, TI, RN, EN, CPN, CFL, WL, AMP, NPAS, XDEPART, XFINAL):
    """DEPLACE.FOR"""
    PI = math.acos(-1.0)
    THETA = _thetas(NFIL, PI)
    DXPAS = CL / NPAS
    X = XDEPART
    F = (1 - CPN * ipow(math.tan(ALPHA), 2)) * ipow(math.cos(ALPHA), 2)
    PITCH = (2 * PI * RN) / math.tan(ALPHA)
    AT = PI * ipow(RT, 2)
    AMPC = (ipow(WL / (2 * PI), 2) * TI * math.sin(ALPHA) * CFL) / (RN * F * ET * AT)
    AMPR = AMP / AMPC
    GAM = real4((TI * math.sin(ALPHA) * CFL) / (ET * AT))
    CST19 = (AMPR * GAM * WL * PITCH) / (4 * PI * math.cos(ALPHA))
    rows = []
    while True:  # 200
        for I in range(1, NFIL + 1):
            CA19 = (math.sin(2 * PI * X * (1 / PITCH - 1 / WL) + THETA[I]) - math.sin(THETA[I])) / (WL - PITCH)
            CB19 = (math.sin(2 * PI * X * (1 / PITCH + 1 / WL) + THETA[I]) - math.sin(THETA[I])) / (WL + PITCH)
            DX = CST19 * (CA19 - CB19) * 10000
            rows.append((X, DX, I, CA19, CB19))
        X = X + DXPAS
        if not (X < XFINAL):
            break
    info = dict(F=F, PITCH=PITCH, AT=AT, AMPC=AMPC, AMPR=AMPR, GAM=GAM, CST19=CST19, DXPAS=DXPAS)
    return rows, info
