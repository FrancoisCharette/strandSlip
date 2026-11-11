$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la deuxième dérivée du déplacement de la    C
C surface de l'âme qui est égale à celle du fil sans glissement donné  C
C par l'équation A.32. Cela pour la flèche sinusoidale.                C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION FRCAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
C
      TMP1=DCOS(2.0D0*PI*XF+THETA)*DSIN((2.0D0*PI*XF)/WLBAR)
      TMP2=DSIN(2.0D0*PI*XF+THETA)*DCOS((2.0D0*PI*XF)/WLBAR)
C
      FRCAME=((2.0D0*PI*ABAR)/WLBAR)*(WLBAR*TMP1+TMP2)
C
      END
