$DEBUG
$NOFLOATCALLS
$STORAGE:2
C
      PROGRAM DEPLACEMENT
C
C  CE PROGRAMME MONTRE LA FORME DE LA VARIATION DU DEPLACEMENT.
C  IL UTILISE L EQUATION 23 DU RAPPORT DE PROJET-1. LE FICHIER 
C  "ENTRE.DAT" EST NECESSAIRE POUR INITIALISE LES VARIABLES.
C
      IMPLICIT DOUBLE PRECISION (A-F)
      IMPLICIT DOUBLE PRECISION (P-X)
      DIMENSION THETA(50),FMXZ(50),FMXY(50),TMX(50),FX(50),
     +FY(50),FZ(50)
C
      OPEN(1,FILE='D_RESFIN.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
      OPEN(3,FILE='ENTRE.DAT',ACCESS='SEQUENTIAL',STATUS='OLD')
      UN=1D0
      PI=DACOS(-UN)
C
      READ(3,1) CL
      READ(3,2) NFIL
      THETA(1)=0 
      DO 100 I=2,NFIL
      M=I-1
      THETA(I)=THETA(M)+(2*PI)/NFIL
      WRITE(*,4) I,THETA(I)
  100 CONTINUE
    4 FORMAT(3X,I2,6X,F9.4)
      READ(3,1) ALPHA
      READ(3,1) RT
      READ(3,1) ET
      READ(3,1) TI
      READ(3,1) RN
      READ(3,1) EN
      READ(3,1) CPN
      READ(3,1) CFL
      READ(3,1) WL
      READ(3,1) AMP
      READ(3,2) NPAS
      READ(3,1) XDEPART
      READ(3,1) XFINAL
    1 FORMAT(1X,D14.8)
    2 FORMAT(1X,I6)
C
C    FIN D ENTRE DES DONNEES
C
      DXPAS=CL/NPAS
      X=XDEPART
C
C   EQUATION 3
C
      F=(1-CPN*(DTAN(ALPHA))**2)*(DCOS(ALPHA))**2
C
C   La longueur du pas ce calcul avec l equation 13
C
      PITCH=(2*PI*RN)/DTAN(ALPHA)
C
C   L aire de la section du toron ce calcul de la facon suivante
C
      AT=PI*RT**2
C 
C   La pression d appuie se calcul selon l'equation 12.
C
      Q=(TI*(DSIN(ALPHA))**2)/RN
C
C   Amplitude critique se calcul selon l'equation 21.
C
      AMPC=(((WL/(2*PI))**2)*TI*DSIN(ALPHA)*CFL)/(RN*F*ET*AT)
C
C   Maintenant on peut calculer le rapport de l'amplitude divise
C   par l'amplitude critique.
C
      AMPR=AMP/AMPC
C
C  La constante Gamma est determine avec l'equation
C
      GAM=(TI*DSIN(ALPHA)*CFL)/(ET*AT)
C
C
      CST19=(AMPR*GAM*WL*PITCH)/(4*PI*DCOS(ALPHA))
C
C   Deplacement de la borne inferieur
C
  200 DO 300 I=1,NFIL
      CA19=(DSIN(2*PI*X*(1/PITCH-1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL-PITCH)
      CB19=(DSIN(2*PI*X*(1/PITCH+1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL+PITCH)
      DX=CST19*(CA19-CB19)*10000
      WRITE(1,10) X,DX,I,CA19,CB19
      WRITE(*,10) X,DX,I,CA19,CB19
  300 CONTINUE
      X=X+DXPAS
      IF(X.LT.XFINAL) GOTO 200
   10 FORMAT(1X,F7.4,3X,E12.5,3X,I3,3X,E11.5,3X,E11.5)
      CLOSE(1)
      CLOSE(2)
      STOP
      END
