$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui détermine les approximations initiales des           C
C différentes bornes dans le demi-pas, le long de X, en fonction de    C
C l'amplitude et de la longueur d'onde de la sinusoide imposée. Ces    C
C approximations initiales sont nécessaire pour la méthode de Newton.  C
C Modèle AVEC complaisance.                                            C
C======================================================================C
C
      SUBROUTINE APPSIN(XK,XB1,XB2)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10)
C
      DIMENSION XK(2*NMAX)
C
      COMMON/CONV/ICONVERG
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      NPORTEMP=NPORTION
      IF(NPORTION.EQ.11) NPORTEMP=NPORTION-1
C
      V1=(2.0D0*PI)/WLBAR
C
C Approximation de la valeur du rayon de courbure à XSUP et XINF.
C
      VDEN=DABS(-ABAR*DSIN(V1*XSUP))
      IF(XINF.LT.0001) THEN
            RHOBINF=1.0D0
            GOTO 900
      END IF
      VDENINF=DABS(-ABAR*DSIN(V1*XINF))
C
      RHOBINF=1.0D0/VDENINF
  900 RHOB=1.0D0/VDEN
C
      ZETAPRIME=XCOMP(NPORTEMP)/YCOMP(NPORTEMP)
C
      XB1A=RHOB*(GAM1*ZETAPRIME+1.0D0)
      XB1B=(-YCOMP(NPORTEMP))
      XB1C=(DACOS(XB1A*XB1B)-PI/2.0D0)/(2.0D0*PI)
C
      IF(ICONVERG.EQ.1) THEN
      ICONVERG=0
      WRITE(*,'(3X,''Valeur approximative de XB1C qui a été '',
     &''essayée ='',D16.8,/,3X,''Veuillez en rentrer une autre'',
     &'' (devrait probablement être inférieur)'')') XB1C
  100 WRITE(*,'(/,3X,''Entrez la nouvelle approximation de XB1C:'',\)')
      READ (*,*,ERR=100) XB1C
      END IF
C
C Approximation de la première borne de la région centrale
C
      XB1=XB1C+XINF
C
C Approximation de la deuxième borne de la région centrale
C
      XB2=XSUP-(XB1C*(RHOB/RHOBINF))
C
C Approximation des points de transitions.
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
