$DEBUG
$STORAGE:2
C======================================================================C
C  Sousroutine qui effectue la décomposition LU de la matrice A.       C
C  Elle provient du livre "NUMERICAL RECIPES" de Press W. H. et al.    C
C  page 35.                                                            C
C======================================================================C
C
      SUBROUTINE DLUDCMP(A,N,NP,INDX,D)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMMAX=100, TINY=1.0E-20)
      DIMENSION A(NP,NP),INDX(N),VV(NMMAX)
C
      D=1.0D0
      DO I=1,N
         AAMAX=0.0D0
          DO J=1,N
            IF (DABS(A(I,J)).GT.AAMAX) AAMAX=DABS(A(I,J))
          END DO
         IF(AAMAX.EQ.0.0D0) PAUSE 'Singular matrix'
         VV(I)=1.0D0/AAMAX
      END DO
C
      DO J=1,N
         DO I=1,J-1
           SUM=A(I,J)
             DO K=1,I-1
               SUM=SUM-A(I,K)*A(K,J)
             END DO
           A(I,J)=SUM
         END DO
C
      AAMAX=0.0D0
      DO I=J,N
         SUM=A(I,J)
           DO  K=1,J-1
            SUM=SUM-A(I,K)*A(K,J)
           END DO
         A(I,J)=SUM
         DUM=VV(I)*DABS(SUM)
         IF(DUM.GE.AAMAX) THEN
            IMAX=I
            AAMAX=DUM
         ENDIF
      END DO
C
      IF(J.NE.IMAX) THEN
         DO K=1,N
            DUM=A(IMAX,K)
            A(IMAX,K)=A(J,K)
            A(J,K)=DUM
         END DO
        D=-D
        VV(IMAX)=VV(J)
      ENDIF
C
      INDX(J)=IMAX
      IF(A(J,J).EQ.0.0D0) A(J,J)=TINY
      IF(J.NE.N) THEN
         DUM=1.0D0/A(J,J)
         DO I=J+1,N
           A(I,J)=A(I,J)*DUM
         END DO
      ENDIF
C
      END DO
C
      RETURN
      END
