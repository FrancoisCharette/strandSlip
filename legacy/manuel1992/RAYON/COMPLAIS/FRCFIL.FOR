$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine la deuxième dérivée du déplacement du fil   C
C dans les régions de micro-glissement. Cela pour le modèle avec       C
C complaisance avec la flèche ayant un rayon de courbure.              C
C Equation A.24.                                                       C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION FRCFIL(ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      TMP1=BTA*(GAMEXP/ZTA)*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*(GAMEXP/ZTA)*DEXP(-XF*DSQRT(GAMEXP/ZTA))
      TMP3=(GAMF1/(GAM1*ZTA+1))*DCOS(2.0D0*PI*XF+THETA)
C
      FRCFIL=TMP1+TMP2+TMP3
C
      END
