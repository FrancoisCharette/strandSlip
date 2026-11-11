$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui sauvegarde dans le fichier INCONNUS.DAT les          C
C différentes valeurs de tout les inconnues qui ont été déterminée en  C
C solutionnant le systèmes d'équations non-linéaire par la méthode de  C
C Newton.                                                              C
C======================================================================C
C
      SUBROUTINE INCONNUS(BETAG,ETAG,BETAD,ETAD,XK,XB1,XB2,BTM,ETM)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10)
C
      DIMENSION BETAG(NMAX),ETAG(NMAX),BETAD(NMAX),ETAD(NMAX)
      DIMENSION XK(2*NMAX)
C
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/PORTION/JDIM,NPOINT,NPORTION
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      OPEN(2,FILE='INCONNUS.DAT',ACCESS='SEQUENTIAL',STATUS='UNKNOWN')
C
      WRITE(2,'(1X,''Les paramètres imposés sont:'')')
C
C Bloc utilisé pour la flèche sinusoidale
      WRITE(2,10) ABAR,WLBAR,GAM1,THETA
  10 FORMAT(1X,'ABAR=',E14.8,2X,'WLBAR=',F9.6,2X,'GAM1=',E14.8,
     &2X,'THETAi=',F9.6)
C
C Bloc utilisé pour la flèche ayant un rayon de courbure constant.
C     WRITE(2,10) GAM1,RHOB,THETA
C   10 FORMAT(1X,'GAM1=',E14.8,3X,'RHOB=',F9.6,3X,'THETAi=',F9.6)
C
      WRITE(2,20) NPORTION,NPOINT,XINF,XSUP
   20 FORMAT(1X,'NPORTION=',I2,3X,'NPOINT=',I2,3X,'XINF=',D16.10,2X,
     &'XSUP=',D16.10)
C
      WRITE(2,'(/,1X,''Les paramètres de complaisance sont:'')')
      DO I=1,NPORTION-1
         WRITE(2,25) I,XCOMP(I),I,YCOMP(I),I,ZETA(I)
      END DO
   25 FORMAT(1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9,2X,
     &'ZETA(',I2,')=',D14.9)
      WRITE(2,26) NPORTION,XCOMP(NPORTION),NPORTION,YCOMP(NPORTION)
   26 FORMAT(1X,'XCOMP(',I2,')=',D14.9,2X,'YCOMP(',I2,')=',D14.9)
C
      WRITE(2,'(/,1X,''Les inconnues sont:'')')
      DO I=1,NPORTION-1
        WRITE(2,30) I,BETAG(I),I,ETAG(I)
      END DO
   30 FORMAT(1X,'BETAG(',I2,')=',D16.10,2X,'ETAG(',I2,')=',D16.10)
C
      WRITE(2,'(/)')
      DO I=1,NPORTION-1
         WRITE(2,40) I,BETAD(I),I,ETAD(I)
      END DO
   40 FORMAT(1X,'BETAD(',I2,')=',D16.10,2X,'ETAD(',I2,')=',D16.10)
C
      WRITE(2,'(/)')
      DO I=1,NPOINT
         WRITE(2,50) I,XK(I)
      END DO
   50 FORMAT(1X,'XK(',I2,')=',D16.10)
C
      WRITE(2,'(/)')
      WRITE(2,60) XB1,XB2,BTM,ETM
   60 FORMAT(1X,'XB1=',D14.8,2X,'XB2=',D14.8,/,1X,'BTM=',D14.8,2X,
     &'ETM=',D14.8)
C
      CLOSE(2)
C
      RETURN
      END
