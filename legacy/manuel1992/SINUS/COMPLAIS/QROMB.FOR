$DEBUG
$STORAGE:2
C===================================================================C
C Sousroutine qui utilise l'algorithme de Romberg pour faire        C
C l'integration numérique. Elle provient du livre "NUMERICAL        C
C RECIPES" de Press W.H. et Al. page 114.                           C
C===================================================================C
C
       SUBROUTINE QROMB(XCP,YCP,ZT,BT,ET,FUNC,A,B,SS)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER(EPS=1.E-6,JJMAX=20,JJMAXP=JJMAX+1,KK=5,KKM=4)
C
      DIMENSION S(JJMAXP),H(JJMAXP)
C
      H(1)=1.
      DO 11 J=1,JJMAX
        CALL TRAPZD(XCP,YCP,ZT,BT,ET,FUNC,A,B,S(J),J)
        IF (J.GE.KK) THEN
          L=J-KKM
          CALL POLINT(H(L),S(L),KK,0.,SS,DSS)
          IF (ABS(DSS).LT.EPS*ABS(SS)) RETURN
        ENDIF
        S(J+1)=S(J)
        H(J+1)=0.25*H(J)
11    CONTINUE
      PAUSE 'Too many steps.'
      END
