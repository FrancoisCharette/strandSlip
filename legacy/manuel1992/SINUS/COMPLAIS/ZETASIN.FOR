$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement, la dissipation d'énergie sur     %
C une longueur d'onde complète et l'analyse d'un demi-pas en           %
C particulier pour la flèche sinusoidale, selon le MODELE AVEC         %
C COMPLAISANCE.                                                        %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM ZETASIN
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
      COMMON/COMPLAIS/EN
      COMMON/CONV/ICONVERG
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
C  Constantes utilisées
C
      ICONVERG=0
      DSPTOTAL=0.0D0
      DSPTMP=0.0D0
      NPORTION=0
C
      EN=2.0D0/3.0D0 ! Exposant de la courbe de complaisance.
C
      CALL COMP(NMAX)
C
      CALL ENSNZETA(ICHOIX)
C
      XTOUR=0.0D0-0.5D0
      IF(ICHOIX.EQ.2) XTOUR=((WLBAR/4.0D0)-0.25D0)-0.5D0
  700 IF(ICHOIX.EQ.3) THEN
         WRITE(*,'(/,9X,''Nombre de tour de l origine (XTOUR) :'',\)')
         READ (*,*,ERR=700) XTOUR
         XTOUR=XTOUR-0.5D0
      END IF
C
  900 XTOUR=XTOUR+0.5D0
C
      XINF=XTOUR
      XSUP=XINF+0.5D0
      XM=(XINF+XSUP)/2.0D0
C
      VCOTE=DCOS(2.0D0*PI*XM+THETA)
      ICOTE=-1
      IF(VCOTE.GT.0.0) ICOTE=1
C
 1000 NPORTION=NPORTION+1
C
      JDIM=6*NPORTION-4  !Dimension totale du jacobien en fonction
C                         du nombre de portions linéaire.
C
      NPOINT=2*(NPORTION-2)  !Nombres totales de point de transition
C                             entre 2 portions
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
      IF(NPORTION.EQ.1) THEN
         CALL UNRES(A,B,BTM,ETM)
         GOTO 990
      END IF
C
      CALL APPSIN(XK,XB1,XB2)  !Approximations initiales
C
      CALL NEWTON(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,A,B)
C
      IF(ICONVERG.EQ.1) GOTO 500
C
  990 CONTINUE
C
C*******BLOC QUI VERIFI LA VALIDITE DU NOMBRE DE PORTION UTILISE*******
      NPORTEMP=NPORTION
      IF(NPORTION.LT.11) THEN
            DFDEP=((DEPAME(XM)-DEPFIL(XCOMP(NPORTION),YCOMP(NPORTION),
     &           ZETA(NPORTION),BTM,ETM,XM))/GAM1)*4.0D0*PI
            RDEP=(DEPAME(XM)-DEPFIL(XCOMP(NPORTION),YCOMP(NPORTION),
     &          ZETA(NPORTION),BTM,ETM,XM))/DEPAME(XM)
      ELSE
            NPORTEMP=NPORTION-1
            DFDEP=((DEPAME(XM)-DEPH(XM,XB1,BTM,ETM))/GAM1)*4.0D0*PI
            RDEP=(DEPAME(XM)-DEPH(XM,XB1,BTM,ETM))/DEPAME(XM)
      END IF
C
      WRITE(*,20) NPORTION,DABS(DFDEP),XCOMP(NPORTEMP+1)*(2.0D0)
   20 FORMAT(//,3X,'Modele a',I3,' port. lin.; 2 delta max.=',F7.4,3X,
     &'Valeur max adm.=',F7.4)
C
      IF((DABS(DFDEP)-2.0D0*XCOMP(NPORTEMP+1)).GT.0.0.AND.NPORTION.
     &LT.11) GOTO 1000
C**********************************************************************
C
C
      CALL DISPENRG(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,DSP)
      DSPTMP=DSPTMP+DSP
C
      CALL ECSNZETA(ICHOIX,BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,
     &ETM,DSP,DSPTOTAL,RDEP)
C
      IF(ICHOIX.EQ.4) GOTO 999
C
      PAUSE 'Pressez ENTER pour continuer'
C
      IF(XM.LT.WLBAR/4.0D0-.6.AND.ICHOIX.EQ.1) THEN
            NPORTION=NPORTION-1
            GOTO 900
      END IF
C
      DSPTOTAL=4.0D0*DSPTMP
C
      CALL ECSNZETA(ICHOIX,BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,
     &ETM,DSP,DSPTOTAL,RDEP)
C
  999 STOP
      END
