$DEBUG
$STORAGE:2
C===================================================================C
C Sousroutine qui est utilisé par l'algorithme de Romberg pour      C
C faire l'integration numérique. Elle provient du livre "NUMERICAL  C
C RECIPES" de Press W.H. et Al. page 111.                           C
C===================================================================C
C
      SUBROUTINE TRAPZD(XCP,YCP,ZT,BT,ET,FUNC,A,B,S,N)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      IF (N.EQ.1) THEN
        S=0.5*(B-A)*(FUNC(XCP,YCP,ZT,BT,ET,A)+FUNC(XCP,YCP,ZT,BT,ET,B))
        IT=1
      ELSE
        TNM=IT
        DEL=(B-A)/TNM
        X=A+0.5*DEL
        SUM=0.
        DO 11 J=1,IT
          SUM=SUM+FUNC(XCP,YCP,ZT,BT,ET,X)
          X=X+DEL
11      CONTINUE
        S=0.5*(S+(B-A)*SUM/TNM)
        IT=2*IT
      ENDIF
      RETURN
      END
