$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui calculs les déplacements, déformations et rapports   C
C de friction du fil le long du demi-pas considéré. Modèles SANS       C
C complaisance.                                                        C
C======================================================================C
C
      SUBROUTINE SORTIE(XB1,XB2,XI,PSI)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale.
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant.
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      OPEN(2,FILE='DEP.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(3,FILE='ELG.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(4,FILE='FRC.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
C
      WRITE(*,'(///,1X,''POSITION EN X'',9X,''DEP. FIL'',11X,
     &''DEF. FIL'',8X,''RAP. DE FRICTION'',/)')
C
      X=XINF
      DX=0.001D0
C
 1000 CONTINUE
C
      DAME=DEPAME(X)
      EAME=ELGAME(X)
      FAME=FRCAME(X)/(2.0D0*PI)
C
      IF(X.GT.XB1.AND.X.LT.XB2) THEN
            DFIL=DEPH(X,XB1,XI,PSI)
            EFIL=DR2H(X,XB1,XI)
            FFIL=ICOTE*1.0D0
      ELSE
            DFIL=DAME
            EFIL=EAME
            FFIL=FAME
      END IF
C
      WRITE(*,10) X,DFIL,EFIL,FFIL
      WRITE(2,20) X,DAME,DFIL
      WRITE(3,20) X,EAME,EFIL
      WRITE(4,20) X,FAME,FFIL
   10 FORMAT(2X,F9.4,2X,3E20.8)
   20 FORMAT(1X,F7.4,2X,E16.8,2X,E16.8)
C
      X=X+DX
C
      IF(X.LE.XSUP+0.1D-8) GOTO 1000
C
      CLOSE(2)
      CLOSE(3)
      CLOSE(4)
C
      RETURN
      END
