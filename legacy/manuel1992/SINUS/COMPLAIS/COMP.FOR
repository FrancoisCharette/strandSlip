$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui détermine les différents paramètres des portions     C
C linéaire de la multi-linéarisation de la courbe f δ. (Voir p. 46)    C
C Modèle AVEC complaisance.                                            C
C======================================================================C
C
      SUBROUTINE COMP(NPORTION)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAXMIC=10)
C
      COMMON/MAT1/ZETA(NMAXMIC),XCOMP(NMAXMIC+1),YCOMP(NMAXMIC+1)
      COMMON/COMPLAIS/EN
C
C  Valeurs qui demeure constante
C
      XCOMP(1)=0.0D0
      YCOMP(1)=0.0D0
C
      PORTION=1.0D0/NPORTION
C
C  Détermine les points initiales de YCOMP
C
      DO I=1,NPORTION
         YCOMP(I+1)=YCOMP(I)+PORTION
         IF(I.EQ.NPORTION) YCOMP(I+1)=1.0D0
      END DO
C
C  Détermine les points YCOMP corrigés, XCOMP et les pentes des
C  différentes portions linéaire.
C
      DO I=1,NPORTION
C
         YCOMP(I+1)=(YCOMP(I+1)+(1.5D0*I-1.0D0))/(1.5D0*I)
C
         XCOMP(I+1)=(3.0D0/2.0D0)*(1.0D0-(1.0D0-
     &                  YCOMP(I+1))**(EN))
C
         ZETA(I)=(XCOMP(I+1)-XCOMP(I))/
     &               (YCOMP(I+1)-YCOMP(I))
C
      END DO
C
      RETURN
      END
