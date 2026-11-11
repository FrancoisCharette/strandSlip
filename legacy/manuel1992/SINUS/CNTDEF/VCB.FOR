$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui prépare le vecteur B de la méthode de Newton.        C
C MODELE AVEC CONTINUITE DE DEFORMATION                                C
C======================================================================C
C
      SUBROUTINE VCB(XB1,XB2,XIC,PSIC,B)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (JDIM=4)
C
      DIMENSION B(JDIM)
C
C Initialisation à zéro du vecteur B
C
      DO I=1,JDIM
         B(I)=0.0D0
      END DO
C
C Valeurs du vecteur B
C
      B(JDIM-3)=-(DEPAME(XB1)-PSIC)
C
      B(JDIM-2)=-(ELGAME(XB1)-XIC)
C
      B(JDIM-1)=-(DEPAME(XB2)-DEPH(XB2,XB1,XIC,PSIC))
C
      B(JDIM)=-(ELGAME(XB2)-DR2H(XB2,XB1,XIC))
C
      RETURN
      END
