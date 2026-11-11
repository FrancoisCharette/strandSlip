$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui affiche à l'écran les différents résultats pour le   C
C modèle AVEC complaisance avec la flèche sinusoidale.                 C
C======================================================================C
C
      SUBROUTINE ECSNZETA(ICHOIX,BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,
     &ETM,DSP,DSPTOTAL,RDEP)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      IF(DSPTOTAL.NE.0D0) GOTO 800
C
      IF(ICHOIX.EQ.2.OR.ICHOIX.EQ.3.) THEN
C
      WRITE(*,'(/,25X,''MODELE AVEC COMPLAISANCE'')')
      WRITE(*,'(24X,''pour la flèche sinusoidale'')')
C
      WRITE(*,'(/,26X,''****** SOLUTION ******'',/)')
C
      END IF
C
      IF(ICHOIX.EQ.1.AND.DSPTOTAL.EQ.0.0D0) WRITE(*,'(//////)')
C
      WRITE(*,'(1X,''Pour l amplitude adimensionnelle ='',F5.2,/,
     &1X,''un nombre de pas dans la longueur d onde ='',F5.1,/,1X,
     &''et un facteur de complaisance GAMMA1 ='',F5.3,/,1X,
     &''avec la position initiale THETAi = '',
     &F7.5,'' rad. et'',/,1X,''pour le demi-pas XINF ='',F5.2,
     &'' à XSUP ='',F5.2)') ABAR,WLBAR,GAM1,THETA,XINF,XSUP
C
      WRITE(*,'(/,1X,''Les 4 inconnues de la région centrale sont:'',
     &/)')
C
      WRITE(*,60) XB1,XB2,BTM,ETM
   60 FORMAT(3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'BTM=',D14.8,2X,
     &'ETM=',D14.8)
C
      IF(ICHOIX.EQ.2) THEN
        WRITE(*,'(3X,''-> les valeurs des autres inconnues sont '',
     &''sauvegardées dans INCONNUS.DAT'')')
        WRITE(*,'(/, 1X,''et le rapport relatif de différence'',
     &'' maximale de déplacement ='',E14.8,//)') RDEP
      CALL INCONNUS(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM)
           ICHOIX=4
            GOTO 999
      END IF
C
      WRITE(*,41) DSP
   41 FORMAT(/,3X,'Energie dissipée dans le demi-pas =',E14.8)
C
      IF(ICHOIX.EQ.1.AND.DSPTOTAL.EQ.0.0D0) WRITE(*,'(////)')
C
      IF(ICHOIX.EQ.3) THEN
C
      CALL INCONNUS(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM)
C
      WRITE(*,'(3X,''(Voir ENERGY.DAT pour details)'')')
      WRITE(*,'(/,3X,''-> les valeurs des autres inconnues sont '',
     &''sauvegardées dans INCONNUS.DAT'')')
   20 WRITE(*,'(//,3X,''Désirez-vous faire calculer le déplacement,''
     &,'' la déformation et le rapport'',/,3X,''de friction le'',
     &'' long du demi-pas (0=>OUI, 1=>NON):'',\)')
      READ (*,*,ERR=20) ISORTIE
C
      IF(ISORTIE.LT.0.5) CALL SORTZETA(BETAG,ETAG,BETAD,ETAD,XK,XB1,
     &                               XB2,BTM,ETM)

C
      ICHOIX=4
      END IF
C
  800 IF(DSPTOTAL.NE.0.0) THEN
C
      WRITE(*,'(///,25X,''MODELE AVEC COMPLAISANCE'')')
      WRITE(*,'(24X,''pour la flèche sinusoidale'')')
C
      WRITE(*,'(//,26X,''****** SOLUTION ******'',///)')
C
      WRITE(*,'(1X,''Pour l amplitude adimensionnelle ='',F5.2,/,
     &1X,''un nombre de pas dans la longueur d onde ='',F5.1,/,1X,
     &''et un facteur de complaisance GAMMA1 ='',F5.3,/,1X,
     &''avec la position initiale THETAi = '',
     &F7.5,'' rad.'',////)') ABAR,WLBAR,GAM1,THETA
C
       WRITE(*,'(3X,''L énergie dissipée adimensionnelle totale'',
     &'' par ce fil'',/,3X,''tout le long de la longueur d onde = '',
     &E14.8,//)') DSPTOTAL
C
      END IF
C
  999 RETURN
      END
