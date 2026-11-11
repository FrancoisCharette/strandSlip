$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction évalue déplacement du fil dans la région de macro-    C
C glissement, selon la flèche et le modèle considéré il s'agit de      C
C l'équation A.7 ou A.12 ou A.25 ou A.33 ou A.36 ou A.42               C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DEPH(XH,XH1,H1,H2)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      DEPH=(ICOTE*PI)*((XH-XH1)**2)+(H1*(XH-XH1))+H2
C
      END
