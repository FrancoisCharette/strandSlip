$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la deuxieme derivée de la surface de l'âme  C
C qui est égale à celle du fil sans glissement donné par l'équation    C
C A.5. Cela pour la flèche ayant un rayon de courbure constant         C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION FRCAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
C
      FRCAME=(2.0D0*PI*DCOS(2.0D0*PI*XF+THETA))/RHOB
C
      END
