$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Fonction qui sert à approximer les positions des bornes pour la      C
C méthode de Newton. Modèle avec continuité de déformation, flèche     C
C ayant un rayon de courbure constant.                                 C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION APPBRN(XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
C Calcul la déformation du fil dans la région de glissement nul
C
      TMP1=DSIN(2.0D0*PI*XF+THETA)/RHOB
C
C Evalue la déformation du fil dans la région de macro-glissement
C
      TMP2=-ICOTE*2.0D0*PI*(XM-XF)
C
C Pose que ces déformations sont égales
C
      APPBRN=TMP1-TMP2
C
      END
