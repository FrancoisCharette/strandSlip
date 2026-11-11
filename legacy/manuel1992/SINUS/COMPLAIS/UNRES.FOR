$DEBUG
$STORAGE:2
C======================================================================C
C Cette sousroutine détermine les constantes BTM et ETM lorsqu'il y a  C
C une seule région de micro-glissement dans tout le demi-pas considéré.C
C======================================================================C
C
      SUBROUTINE UNRES(A,B,BTM,ETM)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      PARAMETER (NMAX=10,JMAX=62)
C
      DIMENSION B(JMAX),A(JMAX,JMAX),INDX(JMAX)
C
      COMMON/MAT1/ZETA(NMAX),XCOMP(NMAX+1),YCOMP(NMAX+1)
      COMMON/XCST/XINF,XSUP,XM,ICOTE
C
      JDIM=2
C
      A(1,1)=F1D(XINF,ZETA(1))
      A(1,2)=F2D(XINF,ZETA(1))
      A(2,1)=F1D(XSUP,ZETA(1))
      A(2,2)=F2D(XSUP,ZETA(1))
C
      B(1)=DEPAME(XINF)-DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),XCOMP(1),
     &YCOMP(1),XINF)
      B(2)=DEPAME(XSUP)-DEPFIL(XCOMP(1),YCOMP(1),ZETA(1),XCOMP(1),
     &YCOMP(1),XSUP)
C
      CALL DLUDCMP(A,JDIM,JMAX,INDX,D)
      CALL DLUBKSB(A,JDIM,JMAX,INDX,B)
C
      BTM=B(1)
      ETM=B(2)
C
      RETURN
      END
