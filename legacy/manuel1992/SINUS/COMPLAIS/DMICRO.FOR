$DEBUG
$STORAGE:2
C----------------------------------------------------------------------C
C Cette fonction calcul la valeur de l'intégrand pour la dissipation   C
C d'énergie du au micro-glissement. Equation A.51                      C
C Modèle AVEC complaisance.                                            C
C----------------------------------------------------------------------C
C
      DOUBLE PRECISION FUNCTION DMICRO(BXORG,BYORG,ZTA,BTA,TA,XF)
C
      IMPLICIT DOUBLE PRECISION (A-H)
      IMPLICIT DOUBLE PRECISION (O-Z)
C
      COMMON/COMPLAIS/EN
      COMMON/CSTF/PI,THETA,PP,PPA,PP1,PN,PPB,PN1,WLBAR,ABAR ! Flèche
C                                                        sinusoidale
C     COMMON/CSTF/PI,THETA,RHOB ! Flèche rayon de courbure constant
      COMMON/CSTF1/GAMEXP,GAM1,GAMD1,GAME1,GAMF1
C
      DIFDEP=DABS(DEPAME(XF)-DEPFIL(BXORG,BYORG,ZTA,BTA,TA,XF))
C
      CSTMP1=(4.0D0*PI*DIFDEP)/(3.0D0*GAM1)
      CSTMP2=(6.0D0*GAM1)/((EN+1.0D0)*PI)
C
      IF(CSTMP1.GT.1.0D0) CSTMP1=DNINT(CSTMP1)
      IF(CSTMP1.GT.1.0D0) THEN
         WRITE(*,'(///,1X,''ATTENTION! FUNCTION DMICRO:'',2X,
     &   ''la valeur =>'',5X,F20.18,/,24X,''est change pour =>'',
     &   5X,F20.18)') CSTMP1,1.0D0
         PAUSE 'Pressez ENTER pour continuer'
         CSTMP1=1.0D0
      END IF
C
      TMP1=1.0D0-(1.0D0-CSTMP1)**((EN+1.0D0)/EN)
C
      TMP2A=(EN+1.0D0)-(((EN+1.0D0)/2.0D0)*CSTMP1)
      TMP2B=1.0D0-(1.0D0-CSTMP1)**(1.0D0/EN)
      TMP2=TMP2A*TMP2B
C
      DMICRO=CSTMP2*(TMP1-TMP2)
C
      END
