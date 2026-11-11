$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine le déplacement de la surface de l'âme qui   C
C est égale à celui du fil sans glissement donné par l'équation A.1    C
C Cela pour la flèche ayant un rayon de courbure constant              C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DEPAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
C
      DEPAME=(DCOS(THETA)-DCOS(2.0D0*PI*XF+THETA))/(2.0D0*PI*RHOB)
C
      END
