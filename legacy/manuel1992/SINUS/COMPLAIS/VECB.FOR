$DEBUG
$STORAGE:2
C===================================================================C
C  Sousroutine qui prepare le vecteur B de la methode de Newton     C
C  MODELE AVEC COMPLAISANCE                                         C
C===================================================================C
C
      SUBROUTINE VECB(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,B)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX),B(JMAX)
C
C     COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Bloc
C                                COMMON pour la flèche sinusoidale.
      COMMON/CSTF/PI,THETA,RHOB ! Bloc COMMON pour la flèche ayant
C                                 un rayon de courbure constant.
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/XCST/XINF,XSUP,XM,ICOTE
      COMMON/PORTION/JDIM,NPOINT,NPORTION
C
C  Initialisation à zéro du vecteur B
C
      DO I=1,JDIM
         B(I)=0.0D0
      END DO
C
C  Condition limites (éq 3.51) à XINF
C
      B(1)=-(DEPAME(XINF)-DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAG(1),
     &ETAG(1),XINF))
C
C  Condition limites (éq 3.52) à XSUP
C
      B(2)=-(DEPAME(XSUP)-DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAD(1),
     &ETAD(1),XSUP))
C
      J=2
C
      IF(NPORTION.LT.3) GOTO 920
C
C#####################################################################
C############### Conditions limites pour les points de ###############
C###### transitions situés du côté gauche de la région centrale ######
C#####################################################################
C
      IPOINT=0
C
      DO I=1,NPORTION-2
         J=J+1
         IPOINT=IPOINT+1
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements au point de transition (éq. 3.36).
C
      B(J)=-(DEPFIL(XCOMP(I),YCOMP(I),ZETA(I),BETAG(I),ETAG(I),
     & XK(IPOINT))-DEPFIL(XCOMP(I+1),YCOMP(I+1),ZETA(I+1),BETAG(I+1),
     & ETAG(I+1),XK(IPOINT)))
C
      J=J+1
C
C  Condition limite qui impose la continuité des déformations au
C  point de transition (éq. 3.37).
C
      B(J)=-(ELGFIL(ZETA(I),BETAG(I),ETAG(I),XK(IPOINT))-
     &       ELGFIL(ZETA(I+1),BETAG(I+1),ETAG(I+1),XK(IPOINT)))
C
      J=J+1
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil au point de transition (éq. 3.38).
C
      B(J)=-(DEPAME(XK(IPOINT))-DEPFIL(XCOMP(I),YCOMP(I),
     &ZETA(I),BETAG(I),ETAG(I),XK(IPOINT))+2.0D0*ICOTE*(GAM1/(4.0D0*PI))
     &*XCOMP(I+1))
C
      END DO
C
C#####################################################################
C############## Conditions limites pour les points de ################
C###### transitions situés du côté droit de la région centrale #######
C#####################################################################
C
      IPOINT=0
C
      DO I=1,NPORTION-2
         J=J+1
         IPOINT=IPOINT+1
         JPOINT=NPOINT-(IPOINT-1)
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements au point de transition.
C
      B(J)=-(DEPFIL(XCOMP(I),YCOMP(I),ZETA(I),BETAD(I),ETAD(I),
     & XK(JPOINT))-DEPFIL(XCOMP(I+1),YCOMP(I+1),ZETA(I+1),BETAD(I+1),
     & ETAD(I+1),XK(JPOINT)))
C
      J=J+1
C
C  Condition limite qui impose la continuité des déformations au point
C  de transition.
C
      B(J)=-(ELGFIL(ZETA(I),BETAD(I),ETAD(I),XK(JPOINT))-
     &       ELGFIL(ZETA(I+1),BETAD(I+1),ETAD(I+1),XK(JPOINT)))
C
      J=J+1
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil au point de transition.
C
      B(J)=-(DEPAME(XK(JPOINT))-DEPFIL(XCOMP(I),YCOMP(I),
     &ZETA(I),BETAD(I),ETAD(I),XK(JPOINT))+2.0D0*ICOTE*(GAM1/(4.0D0*PI))
     &*XCOMP(I+1))
C
      END DO
C
  920 CONTINUE
C
      IF(NPORTION.EQ.11) GOTO 900
C
C#####################################################################
C############## Conditions limites pour les bornes de ################
C###### de la région centrale lorsqu'il s'agit d'une région de #######
C####################### MICRO-glissement ############################
C
C  Première borne
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements à la première borne (éq.3.39).
C
      B(JDIM-5)=-(DEPFIL(XCOMP(NPORTION-1),YCOMP(NPORTION-1),ZETA
     &(NPORTION-1),BETAG(NPORTION-1),ETAG(NPORTION-1),XB1)-DEPFIL(
     &XCOMP(NPORTION),YCOMP(NPORTION),ZETA(NPORTION),BTM,ETM,XB1))
