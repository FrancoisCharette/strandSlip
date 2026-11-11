$DEBUG
$STORAGE:2
C======================================================================C
C Cette sousroutine détermine les différents paramètres d'entrés       C
C pour le modèle de HARDY avec la flèche sinusoidale.                  C
C======================================================================C
C
      SUBROUTINE ENSNHARD(ICHOIX)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      UN=1.0D0
      PI=DACOS(-UN)
C
  110 WRITE(*,'(/////////,3X,''Ce programme peut déterminer:'')')
C
      WRITE(*,'(////,6X,''1. La dissipation d énergie d un fil sur'',
     &'' toute la longueur'',/,8X,'' d onde (pour THETAi=90 deg).'',//,
     &6X,''2. Le rapport relatif de différence maximale de''
     &,/,9X,''déplacement (pour THETAi=0 deg).'',//,6X,
     &''3. Analyser un demi-pas en particulier (pour THETAi=90 deg).''
     &)')
C
  100 WRITE(*,'(///,9X,''Entrez votre choix:'',\)')
      READ(*,*,ERR=100) ICHOIX
      IF(ICHOIX.LT.1.OR.ICHOIX.GT.3) GOTO 110
C
      THETA=PI/2.0D0
      IF(ICHOIX.EQ.2) THETA=0.0D0
C
  120 WRITE(*,'(/,9X,''Entrez un nombre pair de pas par longueur'',
     &'' d onde:'',\)')
      READ (*,*,ERR=120) WLBAR
C
  130 WRITE(*,'(/,9X,''Entrez l amplitude adimensionnelle:'',\)')
      READ (*,*,ERR=130) ABAR
      IF(ABAR.LE.1.0D0) GOTO 130
C
C Calcul des autres facteurs adimensionnelles pour faciliter les calculs
C
      PP=WLBAR+1.0D0
      PN=WLBAR-1.0D0
      PPA=PP/WLBAR
      PPB=PN/WLBAR
      PP1=2.0D0*PI*PPA
      PN1=2.0D0*PI*PPB
C
      RETURN
      END
