"""The Numerical Recipes routines of the 1992 programs, as their listings have them.

QROMB/TRAPZD/POLINT (Romberg integration), RTSEC (secant), RTFLSP (false
position), GOLDEN (golden-section minimum) and DLUDCMP/DLUBKSB (LU solve), from
Press et al., Numerical Recipes (1986), the way the manual prints them:

- EPS, R, C and TINY are REAL*4 constants held in DOUBLE PRECISION names, so
  they carry single-precision values (`real4`);
- DLUBKSB sets II=1 where the book sets II=I (the extra terms multiply zeros);
- QROMB hands POLINT the REAL*4 constant 0. as its DOUBLE PRECISION X; the
  high half of what the DOS program read cannot be known, and 0 is used.

Every expression keeps the listing's operand order, so results are the same
doubles. A PAUSE becomes a call to `notify`, which writes it to the screen.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Callable

Notify = Callable[[str], None]
Integrand = Callable[[float], float]


def real4(value: float) -> float:
    """A constant written without a D exponent: single precision, widened to double."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


rombergTolerance = real4(1.0e-6)  # QROMB: PARAMETER (EPS=1.E-6)
goldenRatio = real4(0.61803399)  # GOLDEN: PARAMETER (R=.61803399
goldenComplement = real4(0.38196602)  # ...,C=.38196602)
luTiny = real4(1.0e-20)  # DLUDCMP: PARAMETER (TINY=1.0E-20)
rombergLevels = 20  # JJMAX
rombergOrder = 5  # KK


def extrapolateToZero(steps: list[float], sums: list[float], notify: Notify) -> tuple[float, float]:
    """POLINT at X = 0: Neville's polynomial through (steps, sums); returns (Y, DY)."""
    count = len(steps)
    nearest = 0
    gap = abs(0.0 - steps[0])
    upper = list(sums)  # C
    lower = list(sums)  # D
    for index in range(count):
        distance = abs(0.0 - steps[index])
        if distance < gap:
            nearest = index
            gap = distance
    estimate = sums[nearest]
    ns = nearest  # the listing's NS after NS=NS-1, counted from 1
    correction = 0.0
    for order in range(1, count):
        for index in range(count - order):
            ho = steps[index] - 0.0
            hp = steps[index + order] - 0.0
            w = upper[index + 1] - lower[index]
            denominator = ho - hp
            if denominator == 0.0:
                notify("Pause")
            denominator = w / denominator
            lower[index] = hp * denominator
            upper[index] = ho * denominator
        if 2 * ns < count - order:
            correction = upper[ns]
        else:
            correction = lower[ns - 1]
            ns = ns - 1
        estimate = estimate + correction
    return estimate, correction


def romberg(integrand: Integrand, a: float, b: float, notify: Notify) -> float:
    """QROMB with TRAPZD: refine the trapezoid rule, extrapolate the last five sums to h = 0."""
    sums = [0.0] * (rombergLevels + 1)  # S(J), J = index + 1
    steps = [0.0] * (rombergLevels + 1)  # H(J)
    steps[0] = 1.0
    points = 0  # TRAPZD's IT, kept between its calls
    estimate = math.nan
    for level in range(1, rombergLevels + 1):
        index = level - 1
        if level == 1:
            sums[index] = 0.5 * (b - a) * (integrand(a) + integrand(b))
            points = 1
        else:
            count = float(points)
            spacing = (b - a) / count
            x = a + 0.5 * spacing
            total = 0.0
            for _ in range(points):
                total = total + integrand(x)
                x = x + spacing
            sums[index] = 0.5 * (sums[index] + (b - a) * total / count)
            points = 2 * points
        if level >= rombergOrder:
            first = level - rombergOrder
            estimate, error = extrapolateToZero(
                steps[first : first + rombergOrder], sums[first : first + rombergOrder], notify
            )
            if abs(error) < rombergTolerance * abs(estimate):
                return estimate
        sums[index + 1] = sums[index]
        steps[index + 1] = 0.25 * steps[index]
    notify("Too many steps.")
    return estimate


def secantRoot(function: Integrand, x1: float, x2: float, accuracy: float, notify: Notify) -> float:
    """RTSEC: secant iterations from the end with the smaller |f|; 30 at most."""
    fl = function(x1)
    f = function(x2)
    if abs(fl) < abs(f):
        root, xl = x1, x2
        fl, f = f, fl
    else:
        xl, root = x1, x2
    for _ in range(30):
        dx = (xl - root) * f / (f - fl)
        xl = root
        fl = f
        root = root + dx
        f = function(root)
        if abs(dx) < accuracy or f == 0.0:
            return root
    notify("RTSEC exceed maximum iterations")
    return root


