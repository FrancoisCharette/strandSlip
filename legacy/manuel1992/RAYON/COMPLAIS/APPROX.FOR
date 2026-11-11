$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui détermine les approximations initiales des           C
C différentes bornes le long de X en fonction du rayon de courbure     C
C imposée. Ces approximations initiales sont nécessaire pour la        C
C méthode de Newton. Modèle AVEC complaisance.                         C
C======================================================================C
C
      SUBROUTINE APPROX(XK,XB1,XB2)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10)
C
      DIMENSION XK(2*NMAX)
C
      COMMON/CONV/ICONVERG
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      NPORTEMP=NPORTION
      IF(NPORTION.EQ.11) NPORTEMP=NPORTION-1
C
      ZETAPRIME=XCOMP(NPORTEMP)/YCOMP(NPORTEMP)
C
      XB1A=(GAM1*ZETAPRIME+1.0D0)/GAME1
      XB1B=(-YCOMP(NPORTEMP))
C
C Approximation de la première borne de la région centrale
C
      XB1C=(DACOS(XB1A*XB1B)-PI/2.0D0)/(2.0D0*PI)
C
C Si la fonction ci-haut ne donne pas de bon résultats, on demande
C à l'utilisateur une approximation
C
      IF(ICONVERG.EQ.1) THEN
      ICONVERG=0
      WRITE(*,'(3X,''Valeur approximative de XB1C qui a ete '',
     &''essayee ='',D16.8,/,3X,''Veuillez en rentrer une autre'',
     &'' (devrait probablement etre inferieur)'')') XB1C
      WRITE(*,'(/,3X,''Entrez la nouvelle approximation de XB1C:'',\)')
      READ (*,*) XB1C
      END IF
C
C
      XB1=XB1C+XINF
C
      XB2=XSUP-XB1C
C
C Connaissant l'approximation des bornes de la région centrale
C on trouve une approximation pour chacun des points de transitions.
C
      DO I=1,NPOINT/2
         JPOINT=NPOINT-(I-1)
         XKTEMP=(XCOMP(I+1)/XCOMP(NPORTEMP+1))*XB1C
         XK(I)=XKTEMP+XINF
         XK(JPOINT)=XSUP-XKTEMP
      END DO
C
      RETURN
      END
