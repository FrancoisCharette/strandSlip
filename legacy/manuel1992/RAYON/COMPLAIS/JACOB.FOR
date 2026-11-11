$DEBUG
$STORAGE:2
C======================================================================C
C  Sousroutine qui prépare le Jacobien de la méthode Newton.           C
C  MODELE AVEC COMPLAISANCE.                                           C
C======================================================================C
C
      SUBROUTINE JACOB(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,A)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX),A(JMAX,JMAX)
C
C     COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Bloc
C                                COMMON pour la flèche sinusoidale.
      COMMON/CSTF/PI,THETA,RHOB ! Bloc COMMON pour la flèche ayant
C                                 un rayon de courbure constant.
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
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
C  Initialisation de certaines variables
C
      I=1
      J=1
C
C  Dérivée partielle de la condition limites (éq 3.51) à XINF
C
      A(I,J)=-F1D(XINF,ZETA(1))
      A(I,J+NPORTION-1)=-F2D(XINF,ZETA(1))
C
      I=I+1
      J=2*(NPORTION-1)+1
C
C  Dérivée partielle de la condition limites (éq 3.52) à XSUP
C
      A(I,J)=-F1D(XSUP,ZETA(1))
      A(I,J+NPORTION-1)=-F2D(XSUP,ZETA(1))
C
C
      IF(NPORTION.LT.3) GOTO 900

C#####################################################################
C### Dérivées partielles des conditions limites pour les points de ###
C###### transitions situés du côté gauche de la région centrale ######
C#####################################################################
      IPOINT=0
C
C  Compteurs pour le Iieme ressort
C
      IPOR=-1
C
C  Compteurs du No. de point de transition entre les 2 ressorts qui
C  sont considérés, en premier on considère que le côté gauche;
C
  700 IPOINT=IPOINT+1
      IPOR=IPOR+1
      J=IPOR
C
      INF=0
C
C  Les compteurs I et J servent pour les différentes positions dans la
C  matrice Jacobienne.
C
      IPORTION=IPOR
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements au point de transition (éq. 3.36).
C
      I=I+1
  710 J=J+1
C
      INF=INF+1
