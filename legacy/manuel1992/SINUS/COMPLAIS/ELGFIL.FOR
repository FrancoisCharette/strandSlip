$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la déformation du fil dans les régions de   C
C micro-glissement. Cela pour le modèle AVEC complaisance avec la      C
C flèche SINUSOIDALE. Equation A.40.                                   C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION ELGFIL(ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      TMP1=BTA*DSQRT(GAMEXP/ZTA)*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*DSQRT(GAMEXP/ZTA)*DEXP(-XF*DSQRT(GAMEXP/ZTA))
C
      TMP3A=DCOS(XF*PN1+THETA)/(GAM1*ZTA*PPB**2.0D0+1.0D0)
      TMP3B=DCOS(XF*PP1+THETA)/(GAM1*ZTA*PPA**2.0D0+1.0D0)
      TMP3=GAME1*(TMP3A-TMP3B)
C
      ELGFIL=TMP1-TMP2+TMP3
C
      END
