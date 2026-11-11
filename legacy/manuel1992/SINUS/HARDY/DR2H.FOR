$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction évalue la déformation du fil dans la région de macro- C
C glissement, selon la flèche et le modèle considéré il s'agit de      C
C l'équation A.10 ou A.15 ou A.26 ou A.34 ou A.37 ou A.43              C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DR2H(XH,XH1,H1)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      DR2H=(ICOTE*2.0D0*PI)*(XH-XH1)+H1
C
      END
