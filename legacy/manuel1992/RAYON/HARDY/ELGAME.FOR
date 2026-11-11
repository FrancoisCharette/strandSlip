$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la déformation de la surface de l'âme qui   C
C est égale à celle du fil sans glissement donné par l'équation A.3.   C
C Cela pour la flèche ayant un rayon de courbure constant              C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION ELGAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
C
      ELGAME=DSIN(2.0D0*PI*XF+THETA)/RHOB
C
      END
