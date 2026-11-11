$DEBUG
$STORAGE:2
C===================================================================C
C Sousroutine qui calcul la dissipation d'énergie dans tout le demi C
C pas considéré. La valeur de la dissipation d'énergie dans chacune C
C des régions du demi-pas est sauvegardé dans le fichier ENERGY.DAT.C
C Modèle AVEC complaisance.                                         C
C===================================================================C
C
      SUBROUTINE DISPENRG(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM,DSP)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      EXTERNAL DMICRO,DMACRO
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX)
C
      COMMON/COMPLAIS/EN
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      OPEN(1,FILE='ENERGY.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
C
      WRITE(1,'(1X,''Energie dissipe dans chacune des regions du'',
     &'' demi-pas:'')')
C
      DSP=0.0D0
      IREGION=1
      DUM0=0.0D0
      DUM1=1.0D0
C
C S'il y a qu'une région de micro-glissement dans tout le demi-pas,
C alors;
      IF (NPORTION.EQ.1) THEN
         CALL QROMB(XCOMP(1),YCOMP(1),ZETA(1),BTM,ETM,DMICRO,XINF,XSUP,
     &   DSP)
         WRITE(1,20) IREGION,DSP
         GOTO 999
      END IF
C
C S'il y a que trois régions de micro-glissement, alors;
C
      IF (NPORTION.EQ.2) THEN
         CALL QROMB(XCOMP(1),YCOMP(1),ZETA(1),BETAG(1),ETAG(1),DMICRO,
     &   XINF,XB1,DSPTMP)
         DSP=DSP+DSPTMP
         WRITE(1,20) IREGION,DSPTMP
         CALL QROMB(XCOMP(2),YCOMP(2),ZETA(2),BTM,ETM,DMICRO,
     &   XB1,XB2,DSPTMP)
         DSP=DSP+DSPTMP
         IREGION=IREGION+1
         WRITE(1,20) IREGION,DSPTMP
         CALL QROMB(XCOMP(1),YCOMP(1),ZETA(1),BETAD(1),ETAD(1),DMICRO,
     &   XB2,XSUP,DSPTMP)
         DSP=DSP+DSPTMP
         IREGION=IREGION+1
         WRITE(1,20) IREGION,DSPTMP
         GOTO 999
      END IF
C
C S'il y a plus que trois régions de micro-glissement, alors;
C
C Dissipation d'énergie dans la première région de micro-glissement
C
      CALL QROMB(XCOMP(1),YCOMP(1),ZETA(1),BETAG(1),ETAG(1),DMICRO,XINF
     &,XK(1),DSPTMP)
      DSP=DSP+DSPTMP
      WRITE(1,20) IREGION,DSPTMP
C
C Dissipation d'énergie dans les régions subséquentes de micro-
C glissement qui sont du côté gauche de la région centrale
C
      DO I=1,NPOINT/2-1
         IREGION=IREGION+1
         CALL QROMB(XCOMP(I+1),YCOMP(I+1),ZETA(I+1),BETAG(I+1),ETAG(I+1)
     &              ,DMICRO,XK(I),XK(I+1),DSPTMP)
         DSP=DSP+DSPTMP
         WRITE(1,20) IREGION,DSPTMP
   20    FORMAT(1X,'REG.',I3,'=',E16.8)
      END DO
C
C Dissipation d'énergie dans la région de micro-glissement qui
C précède immédiatement la région centrale (côté gauche)
C
      CALL QROMB(XCOMP(NPOINT/2+1),YCOMP(NPOINT/2+1),ZETA(NPOINT/2+1),
     &BETAG(NPOINT/2+1),ETAG(NPOINT/2+1),DMICRO,XK(NPOINT/2),XB1,DSPTMP)
      DSP=DSP+DSPTMP
      IREGION=IREGION+1
      WRITE(1,20) IREGION,DSPTMP
C
C Dissipation d'énergie dans la région centrale du demi-pas
C
      IF(NPORTION.LT.11) THEN
         CALL QROMB(XCOMP(NPORTION),YCOMP(NPORTION),ZETA(NPORTION),
     &              BTM,ETM,DMICRO,XB1,XB2,DSPTMP)
         DSP=DSP+DSPTMP
      WRITE(1,20) NPORTION,DSPTMP
      ELSE
         CALL QROMB(DUM0,DUM1,XB1,BTM,ETM,DMACRO,XB1,XB2,DSPTMP)
         DSPMAC=DSPTMP+((6.0D0*GAM1)/PI)*(1.0D0/(EN+1.0D0)-1)*(XB2-XB1)
         DMICMAC=((6.0D0*GAM1)/PI)*(1.0D0/(EN+1.0D0)-0.5D0)*(XB2-XB1)
         DSP=DSP+DSPMAC
      WRITE(1,20) NPORTION,DSPMAC
      END IF
C
C Dissipation d'énergie dans la région de micro-glissement qui
C suit immédiatement la région centrale (côté droit)
C
      CALL QROMB(XCOMP(NPOINT/2+1),YCOMP(NPOINT/2+1),ZETA(NPOINT/2+1),
     &BETAD(NPOINT/2+1),ETAD(NPOINT/2+1),DMICRO,XB2,XK(NPOINT/2+1),
     &DSPTMP)
      DSP=DSP+DSPTMP
      IREGION=IREGION+2
      WRITE(1,20) IREGION,DSPTMP
C
C Dissipation d'énergie dans les régions subséquentes de micro-
C glissement qui sont du côté droit de la région centrale
C
      DO I=NPOINT/2+1,NPOINT-1
         IREGION=IREGION+1
         JPOINT=NPOINT-(I-1)
         CALL QROMB(XCOMP(JPOINT),YCOMP(JPOINT),ZETA(JPOINT),BETAD
     &   (JPOINT),ETAD(JPOINT),DMICRO,XK(I),XK(I+1),DSPTMP)
         DSP=DSP+DSPTMP
      WRITE(1,20) IREGION,DSPTMP
      END DO
C
C Dissipation d'énergie dans la dernière région de micro-glissement
C
      CALL QROMB(XCOMP(1),YCOMP(1),ZETA(1),BETAD(1),ETAD(1),DMICRO,
     &XK(NPOINT),XSUP,DSPTMP)
      DSP=DSP+DSPTMP
      WRITE(1,20) IREGION+1,DSPTMP
C
C
      IF(NPORTION.EQ.11) THEN
          DMIC=DSP-DSPMAC+DMICMAC ! Energie dissipée due au micro-
C                                   glissement seulement
          DMAC=DSPMAC-DMICMAC    ! Energie dissipée due au macro-
C                                   glissement seulement
          DSPRAP=(DMAC/DSP)*100   ! % due au macro-glissement
          RAPMICMAC=(DMICMAC/DSPMAC)*100  ! % due au micro-glissement
C                                        dans la région de macro-gliss.
          WRITE(1,45) DSP,DMAC,DMIC,DSPRAP,DSPMAC,DMICMAC,RAPMICMAC
      ELSE
          WRITE(1,46) DSP
      END IF
C
   45 FORMAT(//,1X,'Energie dissipe dans tout le demi-pas=',E14.8,/,
     &1X,'Total due au macro=',E14.8,/,
     &1X,'Total due au micro=',E14.8,/,
     &1X,'% due au macro=',F5.2,/,
     &1X,'Energie dissipe dans la region de macro-glissement=',E14.8,/,
     &1X,'Energie due au micro dans cette region=',E14.8,/
     &1X,'% due au micro dans la region de macro=',F5.2)
   46 FORMAT(//,1X,'Il n y a que du micro-glissement dans ce demi-pas'
     &,/,1X,'Energie dissipe dans tout le demi-pas=',E14.8)
C
  999 CLOSE(1)
      RETURN
      END
