$DEBUG
$STORAGE:2
C======================================================================C
C  Sousroutine qui effectue la substitution inverse lorsque la         C
C  décomposition LU a été effectué. Elle provient du livre "NUMERICAL  C
C  RECIPES" de Press W. H. et al. page 37.                             C
C======================================================================C
C
      SUBROUTINE DLUBKSB(A,N,NP,INDX,B)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      DIMENSION A(NP,NP), INDX(N), B(N)
C
      II=0
      DO I=1,N
         LL=INDX(I)
         SUM=B(LL)
         B(LL)=B(I)
         IF (II.NE.0) THEN
            DO J=II,I-1
               SUM=SUM-A(I,J)*B(J)
            END DO
         ELSE IF (SUM.NE.0.0D0) THEN
             II=1
         END IF
         B(I)=SUM
      END DO
C
      DO I=N,1,-1
         SUM=B(I)
         IF(I.LT.N) THEN
            DO J=I+1,N
               SUM=SUM-A(I,J)*B(J)
            END DO
         ENDIF
         B(I)=SUM/A(I,I)
      END DO
C
      RETURN
      END
