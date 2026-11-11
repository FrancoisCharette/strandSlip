$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la déformation de la surface de l'âme qui   C
C est égale à celle du fil sans glissement donné par l'équation A.31   C
C Cela pour la flèche sinusoidale.                                     C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION ELGAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
C
      ELGAME=ABAR*DSIN(2.0D0*PI*XF+THETA)*DSIN((2*PI*XF)/WLBAR)
C
      END
