$DEBUG
$NOFLOATCALLS
$STORAGE:2
C
C  CE PROGRAMME CALCUL LA RIGIDITE D'UN CABLE TORONNE, EN FONCTION
C  DE `X', POUR UNE DEFLEXION SUIVANT UNE SINUSOIDE PURE, SELON LES
C  EQUATIONS DEVELOPPE DANS LE RAPPORT DE PROJET-1. CE PROGRAMME 
C  LISTE LES ENDROITS OU LE DEPLACEMENT DEBUTE ET FINI AINSI QUE
C  LEUR VALEUR, POUR CHAQUE FIL, A CHAQUE POSITION LE LONG DE X. LE 
C  FICHIER "ENTRE.DAT" EST NECESSAIRE POUR INITIALISE LES VARIABLES.
C
      PROGRAM RIGIDITE
      IMPLICIT DOUBLE PRECISION (A-F)
      IMPLICIT DOUBLE PRECISION (P-X)
      DIMENSION THETA(50),FMXZ(50),FMXY(50),TMX(50),FX(50),
     +FY(50),FZ(50)
C
      OPEN(1,FILE='RESFIN.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
      OPEN(2,FILE='DONNE1.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
      OPEN(3,FILE='ENTRE.DAT',ACCESS='SEQUENTIAL',STATUS='OLD')
C      OPEN(4,FILE='DATA.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
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
C  Ici on calcul le produit des constante de l'equation 19 
C
      CST9=((RN*AMP*F*ET*AT*DCOS(ALPHA))/Q)*((2*PI)/WL)**3
C
C
C  A partir d'ici les iterations pour chaque toron debute
C
C
  370 DO 110 I=1,NFIL
C
C  Calcul la valeur du coefficient de friction a l'endroit designe
C
C
      CA9=(WL/PITCH)*(DCOS((2*PI*X)/PITCH+THETA(I)))*(DSIN((2*PI*X)/WL))
      CB9=(DSIN((2*PI*X)/PITCH+THETA(I)))*(DCOS((2*PI*X)/WL))
      CFX=CST9*(CA9+CB9)
C
C  dependent de la valeur obtenue, le programme calcul l'elongation
C  selon le cas,
C
      IF(CFX.LT.0) GOTO 300
      IF(CFX.LE.CFL) THEN
C  Elongation selon l'equation 22
        EX=AMPR*GAM*DSIN((2*PI*X)/PITCH+THETA(I))*DSIN((2*PI*X)/WL)
        WRITE(*,331) X,I,EX
        GOTO 310
      ENDIF
  331 FORMAT(1X,F9.5,2X,I3,2X,E9.3)  
C
C  Ici on calcul le moment de flexion la ou il y a du glissement
C  pour les regions ou le coeff. de friction est superieur a la
C  valeur du coeff. limite
C  Premierement on determine les bornes de debut et de fin de
C  glissement.
C
      DX=PITCH/10000
      X4=X
  320 X4=X4+DX
      CA94=(WL/PITCH)*(DCOS((2*PI*X4)/PITCH+THETA(I)))*
     %(DSIN((2*PI*X4)/WL))
      CB94=(DSIN((2*PI*X4)/PITCH+THETA(I)))*(DCOS((2*PI*X4)/WL))
      CFX4=CST9*(CA94+CB94)
      IF(CFX4.GT.CFL) GOTO 320
      X3=X
  330 X3=X3-DX
      CA93=(WL/PITCH)*(DCOS((2*PI*X3)/PITCH+THETA(I)))*
     %(DSIN((2*PI*X3)/WL))
      CB93=(DSIN((2*PI*X3)/PITCH+THETA(I)))*(DCOS((2*PI*X3)/WL))
      CFX3=CST9*(CA93+CB93)
      IF(CFX3.GT.CFL) GOTO 330
C
C   Maintenant que les bornes de glissement X3 et X4 sont determine
C   on applique l'equation 23 pour determiner le deplacement de 
C   chaque borne.
C
      CST19=(AMPR*GAM*WL*PITCH)/(4*PI*DCOS(ALPHA))
C
C   Deplacement de la borne inferieur
C
      CA193=(DSIN(2*PI*X3*(1/PITCH-1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL-PITCH)
      CB193=(DSIN(2*PI*X3*(1/PITCH+1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL+PITCH)
      DX3=CST19*(CA193-CB193)
C
C   Deplacement de la borne superieur
C
      CA194=(DSIN(2*PI*X4*(1/PITCH-1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL-PITCH)
      CB194=(DSIN(2*PI*X4*(1/PITCH+1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL+PITCH)
      DX4=CST19*(CA194-CB194)
C
C   Maintenant que les deplacement sont connus, ont peut calculer
C   la constante avec l'equation 33.
C
      EOD=(DCOS(ALPHA)*(DX4-DX3))/(X4-X3)-(GAM*PI*(X4-X3))/PITCH
C
C   Avec cette constante on peut determiner la force dans le toron
C   selon l equation 35.
C
      EX=(Q*CFL*(X-X3))/(DCOS(ALPHA)*ET*AT)+EOD
C
      WRITE(*,333) X,I,X3,X4,DX3,DX4,EX
  333 FORMAT(1X,F9.5,2X,I3,2X,F9.7,2X,F9.7,2X,E9.3,2X,E9.3,2X,E9.3)
C   Finalement on va calculer le moment que le toron genere.
C   
      GOTO 310
C
C     A PARTIR D'ICI ON FAIT LE MEME CALCUL MAIS POUR UN
C     COEFFICIENT DE FRICTION PLUS PETIT QUE LA VALEUR NEGATIVE
C     DU COEFF. LIMITE.
C
  300 DX=PITCH/10000
      CFLN=0-CFL
      IF(CFX.GE.CFLN) THEN
        EX=AMPR*GAM*DSIN((2*PI*X)/PITCH+THETA(I))*DSIN((2*PI*X)/WL)
        WRITE(*,332) X,I,EX
        GOTO 310
      ENDIF
  332 FORMAT(1X,E11.5,2X,I3,2X,E9.3)  
      X2=X
  350 X2=X2+DX
      CA92=(WL/PITCH)*(DCOS((2*PI*X2)/PITCH+THETA(I)))*
     %(DSIN((2*PI*X2)/WL))
      CB92=(DSIN((2*PI*X2)/PITCH+THETA(I)))*(DCOS((2*PI*X2)/WL))
      CFX2=CST9*(CA92+CB92)
      IF(CFX2.LT.CFLN) GOTO 350
      X1=X
  360 X1=X1-DX
      CA91=(WL/PITCH)*(DCOS((2*PI*X1)/PITCH+THETA(I)))*
     %(DSIN((2*PI*X1)/WL))
      CB91=(DSIN((2*PI*X1)/PITCH+THETA(I)))*(DCOS((2*PI*X1)/WL))
      CFX1=CST9*(CA91+CB91)
      IF(CFX1.LT.CFLN) GOTO 360
C
C   Maintenant que les bornes de glissement X1 et X2 sont determine
C   on applique l'equation 23 pour determiner le deplacement de 
C   chaque borne.
C
      CST19=(AMPR*GAM*WL*PITCH)/(4*PI*DCOS(ALPHA))
C
C   Deplacement de la borne inferieur
C
      CA191=(DSIN(2*PI*X1*(1/PITCH-1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL-PITCH)
      CB191=(DSIN(2*PI*X1*(1/PITCH+1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL+PITCH)
      DX1=CST19*(CA191-CB191)
C
C   Deplacement de la borne superieur
C
      CA192=(DSIN(2*PI*X2*(1/PITCH-1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL-PITCH)
      CB192=(DSIN(2*PI*X2*(1/PITCH+1/WL)+THETA(I))-
     %DSIN(THETA(I)))/(WL+PITCH)
      DX2=CST19*(CA192-CB192)
C
C   Maintenant que les deplacement sont connus, ont peut calculer
C   la constante avec l'equation 32.
C
      EOG=(DCOS(ALPHA)*(DX2-DX1))/(X2-X1)+(GAM*PI*(X2-X1))/PITCH
C
C   Avec cette constante on peut determiner la force dans le toron.
C   selon l equation 34
C
      EX=(Q*CFLN*(X-X1))/(DCOS(ALPHA)*ET*AT)+EOG
C
      WRITE(*,334) X,I,X1,X2,DX1,DX2,EX
  334 FORMAT(1X,E11.5,2X,I3,2X,F9.7,2X,F9.7,2X,E9.3,2X,E9.3,2X,E9.3)
C   MAINTENANT QUE L'ON A ELONGATION DU TORON ON PEUT CALCULER
C   LES FORCES ET LES MOMENTS QU'IL CREE.
C   
C
C   LES FORCES SONT
C
  310 FYZ=EX*ET*AT*DSIN(ALPHA)
      FX(I)=EX*ET*AT*DCOS(ALPHA)
      FY(I)=FYZ*DCOS((2*PI*X)/PITCH+THETA(I))
      FZ(I)=FYZ*DSIN((2*PI*X)/PITCH+THETA(I))
C
C   LES MOMENTS SONT
C
      FMXZ(I)=FX(I)*RN*DSIN((2*PI*X)/PITCH+THETA(I))
      FMXY(I)=FX(I)*RN*DCOS((2*PI*X)/PITCH+THETA(I))
      TMX(I)=FYZ*RN
C      WRITE(4,5) X,I,EX,FMXY(I),TMX(I)
    5 FORMAT(3X,F9.3,5X,I5,5X,E14.8,3X,F9.5,3X,F9.5)
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
C  selon l equation 39
C  
      RIG=(FMXZT*(WL/(2*PI))**2)/(AMP*DSIN((2*PI*X)/WL))
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
      WRITE(2,40) AMP,RN,CPN
   40 FORMAT(2X,'AMPLITUDE=',E9.4,/,2X,'R. DU NOYEAU=',F5.3,/,2X,
     +'COEFFICIENT DE POISSON=',F5.3)
      WRITE(2,41) ALPHA,RT,ET
   41 FORMAT(2X,'ANGLE D ENROULEMENT=',F7.5,/,2X,'R. DU TORON=',E9.4,
     +/,2X,'MODULE DE YOUNG DU TORON=',E9.4)
      WRITE(2,42) Q,WL,CL
   42 FORMAT(2X,'PRESSION D APPUI=',E9.4e2,/,2X,'LONGUEUR D ONDE=',F5.2,
     +/,2X,'LONGUEUR DU CABLE=',F9.3)
      WRITE(2,43) AMPC,CFL,PITCH
   43 FORMAT(2X,'AMPL. CRITIQUE=',E9.4,/,2X,'COEFF. F=',F7.4,/,2X,
     +'PITCH=',F7.4)
      WRITE(2,44) AT,DXPAS,DX,CST9
   44 FORMAT(2X,'AIRE DU TORON=',E9.4,/,2X,'INCREMENT EN X=',F9.5,
     +/,2X,'INCREMENT EN XPAS=',F9.5,/,2X,'CONSTANTE EQ9=',E12.7)
      WRITE(2,45) NFIL,EN,F
   45 FORMAT(2X,'NOMBRE DE FIL:',I2,/,2X,'MOD. DE YOUG DU NOYEAU=',
     +E9.4,/,2X,'F SELON EQUATION 2b=',E9.4)
      WRITE(2,46) TI,AMPR,GAM
   46 FORMAT(2X,'TENSION DANS LE FIL=',E9.4,/,2X,'RAPPORT D AMP.=',
     +E9.4,/,2X,'GAMMA SELON EQUATION 17=',E9.4)
   20 FORMAT(3X,F9.3,6X,F12.4)
   21 FORMAT(1X,F8.4,1X,F10.4,2X,F6.4,1X,F6.4,1X,F8.3,2X,F6.4,1X,
     +F6.3,1X,F8.3)
C      CLOSE(4)
      CLOSE(3)
      CLOSE(2) 
      CLOSE(1)
      STOP
      END
