$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui utilise la méthode de Newton pour solutionner le     C
C système d'équations non-linéaire de la page 25 et de la page 27.     C
C MODELE AVEC CONTINUITE DE DEFORMATION                                C
C======================================================================C
C
      SUBROUTINE NEWT(XB1,XB2,XIC,PSIC)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (JDIM=4)
C
      DIMENSION B(JDIM),INDX(JDIM),A(JDIM,JDIM)
C
      COMMON/CONV/ICONVERG
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
C Initialisation à zéro du vecteur B
C
      DO I=1,JDIM
         B(I)=0.0D0
      END DO
C
      K=0
      TOL=1.0D-8
C
C  Début de la boucle de résolution
C
 1000 CONTINUE
C
      XB1=XB1+B(JDIM-3)
      XB2=XB2+B(JDIM-2)
C
      XIC=XIC+B(JDIM-1)
      PSIC=PSIC+B(JDIM)
C
C
      CALL VCB(XB1,XB2,XIC,PSIC,B)
C
C
      CALL JACO(XB1,XB2,XIC,A)
C
C
      CALL DLUDCMP(A,JDIM,JDIM,INDX,D)
      CALL DLUBKSB(A,JDIM,JDIM,INDX,B)
C
C
C************BLOC QUI VERIFIE S'IL Y A CONVERGENCE***************
      C1=XB1-XINF
      C2=XSUP-XB2
C
      IF(C1.LT.0.OR.C2.LT.0.OR.XB1.GT.XB2.OR.K.GE.15) THEN
            WRITE(*,'(///,1X,''!!!PROBLEME DE CONVERGENCE, '',
     &/,1X,''Veuillez recommencer avec une nouvelle approx.'',/)')
            ICONVERG=1
            GOTO 990
      END IF
C****************************************************************
C
      WRITE(*,39) K
   39 FORMAT(/,3X,'Iteration #',I2)
      WRITE(*,40) XB1,XB2
      WRITE(*,45) XIC,PSIC
   40 FORMAT(3X,'XB1='D14.8,8X,'XB2=',D14.8,8X)
   45 FORMAT(3X,'XIC='D14.8,8X,'PSIC=',D14.8)
C
C--------------BOUCLE DE CONTROLE DES TOLERANCES---------------------
C
      IF(K.EQ.0) GOTO 980
C
      IF(DABS(B(JDIM-3)/XB1).GE.TOL) GOTO 980
      IF(DABS(B(JDIM-2)/XB2).GE.TOL) GOTO 980
C
      IF(DABS(B(JDIM-1)/XIC).GE.TOL) GOTO 980
      IF(DABS(B(JDIM)/PSIC).GE.TOL) GOTO 980
C
      GOTO 990
C--------------------------------------------------------------------
C
  980 K=K+1
C
      GOTO 1000
C
  990 RETURN
      END
