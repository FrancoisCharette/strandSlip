$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction calcul la valeur de l'intégrand pour la dissipation   C
C d'énergie due au MACRO-glissement. Equation A.45 pour les modèles    C
C SANS complaisance ou première intégrale de l'équation A.53 pour le   C
C modèle AVEC complaisance                                             C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DMACRO(DUM0,DUM1,XB1,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      DIFDEP=DABS(DEPAME(XF)-DEPH(XF,XB1,BTA,TA))
C
      DMACRO=4.0D0*DIFDEP
C
      END
