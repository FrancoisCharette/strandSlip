$DEBUG
$NOFLOATCALLS
$STORAGE:2
C
C  CE PROGRAMME CALCUL LA RIGIDITE D'UN TORON EN FONCTION
C  DE `X', POUR UNE DEFLEXION SUIVANT UN RAYON DE COURBURE CONSTANT,
C  SELON LES EQUATIONS DEVELOPPE DANS LE RAPPORT #1.
C
      PROGRAM RAYON
      IMPLICIT DOUBLE PRECISION (A-F)
      IMPLICIT DOUBLE PRECISION (P-X)
      DIMENSION THETA(50),FMXZ(50),FMXY(50),TMX(50),FX(50),
     +FY(50),FZ(50)
C
      OPEN(1,FILE='RESRAY.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
      OPEN(2,FILE='DONRAY.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
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
      READ(3,1) RF
      READ(3,1) EF
      READ(3,1) TI
      READ(3,1) RA
      READ(3,1) EA
      READ(3,1) CPN
      READ(3,1) CFL
      READ(3,1) RIEN
      READ(3,1) RHO
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
C   La longueur du pitch ce calcul avec l equation 13
C
      PITCH=(2*PI*RA)/DTAN(ALPHA)
C
C   L aire de la section du fil ce calcul de la facon suivante
C
      AF=PI*RF**2
C 
C   La pression d appuie se calcul selon l'equation 12.
C
      Q=(TI*(DSIN(ALPHA))**2)/RA
C
C   Rayon de courbure critique se calcul selon l'equation 14.
C
      RHOC=(RA*F*EF*AF)/(TI*DSIN(ALPHA)*CFL)
C
C   Maintenant on peut calculer le rapport des rayons de courbure
C   
      RHOR=RHO/RHOC
C
C  La constante Gamma est determine selon l'equation 
C
      GAM=(TI*DSIN(ALPHA)*CFL)/(EF*AF)
C
C  Ici on calcul le produit des constante de l'equation 10
C
      CST9=(RA*F*EF*AF*DCOS(ALPHA)*2*PI)/(Q*RHO*PITCH)
C
C
C  A partir d ici, les iterations pour chaque fil debute
C  
C
  370 DO 110 I=1,NFIL
C
C  Calcul la valeur du coefficient de friction a l'endroit designe
C  equation 10
C
      CA9=DCOS((2*PI*X)/PITCH+THETA(I))
      CFX=CST9*CA9
C
C  dependent de la valeur obtenue, le programme calcul l elongation
C  selon le cas,
C
      IF(CFX.LT.0) GOTO 300
      IF(CFX.LE.CFL) THEN
C   Elongation selon l equation 15
          EX=(GAM/RHOR)*DSIN((2*PI*X)/PITCH+THETA(I))
          GOTO 310
      ENDIF
C
C  Ici on calcul l elongation la ou il y a du glissement
C  pour les regions ou le coefficient de friction est superieur
C  a la valeur du coefficient limite
C  Premierement on determine les bornes de debut et de fin de
C  glissement.
C
      DX=PITCH/1000
      X4=X
  320 X4=X4+DX
      CA94=DCOS((2*PI*X4)/PITCH+THETA(I))
      CFX4=CST9*CA94
      IF(CFX4.GT.CFL) GOTO 320
      X3=X
  330 X3=X3-DX
      CA93=DCOS((2*PI*X3)/PITCH+THETA(I))
      CFX3=CST9*CA93
      IF(CFX3.GT.CFL) GOTO 330
C
C   Maintenant que les bornes de glissement X3 et X4 sont determine
C   on applique l'equation 17 pour determiner le deplacement de 
C   chaque borne.
C
      CST19=(GAM*PITCH)/(2*PI*DCOS(ALPHA)*RHOR)
C
C   Deplacement de la borne inferieur
C
      CA193=DCOS(THETA(I))-DCOS((2*PI*X3)/PITCH+THETA(I))
      DX3=CST19*CA193
C
C   Deplacement de la borne superieur
C
      CA194=DCOS(THETA(I))-DCOS((2*PI*X4)/PITCH+THETA(I))
      DX4=CST19*CA194
C
C   Maintenant que les deplacement sont connus, ont peut calculer
C   la constante de l'equation 33.
C
      EOD=(DCOS(ALPHA)*(DX4-DX3))/(X4-X3)-(GAM*PI*(X4-X3))/PITCH
C
C   Avec cette constante on peut determiner la force dans le fil
C   selon l equation 35.
C
      EX=(Q*CFL*(X-X3))/(DCOS(ALPHA)*EF*AF)+EOD
C
C   Finalement on va calculer le moment que le fil genere.
C   
      GOTO 310
C
C     A PARTIR D'ICI ON FAIT LE MEME CALCUL MAIS POUR UN
C     COEFFICIENT DE FRICTION PLUS PETIT QUE LA VALEUR NEGATIVE
C     DU COEFFICIENT LIMITE.
C
  300 DX=PITCH/1000
      CFLN=0-CFL
      IF(CFX.GE.CFLN) THEN 
        EX=(GAM/RHOR)*DSIN((2*PI*X)/PITCH+THETA(I))
        GOTO 310
      ENDIF
      X2=X
  350 X2=X2+DX
      CA92=DCOS((2*PI*X2)/PITCH+THETA(I))
      CFX2=CST9*CA92
      IF(CFX2.LT.CFLN) GOTO 350
      X1=X
  360 X1=X1-DX
      CA91=DCOS((2*PI*X1)/PITCH+THETA(I))
      CFX1=CST9*CA91
      IF(CFX1.LT.CFLN) GOTO 360
C
C   Maintenant que les bornes de glissement X1 et X2 sont determine
C   on applique l'equation 17 pour determiner le deplacement de 
C   chaque borne.
C
      CST19=(GAM*PITCH)/(2*PI*DCOS(ALPHA)*RHOR)
C
C   Deplacement de la borne inferieur
C
      CA191=DCOS(THETA(I))-DCOS((2*PI*X1)/PITCH+THETA(I))
      DX1=CST19*CA191
C
C   Deplacement de la borne superieur
C
      CA192=DCOS(THETA(I))-DCOS((2*PI*X2)/PITCH+THETA(I))
      DX2=CST19*CA192
C
C   Maintenant que les deplacement sont connus, ont peut calculer
C   la constante de l'equation 32.
C
      EOG=(DCOS(ALPHA)*(DX2-DX1))/(X2-X1)+(GAM*PI*(X2-X1))/PITCH
C
C   Avec cette constante on peut determiner la force dans le toron.
C   selon l equation 34
C
      EX=(Q*CFLN*(X-X1))/(DCOS(ALPHA)*EF*AF)+EOG
C
C   MAINTENANT QUE L'ON A ELONGATION DU FIL ON PEUT CALCULER
C   LES FORCES ET LES MOMENTS QU'IL VA CREER DANS LA CABLE.
C   
C
C   LES FORCES SONT
C
  310 FYZ=EX*EF*AF*DSIN(ALPHA)
      FX(I)=EX*EF*AF*DCOS(ALPHA)
      FY(I)=FYZ*DCOS((2*PI*X)/PITCH+THETA(I))
      FZ(I)=FYZ*DSIN((2*PI*X)/PITCH+THETA(I))
C
C   LES MOMENTS SONT
C
      FMXZ(I)=FX(I)*RA*DSIN((2*PI*X)/PITCH+THETA(I))
      FMXY(I)=FX(I)*RA*DCOS((2*PI*X)/PITCH+THETA(I))
      TMX(I)=FYZ*RA
  110 CONTINUE
      FXT=0
      FYT=0
      FZT=0
      FMXZT=0
      FMXYT=0
      TMXT=0
      DO 120 I=1,NFIL
      FXT=FXT+FX(I)
      FYT=FYT+FY(I)
      FZT=FZT+FZ(I)
      FMXZT=FMXZT+FMXZ(I)
      FMXYT=FMXYT+FMXY(I)
      TMXT=TMXT+TMX(I)
  120 CONTINUE
      IF(X.EQ.O) GOTO 125
C
C  Calcul de la rigidite du cable au point etudie
C  selon l equation 40
C
      RIG=FMXZT*RHO
      WRITE(1,21) X,RIG,TMXT,FMXYT,FMXZT,FXT,FYT,FZT
      WRITE(*,21) X,RIG,TMXT,FMXYT,FMXZT,FXT,FYT,FZT
  125 IF(X.LT.XFINAL) THEN
        X=X+DXPAS
        GOTO 370
      END IF
C
C
C
C
      WRITE(2,40) RHO,RA,CPN
   40 FORMAT(2X,'RAYON DE COUR.=',F9.3,/,2X,'R. DU NOYEAU=',F5.3,/,2X,
     +'COEFFICIENT DE POISSON=',F5.3)
      WRITE(2,41) ALPHA,RF,EF
   41 FORMAT(2X,'ANGLE D ENROULEMENT=',F7.5,/,2X,'R. DU TORON=',E9.4,
     +/,2X,'MODULE DE YOUNG DU TORON=',E9.4)
      WRITE(2,42) Q,CL
   42 FORMAT(2X,'PRESSION D APPUI=',E9.4e2,/,2X,
     +'LONGUEUR DU CABLE=',F9.3)
      WRITE(2,43) RHOC,CFL,PITCH
   43 FORMAT(2X,'RAYON CRITIQUE=',E9.4,/,2X,'COEFF. F=',F7.4,/,2X,
     +'PITCH=',F7.4)
      WRITE(2,44) AF,DXPAS,DX,CST9
   44 FORMAT(2X,'AIRE DU TORON=',E9.4,/,2X,'INCREMENT EN X=',F9.5,
     +/,2X,'INCREMENT EN XPAS=',F9.5,/,2X,'CONSTANTE EQ9=',E12.7)
      WRITE(2,45) NFIL,EA,F
   45 FORMAT(2X,'NOMBRE DE FIL:',I2,/,2X,'MOD. DE YOUG DU NOYEAU=',
     +E9.4,/,2X,'F SELON EQUATION 2b=',E9.4)
      WRITE(2,46) TI,RHOR,GAM
   46 FORMAT(2X,'TENSION DANS LE FIL=',E9.4,/,2X,'RAPPORT DE RAYON=',
     +E9.4,/,2X,'GAMMA SELON EQUATION 17=',E9.4)
   21 FORMAT(1X,F8.4,1X,F10.4,2X,F6.4,1X,F6.4,1X,F8.3,2X,F6.4,1X,
     +F6.3,1X,F8.3)
C
      CLOSE(1)
      CLOSE(2) 
      CLOSE(3)
      STOP
      END
