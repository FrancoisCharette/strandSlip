$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui calculs les déplacements, déformations et rapports   C
C de friction du fil le long du demi-pas considéré. Pour le modèle     C
C AVEC complaisance.                                                   C
C======================================================================C
C
      SUBROUTINE SORTZETA(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      OPEN(2,FILE='ZETADEP.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(3,FILE='ZETAELG.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(4,FILE='ZETAFRC.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
C
C Fichier de sauvegarde des points de transitions entre 2 ressorts
C
      OPEN(6,FILE='ZETADEPX.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(7,FILE='ZETAELGX.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
      OPEN(8,FILE='ZETAFRCX.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
C
      WRITE(*,'(///,1X,''POSITION EN X'',9X,''DEP. FIL'',11X,
     &''DEF. FIL'',8X,''RAP. DE FRICTION'',/)')
C
      X=XINF
      DX=0.001D0
C
 1000 DAME=DEPAME(X)
      EAME=ELGAME(X)
      FAME=FRCAME(X)/(2.0D0*PI)
C
C S'il y a qu'une région de micro-glissement dans tout le demi-pas,
C alors;
      IF(NPORTION.EQ.1) THEN
         DFIL=DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BTM,ETM,X)
         EFIL=ELGFIL(ZETA(1),BTM,ETM,X)
         FFIL=FRCFIL(ZETA(1),BTM,ETM,X)/(2.0D0*PI)
         GOTO 995
      END IF
C
C S'il y a que trois régions de micro-glissement, alors;
C
      IF(NPORTION.EQ.2) THEN
         IF(X.LT.XB1) THEN
            DFIL=DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAG(1),ETAG(1),X)
            EFIL=ELGFIL(ZETA(1),BETAG(1),ETAG(1),X)
            FFIL=FRCFIL(ZETA(1),BETAG(1),ETAG(1),X)/(2.0D0*PI)
            IF(X.GT.XB1-DX.AND.X.LT.XB1) THEN
               WRITE(6,22) X,DFIL
               WRITE(7,22) X,EFIL
               WRITE(8,22) X,FFIL
            END IF
         END IF
C
         IF(X.GE.XB1.AND.X.LE.XB2) THEN
            DFIL=DEPFIL(XCOMP(2),YCOMP(2),ZETA(2),BTM,ETM,X)
            EFIL=ELGFIL(ZETA(2),BTM,ETM,X)
            FFIL=FRCFIL(ZETA(2),BTM,ETM,X)/(2.0D0*PI)
         END IF
C
         IF(X.GT.XB2) THEN
            DFIL=DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAD(1),ETAD(1),X)
            EFIL=ELGFIL(ZETA(1),BETAD(1),ETAD(1),X)
            FFIL=FRCFIL(ZETA(1),BETAD(1),ETAD(1),X)/(2.0D0*PI)
            IF(X.GT.XB2.AND.X.LT.XB2+DX) THEN
               WRITE(6,22) X,DFIL
               WRITE(7,22) X,EFIL
               WRITE(8,22) X,FFIL
            END IF
         END IF
C
         GOTO 995
      END IF
C
C S'il y a plus que trois régions de micro-glissement, alors;
C
C pour la première région de micro-glissement
C
      IF(X.GE.XINF.AND.X.LT.XK(1)) THEN
         DFIL=DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAG(1),ETAG(1),X)
         EFIL=ELGFIL(ZETA(1),BETAG(1),ETAG(1),X)
         FFIL=FRCFIL(ZETA(1),BETAG(1),ETAG(1),X)/(2.0D0*PI)
         IF(X.GT.XK(1)-DX.AND.X.LT.XK(1)) THEN
               WRITE(6,22) X,DFIL
               WRITE(7,22) X,EFIL
               WRITE(8,22) X,FFIL
         END IF
         WRITE(*,'(2X,''PORTION #1'')')
      END IF
C
C Pour les régions subséquentes de micro-glissement qui sont du côté
C gauche de la région centrale
C
      DO I=1,NPOINT/2-1
         IF(X.GE.XK(I).AND.X.LT.XK(I+1)) THEN
            DFIL=DEPFIL(XCOMP(I+1),YCOMP(I+1),ZETA(I+1),BETAG(I+1),
     &           ETAG(I+1),X)
            EFIL=ELGFIL(ZETA(I+1),BETAG(I+1),ETAG(I+1),X)
            FFIL=FRCFIL(ZETA(I+1),BETAG(I+1),ETAG(I+1),X)/(2.0D0*PI)
            IF(X.GT.XK(I+1)-DX.AND.X.LT.XK(I+1)) THEN
               WRITE(6,22) X,DFIL
               WRITE(7,22) X,EFIL
               WRITE(8,22) X,FFIL
            END IF
            WRITE(*,10) I+1
         END IF
      END DO
C
C Pour la région de micro-glissement qui précède immédiatement la
C région centrale (côté gauche)
C
      IF(X.GE.XK(NPOINT/2).AND.X.LT.XB1) THEN
         DFIL=DEPFIL(XCOMP(NPOINT/2+1),YCOMP(NPOINT/2+1),
     &        ZETA(NPOINT/2+1),BETAG(NPOINT/2+1),ETAG(NPOINT/2+1),X)
      EFIL=ELGFIL(ZETA(NPOINT/2+1),BETAG(NPOINT/2+1),ETAG(NPOINT/2+1),X)
      FFIL=FRCFIL(ZETA(NPOINT/2+1),BETAG(NPOINT/2+1),ETAG(NPOINT/2+1),X)
     &/(2.0D0*PI)
      IF(X.GT.XB1-DX.AND.X.LT.XB1) THEN
         WRITE(6,22) X,DFIL
         WRITE(7,22) X,EFIL
         WRITE(8,22) X,FFIL
      END IF
      WRITE(*,10) NPOINT/2+1
      END IF
C
C Pour la région centrale du demi-pas
C
      IF(X.GE.XB1.AND.X.LT.XB2) THEN
         IF(NPORTION.LT.11) THEN
            DFIL=DEPFIL(XCOMP(NPORTION),YCOMP(NPORTION),ZETA(NPORTION)
     &      ,BTM,ETM,X)
            EFIL=ELGFIL(ZETA(NPORTION),BTM,ETM,X)
            FFIL=FRCFIL(ZETA(NPORTION),BTM,ETM,X)/(2.0D0*PI)
         ELSE
            DFIL=DEPH(X,XB1,BTM,ETM)
            EFIL=DR2H(X,XB1,BTM)
            FFIL=-1.0D0
            WRITE(*,'(2X,''REGION MACRO-GLISSMENT'')')
         END IF
      END IF
C
C Pour la région de micro-glissement qui suit immédiatement la région
C centrale (côté droit)
C
      IF(X.GE.XB2.AND.X.LT.XK(NPOINT/2+1)) THEN
         DFIL=DEPFIL(XCOMP(NPOINT/2+1),YCOMP(NPOINT/2+1),
     &        ZETA(NPOINT/2+1),BETAD(NPOINT/2+1),ETAD(NPOINT/2+1),X)
      EFIL=ELGFIL(ZETA(NPOINT/2+1),BETAD(NPOINT/2+1),ETAD(NPOINT/2+1),X)
      FFIL=FRCFIL(ZETA(NPOINT/2+1),BETAD(NPOINT/2+1),ETAD(NPOINT/2+1),X)
     &/(2.0D0*PI)
            WRITE(*,10) NPOINT/2+1
         IF(X.GT.XB2.AND.X.LT.XB2+DX) THEN
            WRITE(6,22) X,DFIL
            WRITE(7,22) X,EFIL
            WRITE(8,22) X,FFIL
         END IF
      END IF
C
C Pour les régions subséquentes de micro-glissement qui sont du côté
C droit de la région centrale
C
      DO I=NPOINT/2+1,NPOINT-1
         JPOINT=NPOINT-(I-1)
         IF(X.GE.XK(I).AND.X.LT.XK(I+1)) THEN
            DFIL=DEPFIL(XCOMP(JPOINT),YCOMP(JPOINT),ZETA(JPOINT),
     &           BETAD(JPOINT),ETAD(JPOINT),X)
            EFIL=ELGFIL(ZETA(JPOINT),BETAD(JPOINT),ETAD(JPOINT),X)
            FFIL=FRCFIL(ZETA(JPOINT),BETAD(JPOINT),ETAD(JPOINT),X)
     &            /(2.0D0*PI)
         IF(X.GT.XK(I).AND.X.LT.XK(I)+DX) THEN
            WRITE(6,22) X,DFIL
            WRITE(7,22) X,EFIL
            WRITE(8,22) X,FFIL
         END IF
            WRITE(*,10) JPOINT
         END IF
      END DO
C
C Pour la dernière région de micro-glissement
C
      IF(X.GE.XK(NPOINT).AND.X.LE.XSUP) THEN
         DFIL=DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),BETAD(1),ETAD(1),X)
         EFIL=ELGFIL(ZETA(1),BETAD(1),ETAD(1),X)
         FFIL=FRCFIL(ZETA(1),BETAD(1),ETAD(1),X)/(2.0D0*PI)
         IF(X.GT.XK(NPOINT).AND.X.LT.XK(NPOINT)+DX) THEN
            WRITE(6,22) X,DFIL
            WRITE(7,22) X,EFIL
            WRITE(8,22) X,FFIL
         END IF
         WRITE(*,'(2X,''PORTION #1'')')
      END IF
C
C
  995 DIFDEP=DAME-DFIL  ! Différence entre les déplacements
      DIFELG=EAME-EFIL  ! Différence entre les déformations
      DIFFRC=FAME-FFIL  ! Différence entre les rapport de friction
C
      WRITE(*,18) X,DFIL,EFIL,FFIL
      WRITE(2,18) X,DAME,DFIL,DIFDEP
      WRITE(3,18) X,EAME,EFIL,DIFELG
      WRITE(4,18) X,FAME,FFIL,DIFFRC
   18 FORMAT(2X,F9.4,2X,3E20.8)
   10 FORMAT(2X,'PORTION #:',I2)
   22 FORMAT(2X,2E20.8)
C
      X=X+DX
C
      IF(X.LE.XSUP) GOTO 1000
C
      CLOSE(2)
      CLOSE(3)
      CLOSE(4)
      CLOSE(6)
      CLOSE(7)
      CLOSE(8)
C
      RETURN
      END
