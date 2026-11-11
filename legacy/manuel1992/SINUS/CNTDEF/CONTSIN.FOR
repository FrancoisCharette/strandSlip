$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement, la dissipation d'énergie sur     %
C une longueur d'onde complète et l'analyse d'un demi-pas en           %
C particulier pour la flèche sinusoidale, selon le MODELE AVEC         %
C CONTINUITE DE DEFORMATION.                                           %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM CONTSIN
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      EXTERNAL VMIN,DMACRO,APPBRN
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CONV/ICONVERG
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      XACC=1.0D-9
      XTOL=1.0D-6
      DSPTOTAL=0.0D0
  800 DSPTMP=0.0D0
C
      CALL ENSNCONT(ICHOIX)
C
C Selon le choix du calcul, on initialise le ou les demi-pas considérés
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
C Détermine le signe selon la convention de signe de la page 41
C
      VCOTE=DCOS(2.0D0*PI*XM+THETA)
      ICOTE=-1
      IF(VCOTE.GT.0.0) ICOTE=1
C
      FRCMIN=GOLDEN(XINF,XM,XSUP,VMIN,XTOL,XMIN)
      IF(DABS(FRCMIN).LE.1.0D0) THEN
      WRITE(*,'(//,1X,''Pas de macro-glissement dans la demi pas '',
     &''XINF='',F5.2,1X,''a XSUP='',F5.2)') XINF,XSUP
      PAUSE 'Pressez ENTER pour continuer'
      IF(ICHOIX.EQ.1) GOTO 900
      IF(ICHOIX.EQ.3) GOTO 700
      GOTO 800
      END IF
C
C    Fin d'entrée des données
C
      XB1=RTFLSP(APPBRN,XINF,XM-.03,XACC)! 1ère borne de macro-gliss.
      IF(ICONVERG.EQ.1) GOTO 910
      XB2=RTFLSP(APPBRN,XM+0.03,XSUP,XACC)! 2ème borne de macro-gliss.
C
C
  910 IF(ICONVERG.EQ.1) THEN
      ICONVERG=0
      WRITE(*,'(3X,''XINF= '',F5.2,3X,''XSUP='',F5.2,/)') XINF,XSUP
C
      WRITE(*,'(/,3X,''Entrez l approx. de XB1:'',\)')
      READ (*,*) XB1
C
      WRITE(*,'(/,3X,''Entrez l approx. de XB2:'',\)')
      READ (*,*) XB2
C
      END IF
C
      XIC=0.0D0
      PSIC=0.0D0
C
      CALL NEWT(XB1,XB2,XIC,PSIC)
C
      IF(ICONVERG.EQ.1) GOTO 910
C
      IF(ICHOIX.EQ.2) RDEP=(DEPAME(XMIN)-DEPH(XMIN,XB1,XIC,PSIC))
     &                     /DEPAME(XMIN)
C
      CALL QROMB(DUM0,DUM1,XB1,XIC,PSIC,DMACRO,XB1,XB2,DSP)
      DSPTMP=DSPTMP+DSP
C
      CALL ECSNCONT(ICHOIX,XB1,XB2,XIC,PSIC,DSP,DSPTOTAL,RDEP)
C
      IF(ICHOIX.EQ.4) GOTO 999
C
      PAUSE 'Pressez ENTER pour continuer'
C
      IF(XM.LT.WLBAR/4.0D0-.6.AND.ICHOIX.EQ.1) GOTO 900
C
      DSPTOTAL=4.0D0*DSPTMP
C
      CALL ECSNCONT(ICHOIX,XB1,XB2,XIC,PSIC,DSP,DSPTOTAL,RDEP)
C
  999 STOP
      END
