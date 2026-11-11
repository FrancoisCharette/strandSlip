$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement et la dissipation d'énergie       %
C dans un demi-pas pour la flèche ayant un rayon de courbure           %
C constant, selon le MODELE DE HARDY                                   %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM HARDRHOB
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      EXTERNAL FRICTION,DMACRO
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      XACC=1D-10
C
      CALL ENTHARD
C
      XB1=RTSEC(FRICTION,XINF,XM,XACC) ! Première borne de macro-gliss.
C
      XB2=RTSEC(FRICTION,XM,XSUP,XACC) ! Deuxième borne de macro-gliss.
C
      PSIH=DEPAME(XB1) ! Equation 2.16
C
      XIH=-ICOTE*PI*(XB2-XB1) ! Equation 2.17 sous forme adimensionnelle
C
C Rapport relatif de différence maximale de déplacement
C
      RDEP=(DEPAME(XM)-DEPH(XM,XB1,XIH,PSIH))/DEPAME(XM)
C
C Dissipation d'énergie pour le demi-pas considéré
C
      CALL QROMB(DUM0,DUM1,XB1,XIH,PSIH,DMACRO,XB1,XB2,DSP)
C
C Affichage à l'écran des resultats
C
      CALL ECRHARD(XB1,XB2,XIH,PSIH,DSP,RDEP)
C
      STOP
      END
