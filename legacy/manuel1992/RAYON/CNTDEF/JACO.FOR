$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui prépare le Jacobien de la méthode Newton.            C
C MODELE AVEC CONTINUITE DE DEFORMATION                                C
C======================================================================C
C
      SUBROUTINE JACO(XB1,XB2,XIC,A)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (JDIM=4)
C
      DIMENSION A(JDIM,JDIM)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
C  Initialisation à zéro du Jacobien
C
      DO I=1,JDIM
         DO J=1,JDIM
            A(I,J)=0.0D0
         END DO
      END DO
C
C Valeurs du Jacobien
C
      A(1,1)=ELGAME(XB1)
      A(1,2)=0.0D0
      A(1,3)=0.0D0
      A(1,4)=-1.0D0
C
      A(2,1)=FRCAME(XB1)
      A(2,2)=0.0D0
      A(2,3)=-1.0D0
      A(2,4)=0.0D0
C
      A(3,1)=-ICOTE*2.0D0*PI*(XB1-XB2)+XIC
      A(3,2)=ELGAME(XB2)-DR2H(XB2,XB1,XIC)
      A(3,3)=(XB1-XB2)
      A(3,4)=-1.0D0
C
      A(4,1)=ICOTE*2.0D0*PI
      A(4,2)=FRCAME(XB2)-ICOTE*2.0D0*PI
      A(4,3)=-1.0D0
      A(4,4)=0.0D0
C
      RETURN
      END
