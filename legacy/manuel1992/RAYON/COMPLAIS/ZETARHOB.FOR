$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement et la dissipation d'énergie       %
C dans un demi-pas pour la flèche ayant un rayon de courbure           %
C constant, selon le MODELE AVEC COMPLAISANCE.                         %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM ZETARHOB
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX)
      DIMENSION B(JMAX),A(JMAX,JMAX)
C
      COMMON/CONV/ICONVERG
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      ICONVERG=0
      NPORTION=0
C
      CALL ENTZETA
C
      CALL COMP(NMAX)
C
 1000 NPORTION=NPORTION+1
C
      IF(NPORTION.EQ.1) GOTO 990
C
      JDIM=6*NPORTION-4 ! Dimension totale du Jacobien en fonction
C                         du nombre de portion linéaire.
C
      NPOINT=2*(NPORTION-2) ! Nombres totales de point de transition
C                             entre 2 régions de micro-glissement.
C
C  Initialise le Jacobien le vecteur B et XK() sur leur dimension
C  physique.
C
  500 DO I=1,JMAX
         B(I)=0.0D0
         DO J=1,JMAX
            A(I,J)=0.0D0
         END DO
      END DO
C
      DO I=1,2*NMAX
         XK(I)=0.0D0
      END DO
C
      DO I=1,NMAX
         BETAG(I)=0.0D0
         ETAG(I)=0.0D0
         BETAD(I)=0.0D0
         ETAD(I)=0.0D0
      END DO
C
      BTM=0.0D0
      ETM=0.0D0
C
      CALL APPROX(XK,XB1,XB2) ! Routine des approximations initiales
C
      CALL NEWTON(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,A,B)
C
      IF(ICONVERG.EQ.1) GOTO 500
C
  990 CONTINUE
C
C******BLOC QUI VERIFIE LA VALIDITE DU NOMBRE DE PORTIONS UTILISE******
      NPORTEMP=NPORTION
      IF(NPORTION.LT.11) THEN
            DFDEP=DABS(((DEPAME(XM)-DEPFIL(XCOMP(NPORTION),YCOMP
     &   (NPORTION),ZETA(NPORTION),BTM,ETM,XM))/GAM1)*4.0D0*PI)
           RDEP=(DEPAME(XM)-DEPFIL(XCOMP(NPORTION),YCOMP(NPORTION),
     &           ZETA(NPORTION),BTM,ETM,XM))/DEPAME(XM)
      ELSE
            NPORTEMP=NPORTION-1
            DFDEP=DABS(((DEPAME(XM)-DEPH(XM,XB1,BTM,ETM))/GAM1)*4.0D0*PI)
           RDEP=(DEPAME(XM)-DEPH(XM,XB1,BTM,ETM))/DEPAME(XM)
      END IF
C
      WRITE(*,20) NPORTION,DFDEP,XCOMP(NPORTEMP+1)*(2.0D0)
   20 FORMAT(//,3X,'Modèle à',I3,' port. liné; 2 delta max.=',F7.4,3X,
     &'Valeur max adm.=',F7.4)
C
      IF((DFDEP-2.0D0*XCOMP(NPORTEMP+1)).GT.0.0.AND.NPORTION.LT.11)
     & GOTO 1000
C**********************************************************************
C
      CALL DISPENRG(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,DSP)
C
      CALL ECRZETA(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,DSP,RDEP)
C
      STOP
      END
