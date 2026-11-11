$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Utilise la méthode de la fausse position pour trouver les racines    C
C d'une fonction. Elle provient du livre "NUMERICAL RECIPES" de Press  C
C W. H. et Al. page 248.                                               C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION RTFLSP(FUNC,X1,X2,XACC)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (MAXIT=100)
C
      COMMON/CONV/ICONVERG
C
      FL=FUNC(X1)
      FH=FUNC(X2)
      IF(FL*FH.GT.0.) THEN
         PAUSE 'Problème d approximation de la borne (Pressez ENTER)!!!'
         ICONVERG=1
         RETURN
      END IF
      IF(FL.LT.0.)THEN
        XL=X1
        XH=X2
      ELSE
        XL=X2
        XH=X1
        SWAP=FL
        FL=FH
        FH=SWAP
      ENDIF
      DX=XH-XL
      DO 11 J=1,MAXIT
        RTFLSP=XL+DX*FL/(FL-FH)
        F=FUNC(RTFLSP)
        IF(F.LT.0.) THEN
          DEL=XL-RTFLSP
          XL=RTFLSP
          FL=F
        ELSE
          DEL=XH-RTFLSP
          XH=RTFLSP
          FH=F
        ENDIF
        DX=XH-XL
        IF(ABS(DEL).LT.XACC.OR.F.EQ.0.)RETURN
11    CONTINUE
      END
