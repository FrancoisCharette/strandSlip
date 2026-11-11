$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui affiche à l'écran les différents résultats pour le   C
C modèle de HARDY avec la flèche ayant un rayon de courbure constant.  C
C======================================================================C
C
      SUBROUTINE ECRHARD(XB1,XB2,XIH,PSIH,DSP,RDEP)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      WRITE(*,'(/,29X,''MODELE DE HARDY'')')
      WRITE(*,'(12X,''pour la flèche ayant un rayon de courbure '',
     &''constant'')')
C
      WRITE(*,'(//,26X,''****** SOLUTION ******'',/)')
      WRITE(*,'(1X,''Pour le rayon de courbure constant adimension'',
     &''nel ='',F5.3,/,1X''avec la position initiale THETAi = '',
     &F7.5,'' rad. et'',/,1X,''pour le demi-pas XINF ='',F4.2,
     &'' à XSUP ='',F4.2)') RHOB,THETA,XINF,XSUP
C
      WRITE(*,'(//,1X,''Les 4 inconnues sont:'',/)')
C
      WRITE(*,60) XB1,XB2,XIH,PSIH
   60 FORMAT(3X,'XB1=',D14.8,2X,'XB2=',D14.8,/,3X,'XIH=',D14.8,2X,
     &'PSIH=',D14.8)
C
      WRITE(*,'(//,1X,''Les résultats sont:'')')
C
      WRITE(*,41) DSP,RDEP
   41 FORMAT(/,3X,'Energie dissipée dans le demi-pas =',E14.8,
     &/, 3X,'Rapport relatif de différence',
     &' maximale de déplacement =',E14.8)
C
      WRITE(*,'(/,3X,''Désirez-vous faire calculer le déplacement, la'',
     &'' déformation et le rapport'',/,3X,''de friction le'',
     &'' long du demi-pas (0=>OUI, 1=>NON):'',\)')
      READ (*,*) ISORTIE
C
      IF(ISORTIE.LT.0.5) CALL SORTIE(XB1,XB2,XIH,PSIH)
C
      RETURN
      END
