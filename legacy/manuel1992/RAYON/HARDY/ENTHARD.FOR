$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui initialise les diverses constantes utilisées ainsi   C
C que le rayon de courbure imposé, modèle de HARDY.                    C
C======================================================================C
C
      SUBROUTINE ENTHARD
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,RHOB
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      UN=1.0D0
C
      PI=DACOS(-UN)
      THETA=PI/2.0D0  ! Si théta est changer, il faut changer XINF et
C                       XSUP en conséquence.
C
C On considere le premier demi-pas du fil theta = 90 deg.
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
  100 WRITE(*,'(/,1X,''Entrez le rayon de courbure adim.:'',\)')
      READ (*,*) RHOB
C
      IF(ICOTE*(FRICTION(XM)).LE.0.0D0) THEN
      WRITE(*,'(//,1X,''Pas de macro-glissement dans la demi-pas '',
     &''XINF='',F5.2,1X,''a XSUP='',F5.2)') XINF,XSUP
      PAUSE 'Pressez ENTER pour continuer'
      GOTO 100
      END IF
C
      RETURN
      END
