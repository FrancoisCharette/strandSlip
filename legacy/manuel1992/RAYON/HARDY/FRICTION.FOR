$DEBUG
$STORAGE:2
C---------------------------------------------------------------------C
C Fonction utilisé pour trouver les bornes de la région de macro-glis C
C Cela pour la flèche ayant un rayon de courbure constant, modèles    C
C SANS complaisance.                                                  C
C---------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION FRICTION(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      FRICTION=(DCOS(2.0D0*PI*XF+THETA)/RHOB)-ICOTE*1.0D0
C
      END
