$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la déformation du fil dans les régions de   C
C micro-glissement. Cela pour le modèle avec complaisance avec la      C
C flèche ayant un rayon de courbure. Equation A.23.                    C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION ELGFIL(ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      TMP1=BTA*DSQRT(GAMEXP/ZTA)*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*DSQRT(GAMEXP/ZTA)*DEXP(-XF*DSQRT(GAMEXP/ZTA))
      TMP3=(GAME1/(GAM1*ZTA+1))*DSIN(2.0D0*PI*XF+THETA)
C
      ELGFIL=TMP1-TMP2+TMP3
C
      END
