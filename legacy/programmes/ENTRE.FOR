$DEBUG
C
C  CE PROGRAMME PREPARE LE FICHIER D'ENTRE POUR SINUS.FOR
C 
      PROGRAM ENTRE
      IMPLICIT DOUBLE PRECISION (A-F)
      IMPLICIT DOUBLE PRECISION (P-X)
C
      OPEN(1,FILE='ENTRE.DAT',ACCESS='SEQUENTIAL',STATUS='NEW')
C
      WRITE(*,1)
    1 FORMAT(////,3X,'Ce programme prepare le fichier d entre pour',
     +/,3X,'SINUS.FOR. ou RAYON.FOR. Mettre 0 lorsque',
     +/,3X,'la question ne s applique pas.'//)
C
      WRITE(*,2) 
    2 FORMAT(3X,'Quelle est la longueur du toron (en metre):',1X,\)
      READ(*,*) CL
      WRITE(1,100) CL
  100 FORMAT(1X,D14.8,10X,'Longueur du toron')
C
      WRITE(*,3)
    3 FORMAT(3X,'Combien de fil sont entoure autour de l ame:',1X,\)
      READ(*,*) NFIL
      WRITE(1,101) NFIL
  101 FORMAT(1X,I6,18X,'Nombre de fil')
C 
      WRITE(*,5)
    5 FORMAT(3X,'Quel est l angle d helice des fils (en radians):',
     +1X,\)
      READ(*,*) ALPHA
      WRITE(1,102) ALPHA
  102 FORMAT(1X,D14.8,10X,'Angle d helice')
C
      WRITE(*,6)
    6 FORMAT(3X,'Quel est le rayon d un des fils (en metre):',1X,\)
      READ(*,*) RF
      WRITE(1,103) RF
  103 FORMAT(1X,D14.8,10X,'Rayon d un fil')
C
      WRITE(*,7)
    7 FORMAT(3X,'Quel est le module de Young des fils (en Pascal):',
     +1X,\)
      READ(*,*) EF
      WRITE(1,104) EF
  104 FORMAT(1X,D14.8,10X,'E des fils')
C
      WRITE(*,8)
    8 FORMAT(3X,'Quelle est la tension dans un fil (en Newton):',
     +1X,\)
      READ(*,*) TI
      WRITE(1,105) TI
  105 FORMAT(1X,D14.8,10X,'Tension dans un fil')
C
      WRITE(*,9) 
    9 FORMAT(3X,'Quel est le rayon de l ame (en metre):',1X,\)
      READ(*,*) RA
      WRITE(1,106) RA
  106 FORMAT(1X,D14.8,10X,'Rayon de l ame')
C
      WRITE(*,11)
   11 FORMAT(3X,'Quel est le module de Young de l ame (en Pascal):',
     +1X,\)
      READ(*,*) EA
      WRITE(1,107) EA
  107 FORMAT(1X,D14.8,10X,'E de l ame')
C
      WRITE(*,12)
   12 FORMAT(3X,'Quel est le coefficient de Poisson de l ame:',1X,\)
      READ(*,*) CPN
      WRITE(1,108) CPN
  108 FORMAT(1X,D14.8,10X,'Coefficient de Poisson')
C
      WRITE(*,13)
   13 FORMAT(3X,'Quel est le coefficient de friction entre l ame',/,
     +3X,'et les fils:',1X,\)
      READ(*,*) CFL
      WRITE(1,109) CFL
  109 FORMAT(1X,D14.8,10X,'Coefficient de friction')
C
      WRITE(*,14)
   14 FORMAT(3X,'Quelle est la longueur d onde de la sinusoide', 
     +' (en metre):',1X,\)
      READ(*,*) WL
      WRITE(1,110) WL
  110 FORMAT(1X,D14.8,10X,'Longueur d onde')
C 
      WRITE(*,15)
   15 FORMAT(3X,'Quelle est l amplitude de la sinusoide ou le',/,
     +3X,'rayon de courbure (en metre):',1X,\)
      READ(*,*) AMP
      WRITE(1,111) AMP
  111 FORMAT(1X,D14.8,10X,'Amplitude ou rayon de courbure')
C
      WRITE(*,16)
   16 FORMAT(3X,'Combien de position desirez-vous:',1X,\)
      READ(*,*) NPAS
      WRITE(1,112) NPAS
  112 FORMAT(1X,I6,18X,'Nombre de position')
C
      WRITE(*,17)
   17 FORMAT(3X,'Point de depart des iterations le long de X ',
     +'(en metre):',1X,\)
      READ(*,*) XDEPART
      WRITE(1,113) XDEPART
  113 FORMAT(1X,D14.8,10X,'Point de depart')
C
      WRITE(*,18)
   18 FORMAT(3X,'Point d arret des iterations le long de X ',
     +'(en metre):',1X,\) 
      READ(*,*) XFINAL
      WRITE(1,114) XFINAL
  114 FORMAT(1X,D14.8,10X,'Point d arret')
C
C    FIN D ENTRE DES DONNEES
C
      CLOSE(1)
      STOP
      END
