$DEBUG
$STORAGE:2
C======================================================================C
C Sousroutine qui demande à l'utilisateur d'initialiser la position    C
C des bornes lorsque l'approximation automatique ne fonctionne pas.    C
C======================================================================C
C
      SUBROUTINE PBCONV(XB1,XB2)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/CONV/ICONVERG
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      ICONVERG=0
C
      WRITE(*,'(3X,''XINF= '',F5.2,3X,''XSUP='',F5.2,/)') XINF,XSUP
C
   10 WRITE(*,'(/,3X,''Entrez l approx. de XB1:'',\)')
      READ (*,*,ERR=10) XB1
C
      XB2=XSUP-XB1
C
      RETURN
      END
