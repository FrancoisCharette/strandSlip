$DEBUG
$STORAGE:2
C---------------------------------------------------------------------C
C Cette fonction sert à déterminer la position et la valeur du        C
C minimum du coefficient de friction. Cela pour la flèche sinusoidale.C
C---------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION VMIN(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      TMP1=DCOS(2.0D0*PI*XF+THETA)*DSIN((2.0D0*PI*XF)/WLBAR)
      TMP2=DSIN(2.0D0*PI*XF+THETA)*DCOS((2.0D0*PI*XF)/WLBAR)
C
      VMIN=-ICOTE*(ABAR/WLBAR)*(WLBAR*TMP1+TMP2)
C
      END
