$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui affiche à l'écran les différents résultats pour le   C
C modèle AVEC complaisance avec la flèche ayant un rayon de courbure   C
C constant.                                                            C
C======================================================================C
C
      SUBROUTINE ECRZETA(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,DSP,
     &RDEP)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      WRITE(*,'(/,25X,''MODELE AVEC COMPLAISANCE'')')
      WRITE(*,'(12X,''pour la flèche ayant un rayon de courbure '',
     &''constant'')')
C
      WRITE(*,'(//,26X,''****** SOLUTION ******'',/)')
      WRITE(*,'(1X,''Pour le rayon de courbure constant adimension'',
     &''nel ='',F5.3,/,1X,''avec un facteur de complaisance GAM1 ='',
     &F5.3,/,1X,''pour la position initiale THETAi = '',F7.4,
     &'' rad. et'',/,1X,''le demi-pas XINF ='',F4.2,'' à XSUP ='',F4.2
     &)') RHOB,GAM1,THETA,XINF,XSUP
C
      CALL INCONNUS(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM)
C
      WRITE(*,'(///,1X,''Les résultats sont:'')')
C
      WRITE(*,41) DSP,RDEP
   41 FORMAT(/,3X,'Energie dissipée dans le demi-pas =',E14.8,2X,
     &'(Détails dans ENERGY.DAT)',/, 3X,'Rapport relatif de différence',
     &' maximale de déplacement =',E14.8,//,3X,'Les valeurs des '
     &'inconnues sont sauvegardées dans INCONNUS.DAT',/,)
C
   20 WRITE(*,'(//,3X,''Désirez-vous faire calculer le déplacement,'',
     &'' la déformation et le rapport'',/,3X,''de friction le'',
     &'' long du demi-pas (0=>OUI, 1=>NON):'',\)')
      READ (*,*,ERR=20) ISORTIE
C
      IF(ISORTIE.LT.0.5) CALL SORTZETA(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,
     &BTM,ETM)
C
      RETURN
      END