falsePositionPause = "Problème d approximation de la borne (Pressez ENTER)!!!"


def falsePositionRoot(
    function: Integrand, x1: float, x2: float, accuracy: float, notify: Notify
) -> float | None:
    """RTFLSP: false position on a bracket; None where the ends have the same sign.

    The listing then pauses, raises ICONVERG and returns without assigning a
    result, which its callers either replace by an approximation typed at the
    keyboard or, in HARDSIN, use as it is.
    """
    fl = function(x1)
    fh = function(x2)
    if fl * fh > 0.0:
        notify(falsePositionPause)
        return None
    if fl < 0.0:
        xl, xh = x1, x2
    else:
        xl, xh = x2, x1
        fl, fh = fh, fl
    dx = xh - xl
    root = math.nan
    for _ in range(100):
        root = xl + dx * fl / (fl - fh)
        f = function(root)
        if f < 0.0:
            delta = xl - root
            xl = root
            fl = f
        else:
            delta = xh - root
            xh = root
            fh = f
        dx = xh - xl
        if abs(delta) < accuracy or f == 0.0:
            return root
    return root


def goldenMinimum(
    function: Integrand, ax: float, bx: float, cx: float, tolerance: float
) -> tuple[float, float]:
    """GOLDEN: (minimum value, its position) by golden-section search on (ax, bx, cx)."""
    r, c = goldenRatio, goldenComplement
    x0 = ax
    x3 = cx
    if abs(cx - bx) > abs(bx - ax):
        x1 = bx
        x2 = bx + c * (cx - bx)
    else:
        x2 = bx
        x1 = bx - c * (bx - ax)
    f1 = function(x1)
    f2 = function(x2)
    while abs(x3 - x0) > tolerance * (abs(x1) + abs(x2)):
        if f2 < f1:
            x0 = x1
            x1 = x2
            x2 = r * x1 + c * x3
            f1 = f2
            f2 = function(x2)
        else:
            x3 = x2
            x2 = x1
            x1 = r * x2 + c * x0
            f2 = f1
            f1 = function(x1)
    if f1 < f2:
        return f1, x1
    return f2, x2


Matrix = list[list[float]]


def luDecompose(a: Matrix, n: int, notify: Notify) -> list[int]:
    """DLUDCMP: Crout's LU of the leading n x n block of `a`, in place; the row permutation.

    `a` is indexed [row][column] from 0. Returns INDX, 0-based.
    """
    scale = [0.0] * n  # VV
    for i in range(n):
        largest = 0.0
        for j in range(n):
            if abs(a[i][j]) > largest:
                largest = abs(a[i][j])
        if largest == 0.0:
            notify("Singular matrix")
        scale[i] = 1.0 / largest
    pivots = [0] * n
    pivotRow = 0
    for j in range(n):
        for i in range(j):
            total = a[i][j]
            for k in range(i):
                total = total - a[i][k] * a[k][j]
            a[i][j] = total
        largest = 0.0
        for i in range(j, n):
            total = a[i][j]
            for k in range(j):
                total = total - a[i][k] * a[k][j]
            a[i][j] = total
            figure = scale[i] * abs(total)
            if figure >= largest:
                pivotRow = i
                largest = figure
        if j != pivotRow:
            a[pivotRow], a[j] = a[j], a[pivotRow]
            scale[pivotRow] = scale[j]
        pivots[j] = pivotRow
        if a[j][j] == 0.0:
            a[j][j] = luTiny
        if j != n - 1:
            inverse = 1.0 / a[j][j]
            for i in range(j + 1, n):
                a[i][j] = a[i][j] * inverse
    return pivots


def luSolve(a: Matrix, n: int, pivots: list[int], b: list[float]) -> None:
    """DLUBKSB: solve in place, with the listing's II=1 (Numerical Recipes: II=I)."""
    first = -1  # II=0
    for i in range(n):
        row = pivots[i]
        total = b[row]
        b[row] = b[i]
        if first != -1:
            for j in range(first, i):
                total = total - a[i][j] * b[j]
        elif total != 0.0:
            first = 0  # II=1: from the first row, not row i
        b[i] = total
    for i in range(n - 1, -1, -1):
        total = b[i]
        for j in range(i + 1, n):
            total = total - a[i][j] * b[j]
        b[i] = total / a[i][i]
