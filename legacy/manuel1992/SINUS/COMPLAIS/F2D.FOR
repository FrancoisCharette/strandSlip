$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction calcul la valeur de la dérivée partielle par rapport  C
C à eta i, pour les conditions limites qui posent les déplacements     C
C égaux.                                                               C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION F2D(XF,ZTA)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      F2D=DEXP(-XF*DSQRT(GAMEXP/ZTA))
C
      END
