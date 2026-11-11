$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la deuxième dérivée du déplacement du fil   C
C dans les régions de micro-glissement. Cela pour le modèle AVEC       C
C complaisance avec la flèche SINUSOIDALE. Equation A.41.              C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION FRCFIL(ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      TMP1=BTA*(GAMEXP/ZTA)*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*(GAMEXP/ZTA)*DEXP(-XF*DSQRT(GAMEXP/ZTA))
C
      TMP3A=-PN*DSIN(XF*PN1+THETA)/(GAM1*ZTA*PPB**2.0D0+1.0D0)
      TMP3B=PP*DSIN(XF*PP1+THETA)/(GAM1*ZTA*PPA**2.0D0+1.0D0)
      TMP3=GAMF1*(TMP3A+TMP3B)
C
      FRCFIL=TMP1+TMP2+TMP3
C
      END
