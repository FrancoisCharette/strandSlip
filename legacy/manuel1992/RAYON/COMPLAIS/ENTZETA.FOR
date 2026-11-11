$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui initialise les diverses constantes utilisées ainsi   C
C que le rayon de courbure imposée, modèle avec complaisance.          C
C======================================================================C
C
      SUBROUTINE ENTZETA
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/COMPLAIS/EN
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      UN=1.0D0
      PI=DACOS(-UN)
C
      THETA=PI/2.0D0  ! Si théta est changer, il faut changer XINF et
C                       XSUP en conséquence.
C
C On considère le premier demi-pas du fil THETAi = 90 deg.
C
      XINF=0.0D0
      XSUP=XINF+0.5D0
      XM=(XINF+XSUP)/2.0D0
C
C Détermine le signe selon la convention de signe de la page 41
C
      VCOTE=DCOS(2.0D0*PI*XM+THETA)
      ICOTE=-1
      IF(VCOTE.GT.0.0) ICOTE=1
C
      EN=2.0D0/3.0D0  ! Exposant de la courbe de complaisance.
C
      WRITE(*,'(/,3X,''Entrez le facteur complaisance GAM1:'',\)')
      READ (*,*) GAM1
C
      WRITE(*,'(/,3X,''Entrez le rayon de courbure adim.:'',\)')
      READ (*,*) RHOB
C
C Calcul des autres facteurs adimensionnelles
C
C Exposant utilisé dans les équations du fil
C
      GAMEXP=(4.0D0*PI**2.0D0)/(GAM1)
C
C Constante utilisée pour les équations de déplacement
C
      GAMD1=1.0D0/(2.0D0*PI*RHOB)
C
C Constantes utilisée pour les équations de déformation
C
      GAME1=2.0D0*PI*GAMD1
C
C Constantes utilisée pour les équations de deuxième dérivée
C de déplacement
C
      GAMF1=2.0D0*PI*GAME1
C
      RETURN
      END
