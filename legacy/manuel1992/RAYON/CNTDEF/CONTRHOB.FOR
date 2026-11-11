$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement et la dissipation d'énergie       %
C dans un demi-pas pour la flèche ayant un rayon de courbure           %
C constant, selon le MODELE AVEC CONTINUITE DE DEFORMATION             %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM CONTRHOB
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      EXTERNAL DMACRO,APPBRN
C
      COMMON/CONV/ICONVERG
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      XACC=1D-10
C
      CALL ENTCONT
C
      XB1=RTFLSP(APPBRN,XINF,XM-.03,XACC)
C
      IF (ICONVERG.EQ.1) GOTO 910
C
      XB2=RTFLSP(APPBRN,XM+0.03,XSUP,XACC)
C
  910 IF (ICONVERG.EQ.1) CALL PBCONV(XB1,XB2)
C
      XIC=0.0D0
      PSIC=0.0D0
C
      CALL NEWT(XB1,XB2,XIC,PSIC)
C
      IF(ICONVERG.EQ.1) GOTO 910
C
      RDEP=(DEPAME(XM)-DEPH(XM,XB1,XIC,PSIC))/DEPAME(XM)
C
      CALL QROMB(DUM0,DUM1,XB1,XIC,PSIC,DMACRO,XB1,XB2,DSP)
C
      CALL ECRCONT(XB1,XB2,XIC,PSIC,DSP,RDEP)
C
      STOP
      END
