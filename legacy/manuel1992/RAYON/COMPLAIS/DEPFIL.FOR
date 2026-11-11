$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction détermine le déplacement du fil dans les régions de   C
C micro-glissement. Cela pour le modèle avec complaisance avec la      C
C flèche ayant un rayon de courbure. Equation A.17.                    C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DEPFIL(BXORG,BYORG,ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      TMP1=BTA*DEXP(XF*DSQRT(GAMEXP/ZTA))
      TMP2=TA*DEXP(-XF*DSQRT(GAMEXP/ZTA))
      TMP3=GAMD1*DCOS(THETA)
      TMP4=(GAMD1/(GAM1*ZTA+1))*DCOS((2.0D0*PI*XF)+THETA)
C
      DEPFIL=TMP1+TMP2+TMP3-TMP4+ICOTE*2.0D0*(GAM1/(4.0D0*PI))*BXORG-
     &ICOTE*2.0D0*(GAM1/(4.0D0*PI))*ZTA*BYORG
C
      END
