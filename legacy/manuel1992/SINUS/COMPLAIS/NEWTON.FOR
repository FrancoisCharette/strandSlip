$DEBUG
$STORAGE:2
C======================================================================C
C  Sousroutine qui utilise la méthode de Newton pour solutionner le    C
C  système d'équation non-linéaire dont l'algorithme est donné à       C
C  l'annexe C. MODELE AVEC COMPLAISANCE.                               C
C======================================================================C
C
      SUBROUTINE NEWTON(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,A,B)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX),A(JMAX,JMAX)
      DIMENSION B(JMAX),INDX(JMAX)
C
      COMMON/CONV/ICONVERG
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
C  Initialisation à zéro du vecteur B
C
      DO I=1,JDIM
         B(I)=0.0D0
      END DO
C
      K=0
      TOL=1.0D-10
      IERROR=0
C
C  Début de la boucle de résolution
C
C  Additionne la correction à chacunes des approximations des
C  inconnues.
C
 1000 DO I=1,NPORTION-1
         BETAG(I)=BETAG(I)+B(I)
         ETAG(I)=ETAG(I)+B(I+NPORTION-1)
         BETAD(I)=BETAD(I)+B(I+2*(NPORTION-1))
         ETAD(I)=ETAD(I)+B(I+3*(NPORTION-1))
      END DO
C
      IF(NPORTION.LT.2) GOTO 910
C
      DO I=1,NPOINT
         XK(I)=XK(I)+B(I+4*(NPORTION-1))
         IF(XK(I).LT.0.0) THEN
             IERROR=1
              GOTO 750
         END IF
      END DO
C
  910 CONTINUE
C
      XB1=XB1+B(JDIM-3)
      XB2=XB2+B(JDIM-2)
C
      BTM=BTM+B(JDIM-1)
      ETM=ETM+B(JDIM)
C
C  Le vecteur B() précédent a été obtenue suite à la résolution du
C  système d'équation et est totalement different de celui ci-bas
C  (voir "Numerical Recipes" pour les routines DLUDCMP et DLUBKSB).
C
C  Calcul du vecteur B, ce qui correspond à F(X) de l'étape 3
C  dans l'algorithme de l'annexe C.
C
      CALL VECB(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,B)
C
C  Calcul du Jacobien, ce qui correspond à J(X) de l'étape 3
C  dans l'algorithme de l'annexe C.
C
      CALL JACOB(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,A)
C
C  Solutionnne le système d'équation pour déterminer Y, ce qui
C  correspond à l'étape 4 dans l'algorithme de l'annexe C.
C
      CALL DLUDCMP(A,JDIM,JMAX,INDX,D)
      CALL DLUBKSB(A,JDIM,JMAX,INDX,B)
C
C************BLOC QUI VERIFIE S IL Y A CONVERGENCE***************
C
      C1=XB1-XINF
      C2=XSUP-XB2
      C3=XSUP-XB1
      C4=XB2-XINF
C
      IF(C1.LT.0.OR.C2.LT.0.OR.C3.LT.0.OR.C4.LT.0.OR.XB1.GT.XB2.
     &OR.K.EQ.14) THEN
            WRITE(*,'(///,1X,''!!!PROBLEME DE CONVERGENCE, '',
     &/,1X,''Veuillez recommencer avec une nouvelle approx.'',/)')
            ICONVERG=1
            GOTO 990
      END IF
C
  750 DO I=1,NPOINT/2
         JPOINT=NPOINT-(I-1)
         CR1=XK(I)-XINF
         CR2=XSUP-XK(JPOINT)
         CR3=XSUP-XK(JPOINT)
         CR4=XK(JPOINT)-XINF
C
         IF(CR1.LT.0.OR.CR2.LT.0.OR.CR3.LT.0.OR.CR4.LT.0.OR.XK(I).
     &      GT.XK(JPOINT).OR.IERROR.EQ.1) THEN
            WRITE(*,'(///,1X,''!!!PROBLEME DE CONVERGENCE, '',
     &/,1X,''Veuillez recommencer avec une nouvelle approx.'',/)')
            ICONVERG=1
            IERROR=0
            GOTO 990
      END IF
C
      END DO
C****************************************************************
C
      WRITE(*,39) K
   39 FORMAT(/,3X,'Iteration #',I2)
      WRITE(*,40) XB1,XB2
   40 FORMAT(1X,'XB1='D16.8,5X,'XB2=',D16.8)
C
      DO I=1,NPOINT/2
         JPOINT=NPOINT-(I-1)
         WRITE(*,42) I,XK(I),JPOINT,XK(JPOINT)
      END DO
C
C Bloc d'écriture supplémentaire utilisé pour la flèche sinusoidale.
C
      WRITE(*,41) XB1-XINF,XSUP-XB2
   41 FORMAT(/,1X,'XB1-XINF='D14.8,4X,'XSUP-XB2=',D14.8)
C
      DO I=1,NPOINT/2
         JPOINT=NPOINT-(I-1)
         WRITE(*,43) I,XK(I)-XINF,JPOINT,XSUP-XK(JPOINT)
      END DO
C
   42 FORMAT(1X,'XK(',I2,')=',D16.8,5X,'XK(',I2,')=',D16.8)
   43 FORMAT(1X,'XK(',I2,')-XINF=',D14.8,4X,'XSUP-XK(',I2,')=',D14.8)
C
C--------------BOUCLE DE CONTROLE DES TOLERANCES---------------------
C
C Ce qui correspond à l'étape 6 dans l'algorithme de l'annexe C.
C
      IF(K.EQ.0) GOTO 980
C
      DO I=1,NPORTION-1
         IF(DABS(B(I)/BETAG(I)).GE.TOL) GOTO 980
         IF(DABS(B(I+NPORTION-1)/ETAG(I)).GE.TOL) GOTO 980
         IF(DABS(B(I+2*(NPORTION-1))/BETAD(I)).GE.TOL) GOTO 980
         IF(DABS(B(I+3*(NPORTION-1))/ETAD(I)).GE.TOL) GOTO 980
      END DO
C
      DO I=1,NPOINT
         IF(DABS(B(I+4*(NPORTION-1))/XK(I)).GE.TOL) GOTO 980
      END DO
C
      IF(DABS(B(JDIM-3)/XB1).GE.TOL) GOTO 980
      IF(DABS(B(JDIM-2)/XB2).GE.TOL) GOTO 980
C
      IF(DABS(B(JDIM-1)/BTM).GE.TOL) GOTO 980
      IF(DABS(B(JDIM)/ETM).GE.TOL) GOTO 980
C
      GOTO 990
C--------------------------------------------------------------------
C
  980 K=K+1
      IF(K.GT.15) GOTO 990
C
      GOTO 1000
C
  990 RETURN
      END
