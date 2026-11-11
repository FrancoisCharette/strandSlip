$DEBUG
$STORAGE:2
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C Bloc principale du programme qui détermine le rapport relatif de     %
C différence maximale de déplacement, la dissipation d'énergie sur     %
C une longueur d'onde complète et l'analyse d'un demi-pas en           %
C particulier pour la flèche sinusoidale, selon le MODELE DE HARDY     %
C%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
C
      PROGRAM HARDSIN
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      EXTERNAL FRICTION,DMACRO,VMIN
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
      CALL ENSNHARD(ICHOIX)
C
C Selon le choix du calcul, on initialise le ou les demi-pas considérés
C
      XTOUR=0.0D0-0.5D0
      IF(ICHOIX.EQ.2) XTOUR=((WLBAR/4.0D0)-0.25D0)-0.5D0
  700 IF(ICHOIX.EQ.3) THEN
         WRITE(*,'(/,9X,''Nombre de tour de l origine (XTOUR) :'',\)')
         READ (*,*) XTOUR
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
C Trouve la valeur minimum du coefficient de friction dans le
C demi-pas
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
  950 CONTINUE
C
C    Fin d'entrée des données
C
      XB1=RTFLSP(FRICTION,XINF,XMIN,XACC)! 1ère borne de macro-gliss.
C
      XB2=RTFLSP(FRICTION,XMIN,XSUP,XACC)! 2ème borne de macro-gliss.
C
      PSIH=DEPAME(XB1) ! Equation 2.27
C
      XIH=(DEPAME(XB2)-DEPAME(XB1))/(XB2-XB1)-ICOTE*PI*(XB2-XB1)
C                           Equation 2.28 sous-forme adimensionnelle.
C
      IF(ICHOIX.EQ.2) RDEP=(DEPAME(XMIN)-DEPH(XMIN,XB1,XIH,PSIH))
     &                     /DEPAME(XMIN)
C
      CALL QROMB(DUM0,DUM1,XB1,XIH,PSIH,DMACRO,XB1,XB2,DSP)
      DSPTMP=DSPTMP+DSP
C
      CALL ECSNHARD(ICHOIX,XB1,XB2,XIH,PSIH,DSP,DSPTOTAL,RDEP)
C
      IF(ICHOIX.EQ.4) GOTO 999
C
      PAUSE 'Pressez ENTER pour continuer'
C
      IF(XM.LT.WLBAR/4.0D0-.6.AND.ICHOIX.EQ.1) GOTO 900
C
      DSPTOTAL=4.0D0*DSPTMP
C
      CALL ECSNHARD(ICHOIX,XB1,XB2,XIH,PSIH,DSP,DSPTOTAL,RDEP)
C
  999 STOP
      END
