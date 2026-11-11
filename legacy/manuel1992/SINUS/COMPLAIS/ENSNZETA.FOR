$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui détermine les différents paramètres d'entrés pour le C
C modèle AVEC complaisance avec la flèche sinusoidale.                 C
C======================================================================C
C
      SUBROUTINE ENSNZETA(ICHOIX)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
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
C
  140 WRITE(*,'(/,9X,''Entrez le facteur de complaisance GAMMA1:'',\)')
      READ (*,*,ERR=140) GAM1
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
C
      GAMEXP=(4.0D0*PI**2.0D0)/GAM1
C
C Déplacements
C
      GAMD1=(ABAR*WLBAR)/(4.0D0*PI)
C
C Déformations
C
      GAME1=GAMD1*((2.0D0*PI)/WLBAR)
C
C Deuxième dérivée du déplacement
C
      GAMF1=GAME1*((2.0D0*PI)/WLBAR)
C
      RETURN
      END
