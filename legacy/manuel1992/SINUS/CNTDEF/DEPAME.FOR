$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine le déplacement de la surface de l'âme qui   C
C est égale à celui du fil sans glissement donné par l'équation A.30   C
C Cela pour la flèche sinusoidale.                                     C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DEPAME(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
C
      TMP3A=DSIN(XF*PN1+THETA)-SIN(THETA)
      TMP3B=DSIN(XF*PP1+THETA)-SIN(THETA)
C
      DEPAME=((WLBAR*ABAR)/(4.0D0*PI))*(TMP3A/PN-TMP3B/PP)
C
      END