C
C  Condition limite qui impose la continuité des déformations à la
C  première borne (éq. 3.40).
C
      B(JDIM-4)=-(ELGFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     &ETAG(NPORTION-1),XB1)-ELGFIL(ZETA(NPORTION),BTM,ETM,XB1))
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil à la première borne (éq. 3.41).
C
      B(JDIM-3)=-(DEPAME(XB1)-DEPFIL(XCOMP(NPORTION-1),YCOMP
     &(NPORTION-1),ZETA(NPORTION-1),BETAG(NPORTION-1),ETAG(NPORTION-1),
     &XB1)+2.0D0*ICOTE*(GAM1/(4.0D0*PI))*XCOMP(NPORTION))
C
C  Deuxième borne
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements à la deuxième borne (éq.3.42).
C
      B(JDIM-2)=-(DEPFIL(XCOMP(NPORTION-1),YCOMP(NPORTION-1),ZETA
     &(NPORTION-1),BETAD(NPORTION-1),ETAD(NPORTION-1),XB2)-DEPFIL(
     &XCOMP(NPORTION),YCOMP(NPORTION),ZETA(NPORTION),BTM,ETM,XB2))
C
C  Condition limite qui impose la continuité des déformations à la
C  deuxième borne (éq. 3.43).
C
      B(JDIM-1)=-(ELGFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     &ETAD(NPORTION-1),XB2)-ELGFIL(ZETA(NPORTION),BTM,ETM,XB2))
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil à la deuxième borne (éq. 3.44).
C
      B(JDIM)=-(DEPAME(XB2)-DEPFIL(XCOMP(NPORTION-1),YCOMP
     &(NPORTION-1),ZETA(NPORTION-1),BETAD(NPORTION-1),ETAD(NPORTION-1),
     &XB2)+2.0D0*ICOTE*(GAM1/(4.0D0*PI))*XCOMP(NPORTION))
C
      GOTO 999
C
C#####################################################################
C############### Conditions limites pour les bornes de ###############
C###### de la région centrale lorsqu'il s'agit d'une région de #######
C####################### MACRO-glissement ############################
C
C  Première borne
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements à la première borne (éq.3.45).
C
  900 B(JDIM-5)=-(DEPFIL(XCOMP(NPORTION-1),YCOMP(NPORTION-1),ZETA
     & (NPORTION-1),BETAG(NPORTION-1),ETAG(NPORTION-1),XB1)-
     & DEPH(XB1,XB1,BTM,ETM))
C
C  Condition limite qui impose la continuité des déformations à la
C  première borne (éq. 3.46).
C
      B(JDIM-4)=-(ELGFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     & ETAG(NPORTION-1),XB1)-DR2H(XB1,XB1,BTM))
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil à la première borne (éq. 3.47).
C
      B(JDIM-3)=-(DEPAME(XB1)-DEPFIL(XCOMP(NPORTION-1),YCOMP
     & (NPORTION-1),ZETA(NPORTION-1),BETAG(NPORTION-1),ETAG(NPORTION-1)
     & ,XB1)+2.0D0*ICOTE*(GAM1/(4.0D0*PI))*XCOMP(NPORTION))
C
C  Deuxième borne
C
C  Condition limite qui impose la compatibilité géométrique des
C  déplacements à la deuxième borne (éq.3.48).
C
      B(JDIM-2)=-(DEPFIL(XCOMP(NPORTION-1),YCOMP(NPORTION-1),ZETA
     & (NPORTION-1),BETAD(NPORTION-1),ETAD(NPORTION-1),XB2)-
     & DEPH(XB2,XB1,BTM,ETM))
C
C  Condition limite qui impose la continuité des déformations à la
C  deuxième borne (éq. 3.49).
C
      B(JDIM-1)=-(ELGFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     & ETAD(NPORTION-1),XB2)-DR2H(XB2,XB1,BTM))
C
C  Condition limite qui impose la différence entre le déplacement de la
C  surface de l'âme et celui du fil à la deuxième borne (éq. 3.50).
C
      B(JDIM)=-(DEPAME(XB2)-DEPFIL(XCOMP(NPORTION-1),YCOMP
     & (NPORTION-1),ZETA(NPORTION-1),BETAD(NPORTION-1),ETAD(NPORTION-1)
     & ,XB2)+2.0D0*ICOTE*(GAM1/(4.0D0*PI))*XCOMP(NPORTION))
C
  999 RETURN
      END
