$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Fonction qui sert à approximer les positions des bornes de la région C
C de macro-glissement. Modèle avec continuitée de déformation, flèche  C
C sinusoidale.                                                         C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION APPBRN(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      TMP1=ABAR*DSIN(2.0D0*PI*XF+THETA)*DSIN((2*PI*XF)/WLBAR)
      TMP2=ICOTE*2.0D0*PI*(XM-XF)
C
      APPBRN=TMP1+TMP2
      END