C
      IPORTION=IPORTION+1
      IF(INF.EQ.1) ISIGNE=1
      IF(INF.EQ.2) ISIGNE=-1
      A(I,J)=ISIGNE*F1D(XK(IPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=ISIGNE*F2D(XK(IPOINT),ZETA(IPORTION))
C
      IF(INF.LT.2) GOTO 710
C
      A(I,IPOINT+4*(NPORTION-1))=ELGFIL(ZETA(IPOINT),BETAG(IPOINT),
     &ETAG(IPOINT),XK(IPOINT))-ELGFIL(ZETA(IPOINT+1),BETAG(IPOINT+1),
     &ETAG(IPOINT+1),XK(IPOINT))
C
C  Reinitialisation de certaine valeurs
C
      J=IPOR
      IPORTION=IPOR
      INF=0
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations au point de transition (éq. 3.37).
C
      I=I+1
  720 J=J+1
C
      INF=INF+1
C
      IPORTION=IPORTION+1
      IF(INF.EQ.1) ISIGNE=1
      IF(INF.EQ.2) ISIGNE=-1
      A(I,J)=ISIGNE*F1E(XK(IPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=ISIGNE*F2E(XK(IPOINT),ZETA(IPORTION))
C
      IF(INF.LT.2) GOTO 720
C
      A(I,IPOINT+4*(NPORTION-1))=FRCFIL(ZETA(IPOINT),BETAG(IPOINT),
     &ETAG(IPOINT),XK(IPOINT))-FRCFIL(ZETA(IPOINT+1),BETAG(IPOINT+1),
     &ETAG(IPOINT+1),XK(IPOINT))
C
C  Reinitialisation de certaine valeurs
C
      J=IPOR
      IPORTION=IPOR
      INF=0
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil au point
C  de transition (éq. 3.38).
C
      I=I+1
      J=J+1
      IPORTION=IPORTION+1
C
      A(I,J)=-F1D(XK(IPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=-F2D(XK(IPOINT),ZETA(IPORTION))
C
      A(I,IPOINT+4*(NPORTION-1))=ELGAME(XK(IPOINT))-ELGFIL(ZETA
     &(IPORTION),BETAG(IPORTION),ETAG(IPORTION),XK(IPOINT))
C
C
C  Dependent du nombre de ressort, on recommence pour le point
C  de transition suivant.
C
      IF(IPOR.LT.(NPORTION-3)) GOTO 700
C#####################################################################
C### Dérivées partielles des conditions limites pour les points de ###
C###### transitions situés du côté droit de la région centrale #######
C#####################################################################
      IPOINT=0
C
C  Compteurs pour le Iieme ressort
C
      IPOR=-1
C
C  Compteurs du No. de point de transition entre les 2 ressorts qui
C  sont considérés, ici on considère le côté droit;
C
  600 IPOINT=IPOINT+1
      JPOINT=NPOINT-(IPOINT-1)
      IPOR=IPOR+1
      J=IPOR+2*(NPORTION-1)
C
      INF=0
C
C  Les compteurs I et J servent pour les différentes positions dans la
C  matrice Jacobienne.
C
      IPORTION=IPOR
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements au point de transition.
C
      I=I+1
  610 J=J+1
C
      INF=INF+1
C
      IPORTION=IPORTION+1
      IF(INF.EQ.1) ISIGNE=1
      IF(INF.EQ.2) ISIGNE=-1
      A(I,J)=ISIGNE*F1D(XK(JPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=ISIGNE*F2D(XK(JPOINT),ZETA(IPORTION))
C
      IF(INF.LT.2) GOTO 610
C
      A(I,JPOINT+4*(NPORTION-1))=ELGFIL(ZETA(IPOINT),BETAD(IPOINT),
     &ETAD(IPOINT),XK(JPOINT))-ELGFIL(ZETA(IPOINT+1),BETAD(IPOINT+1),
     &ETAD(IPOINT+1),XK(JPOINT))
C
C  Reinitialisation de certaine valeurs
C
      J=IPOR+2*(NPORTION-1)
      IPORTION=IPOR
      INF=0
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations au point de transition.
C
      I=I+1
  620 J=J+1
C
      INF=INF+1
C
      IPORTION=IPORTION+1
      IF(INF.EQ.1) ISIGNE=1
      IF(INF.EQ.2) ISIGNE=-1
      A(I,J)=ISIGNE*F1E(XK(JPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=ISIGNE*F2E(XK(JPOINT),ZETA(IPORTION))
C
      IF(INF.LT.2) GOTO 620
C
      A(I,JPOINT+4*(NPORTION-1))=FRCFIL(ZETA(IPOINT),BETAD(IPOINT),
     &ETAD(IPOINT),XK(JPOINT))-FRCFIL(ZETA(IPOINT+1),BETAD(IPOINT+1),
     &ETAD(IPOINT+1),XK(JPOINT))
C
C  Reinitialisation de certaine valeurs
C
      J=IPOR+2*(NPORTION-1)
      IPORTION=IPOR
      INF=0
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil au point
C  de transition.
C
      I=I+1
      J=J+1
      IPORTION=IPORTION+1
C
      A(I,J)=-F1D(XK(JPOINT),ZETA(IPORTION))
      A(I,J+NPORTION-1)=-F2D(XK(JPOINT),ZETA(IPORTION))
C
      A(I,JPOINT+4*(NPORTION-1))=ELGAME(XK(JPOINT))-ELGFIL(ZETA
     &(IPORTION),BETAD(IPORTION),ETAD(IPORTION),XK(JPOINT))
C
C
C  Dependent du nombre de ressort, on recommence pour le point
C  suivant de transition.
C
      IF(IPOR.LT.(NPORTION-3)) GOTO 600
C
C
  900 CONTINUE
C
C
      IF(NPORTION.EQ.11) GOTO 950
C
C#####################################################################
C### Dérivées partielles des conditions limites pour les bornes de ###
C###### de la région centrale lorsqu'il s'agit d'une région de #######
C####################### MICRO-glissement ############################
C
C  Première borne
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements à la première borne (éq.3.39).
C
      A(I,NPORTION-1)=F1D(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=F2D(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=ELGFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     &ETAG(NPORTION-1),XB1)-ELGFIL(ZETA(NPORTION),BTM,ETM,XB1)
      A(I,JDIM-1)=-F1D(XB1,ZETA(NPORTION))
      A(I,JDIM)=-F2D(XB1,ZETA(NPORTION))
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations à la première borne (éq. 3.40).
C
      A(I,NPORTION-1)=F1E(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=F2E(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=FRCFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     &ETAG(NPORTION-1),XB1)-FRCFIL(ZETA(NPORTION),BTM,ETM,XB1)
      A(I,JDIM-1)=-F1E(XB1,ZETA(NPORTION))
      A(I,JDIM)=-F2E(XB1,ZETA(NPORTION))
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil à la
C  première borne (éq. 3.41).
C
      A(I,NPORTION-1)=-F1D(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=-F2D(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=ELGAME(XB1)-ELGFIL(ZETA(NPORTION-1),BETAG
     &(NPORTION-1),ETAG(NPORTION-1),XB1)
C
C
C  Deuxième borne
C
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements à la deuxième borne (éq.3.42).
C
      A(I,3*(NPORTION-1))=F1D(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=F2D(XB2,ZETA(NPORTION-1))
      A(I,JDIM-2)=ELGFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     &ETAD(NPORTION-1),XB2)-ELGFIL(ZETA(NPORTION),BTM,ETM,XB2)
      A(I,JDIM-1)=-F1D(XB2,ZETA(NPORTION))
      A(I,JDIM)=-F2D(XB2,ZETA(NPORTION))
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations à la deuxième borne (éq. 3.43).
C
      A(I,3*(NPORTION-1))=F1E(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=F2E(XB2,ZETA(NPORTION-1))
      A(I,JDIM-2)=FRCFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     &ETAD(NPORTION-1),XB2)-FRCFIL(ZETA(NPORTION),BTM,ETM,XB2)
      A(I,JDIM-1)=-F1E(XB2,ZETA(NPORTION))
      A(I,JDIM)=-F2E(XB2,ZETA(NPORTION))
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil à la
C  deuxième borne (éq. 3.44).
C
      A(I,3*(NPORTION-1))=-F1D(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=-F2D(XB2,ZETA(NPORTION-1))
      A(I,JDIM-2)=ELGAME(XB2)-ELGFIL(ZETA(NPORTION-1),BETAD
     &(NPORTION-1),ETAD(NPORTION-1),XB2)
C
      GOTO 999
C
C
  950 CONTINUE
C
C#####################################################################
C### Dérivées partielles des conditions limites pour les bornes de ###
C###### de la région centrale lorsqu'il s'agit d'une région de #######
C####################### MACRO-glissement ############################
C
C  Première borne
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements à la première borne (éq.3.45).
C
      A(I,NPORTION-1)=F1D(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=F2D(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=ELGFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     &            ETAG(NPORTION-1),XB1)
      A(I,JDIM)=-1.0D0
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations à la première borne (éq. 3.46).
C
      A(I,NPORTION-1)=F1E(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=F2E(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=FRCFIL(ZETA(NPORTION-1),BETAG(NPORTION-1),
     &            ETAG(NPORTION-1),XB1)
      A(I,JDIM-1)=-1.0D0
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil à la
C  première borne (éq. 3.47).
C
      A(I,NPORTION-1)=-F1D(XB1,ZETA(NPORTION-1))
      A(I,2*(NPORTION-1))=-F2D(XB1,ZETA(NPORTION-1))
      A(I,JDIM-3)=ELGAME(XB1)-ELGFIL(ZETA(NPORTION-1),BETAG
     &(NPORTION-1),ETAG(NPORTION-1),XB1)
C
C
C  Deuxième borne
C
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la compatibilité
C  géométrique des déplacements à la deuxième borne (éq.3.48).
C
      A(I,3*(NPORTION-1))=F1D(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=F2D(XB2,ZETA(NPORTION-1))
      A(I,JDIM-3)=ICOTE*(2.0D0*PI)*(XB2-XB1)+BTM
      A(I,JDIM-2)=ELGFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     &ETAD(NPORTION-1),XB2)-DR2H(XB2,XB1,BTM)
      A(I,JDIM-1)=-(XB2-XB1)
      A(I,JDIM)=-1.0D0
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la continuité
C  des déformations à la deuxième borne (éq. 3.49).
C
      A(I,3*(NPORTION-1))=F1E(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=F2E(XB2,ZETA(NPORTION-1))
      A(I,JDIM-3)=ICOTE*2.0D0*PI
      A(I,JDIM-2)=FRCFIL(ZETA(NPORTION-1),BETAD(NPORTION-1),
     &ETAD(NPORTION-1),XB2)-ICOTE*2.0D0*PI
      A(I,JDIM-1)=-1.0D0
C
      I=I+1
C
C  Dérivée partielle de la condition limite qui impose la différence
C  entre le déplacement de la surface de l'âme et celui du fil à la
C  deuxième borne (éq. 3.50).
C
      A(I,3*(NPORTION-1))=-F1D(XB2,ZETA(NPORTION-1))
      A(I,4*(NPORTION-1))=-F2D(XB2,ZETA(NPORTION-1))
      A(I,JDIM-2)=ELGAME(XB2)-ELGFIL(ZETA(NPORTION-1),BETAD
     &(NPORTION-1),ETAD(NPORTION-1),XB2)
C
  999 RETURN
      END
