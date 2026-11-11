$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine le déplacement du fil dans les régions de   C
C micro-glissement. Cela pour le modèle AVEC complaisance avec la      C
C flèche SINUSOIDALE. Equation A.39.                                   C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DEPFIL(BXORG,BYORG,ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      TMP1=BTA*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*DEXP(-XF*DSQRT(GAMEXP/ZTA))
C
      TMP3A=DSIN(XF*PN1+THETA)/(GAM1*ZTA*PPB**2.0D0+1.0D0)-SIN(THETA)
      TMP3B=DSIN(XF*PP1+THETA)/(GAM1*ZTA*PPA**2.0D0+1.0D0)-SIN(THETA)
      TMP3=GAMD1*(TMP3A/PN-TMP3B/PP)
C
      DEPFIL=TMP1+TMP2+TMP3+2.0D0*(GAM1/(4.0D0*PI))*ICOTE*BXORG-
     &2.0D0*(GAM1/(4.0D0*PI))*ICOTE*ZTA*BYORG
C
      END
