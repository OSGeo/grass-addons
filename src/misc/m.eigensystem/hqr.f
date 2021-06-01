      SUBROUTINE HQR(NM,N,LOW,IGH,H,WR,WI,IERR)                         EIS4
C                                                                       EIS4
      INTEGER I,J,K,L,M,N,EN,LL,MM,NA,NM,IGH,ITN,ITS,LOW,MP2,ENM2,IERR  EIS4
      DOUBLE PRECISION H(NM,N),WR(N),WI(N)                              EIS4
      DOUBLE PRECISION P,Q,R,S,T,W,X,Y,ZZ,NORM,TST1,TST2                EIS4
      LOGICAL NOTLAS                                                    EIS4
C                                                                       EIS4
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE HQR,      EIS4
C     NUM. MATH. 14, 219-231(1970) BY MARTIN, PETERS, AND WILKINSON.    EIS4
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 359-371(1971).   EIS4
C                                                                       EIS4
C     THIS SUBROUTINE FINDS THE EIGENVALUES OF A REAL                   EIS4
C     UPPER HESSENBERG MATRIX BY THE QR METHOD.                         EIS4
C                                                                       EIS4
C     ON INPUT                                                          EIS4
C                                                                       EIS4
C        NM MUST BE SET TO THE ROW DIMENSION OF TWO-DIMENSIONAL         EIS4
C          ARRAY PARAMETERS AS DECLARED IN THE CALLING PROGRAM          EIS4
C          DIMENSION STATEMENT.                                         EIS4
C                                                                       EIS4
C        N IS THE ORDER OF THE MATRIX.                                  EIS4
C                                                                       EIS4
C        LOW AND IGH ARE INTEGERS DETERMINED BY THE BALANCING           EIS4
C          SUBROUTINE  BALANC.  IF  BALANC  HAS NOT BEEN USED,          EIS4
C          SET LOW=1, IGH=N.                                            EIS4
C                                                                       EIS4
C        H CONTAINS THE UPPER HESSENBERG MATRIX.  INFORMATION ABOUT     EIS4
C          THE TRANSFORMATIONS USED IN THE REDUCTION TO HESSENBERG      EIS4
C          FORM BY  ELMHES  OR  ORTHES, IF PERFORMED, IS STORED         EIS4
C          IN THE REMAINING TRIANGLE UNDER THE HESSENBERG MATRIX.       EIS4
C                                                                       EIS4
C     ON OUTPUT                                                         EIS4
C                                                                       EIS4
C        H HAS BEEN DESTROYED.  THEREFORE, IT MUST BE SAVED             EIS4
C          BEFORE CALLING  HQR  IF SUBSEQUENT CALCULATION AND           EIS4
C          BACK TRANSFORMATION OF EIGENVECTORS IS TO BE PERFORMED.      EIS4
C                                                                       EIS4
C        WR AND WI CONTAIN THE REAL AND IMAGINARY PARTS,                EIS4
C          RESPECTIVELY, OF THE EIGENVALUES.  THE EIGENVALUES           EIS4
C          ARE UNORDERED EXCEPT THAT COMPLEX CONJUGATE PAIRS            EIS4
C          OF VALUES APPEAR CONSECUTIVELY WITH THE EIGENVALUE           EIS4
C          HAVING THE POSITIVE IMAGINARY PART FIRST.  IF AN             EIS4
C          ERROR EXIT IS MADE, THE EIGENVALUES SHOULD BE CORRECT        EIS4
C          FOR INDICES IERR+1,...,N.                                    EIS4
C                                                                       EIS4
C        IERR IS SET TO                                                 EIS4
C          ZERO       FOR NORMAL RETURN,                                EIS4
C          J          IF THE LIMIT OF 30*N ITERATIONS IS EXHAUSTED      EIS4
C                     WHILE THE J-TH EIGENVALUE IS BEING SOUGHT.        EIS4
C                                                                       EIS4
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS4
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS4
C                                                                       EIS4
C     THIS VERSION DATED AUGUST 1983.                                   EIS4
C                                                                       EIS4
C     ------------------------------------------------------------------EIS4
C                                                                       EIS4
      IERR = 0                                                          EIS4
      NORM = 0.0D0                                                      EIS4
      K = 1                                                             EIS4
C     .......... STORE ROOTS ISOLATED BY BALANC                         EIS4
C                AND COMPUTE MATRIX NORM ..........                     EIS4
      DO 50 I = 1, N                                                    EIS4
C                                                                       EIS4
         DO 40 J = K, N                                                 EIS4
   40    NORM = NORM + DABS(H(I,J))                                     EIS4
C                                                                       EIS4
         K = I                                                          EIS4
         IF (I .GE. LOW .AND. I .LE. IGH) GO TO 50                      EIS4
         WR(I) = H(I,I)                                                 EIS4
         WI(I) = 0.0D0                                                  EIS4
   50 CONTINUE                                                          EIS4
C                                                                       EIS4
      EN = IGH                                                          EIS4
      T = 0.0D0                                                         EIS4
      ITN = 30*N                                                        EIS4
C     .......... SEARCH FOR NEXT EIGENVALUES ..........                 EIS4
   60 IF (EN .LT. LOW) GO TO 1001                                       EIS4
      ITS = 0                                                           EIS4
      NA = EN - 1                                                       EIS4
      ENM2 = NA - 1                                                     EIS4
C     .......... LOOK FOR SINGLE SMALL SUB-DIAGONAL ELEMENT             EIS4
C                FOR L=EN STEP -1 UNTIL LOW DO -- ..........            EIS4
   70 DO 80 LL = LOW, EN                                                EIS4
         L = EN + LOW - LL                                              EIS4
         IF (L .EQ. LOW) GO TO 100                                      EIS4
         S = DABS(H(L-1,L-1)) + DABS(H(L,L))                            EIS4
         IF (S .EQ. 0.0D0) S = NORM                                     EIS4
         TST1 = S                                                       EIS4
         TST2 = TST1 + DABS(H(L,L-1))                                   EIS4
         IF (TST2 .EQ. TST1) GO TO 100                                  EIS4
   80 CONTINUE                                                          EIS4
C     .......... FORM SHIFT ..........                                  EIS4
  100 X = H(EN,EN)                                                      EIS4
      IF (L .EQ. EN) GO TO 270                                          EIS4
      Y = H(NA,NA)                                                      EIS4
      W = H(EN,NA) * H(NA,EN)                                           EIS4
      IF (L .EQ. NA) GO TO 280                                          EIS4
      IF (ITN .EQ. 0) GO TO 1000                                        EIS4
      IF (ITS .NE. 10 .AND. ITS .NE. 20) GO TO 130                      EIS4
C     .......... FORM EXCEPTIONAL SHIFT ..........                      EIS4
      T = T + X                                                         EIS4
C                                                                       EIS4
      DO 120 I = LOW, EN                                                EIS4
  120 H(I,I) = H(I,I) - X                                               EIS4
C                                                                       EIS4
      S = DABS(H(EN,NA)) + DABS(H(NA,ENM2))                             EIS4
      X = 0.75D0 * S                                                    EIS4
      Y = X                                                             EIS4
      W = -0.4375D0 * S * S                                             EIS4
  130 ITS = ITS + 1                                                     EIS4
      ITN = ITN - 1                                                     EIS4
C     .......... LOOK FOR TWO CONSECUTIVE SMALL                         EIS4
C                SUB-DIAGONAL ELEMENTS.                                 EIS4
C                FOR M=EN-2 STEP -1 UNTIL L DO -- ..........            EIS4
      DO 140 MM = L, ENM2                                               EIS4
         M = ENM2 + L - MM                                              EIS4
         ZZ = H(M,M)                                                    EIS4
         R = X - ZZ                                                     EIS4
         S = Y - ZZ                                                     EIS4
         P = (R * S - W) / H(M+1,M) + H(M,M+1)                          EIS4
         Q = H(M+1,M+1) - ZZ - R - S                                    EIS4
         R = H(M+2,M+1)                                                 EIS4
         S = DABS(P) + DABS(Q) + DABS(R)                                EIS4
         P = P / S                                                      EIS4
         Q = Q / S                                                      EIS4
         R = R / S                                                      EIS4
         IF (M .EQ. L) GO TO 150                                        EIS4
         TST1 = DABS(P)*(DABS(H(M-1,M-1)) + DABS(ZZ) + DABS(H(M+1,M+1)))EIS4
         TST2 = TST1 + DABS(H(M,M-1))*(DABS(Q) + DABS(R))               EIS4
         IF (TST2 .EQ. TST1) GO TO 150                                  EIS4
  140 CONTINUE                                                          EIS4
C                                                                       EIS4
  150 MP2 = M + 2                                                       EIS4
C                                                                       EIS4
      DO 160 I = MP2, EN                                                EIS4
         H(I,I-2) = 0.0D0                                               EIS4
         IF (I .EQ. MP2) GO TO 160                                      EIS4
         H(I,I-3) = 0.0D0                                               EIS4
  160 CONTINUE                                                          EIS4
C     .......... DOUBLE QR STEP INVOLVING ROWS L TO EN AND              EIS4
C                COLUMNS M TO EN ..........                             EIS4
      DO 260 K = M, NA                                                  EIS4
         NOTLAS = K .NE. NA                                             EIS4
         IF (K .EQ. M) GO TO 170                                        EIS4
         P = H(K,K-1)                                                   EIS4
         Q = H(K+1,K-1)                                                 EIS4
         R = 0.0D0                                                      EIS4
         IF (NOTLAS) R = H(K+2,K-1)                                     EIS4
         X = DABS(P) + DABS(Q) + DABS(R)                                EIS4
         IF (X .EQ. 0.0D0) GO TO 260                                    EIS4
         P = P / X                                                      EIS4
         Q = Q / X                                                      EIS4
         R = R / X                                                      EIS4
  170    S = DSIGN(DSQRT(P*P+Q*Q+R*R),P)                                EIS4
         IF (K .EQ. M) GO TO 180                                        EIS4
         H(K,K-1) = -S * X                                              EIS4
         GO TO 190                                                      EIS4
  180    IF (L .NE. M) H(K,K-1) = -H(K,K-1)                             EIS4
  190    P = P + S                                                      EIS4
         X = P / S                                                      EIS4
         Y = Q / S                                                      EIS4
         ZZ = R / S                                                     EIS4
         Q = Q / P                                                      EIS4
         R = R / P                                                      EIS4
         IF (NOTLAS) GO TO 225                                          EIS4
C     .......... ROW MODIFICATION ..........                            EIS4
         DO 200 J = K, N                                                EIS4
            P = H(K,J) + Q * H(K+1,J)                                   EIS4
            H(K,J) = H(K,J) - P * X                                     EIS4
            H(K+1,J) = H(K+1,J) - P * Y                                 EIS4
  200    CONTINUE                                                       EIS4
C                                                                       EIS4
         J = MIN0(EN,K+3)                                               EIS4
C     .......... COLUMN MODIFICATION ..........                         EIS4
         DO 210 I = 1, J                                                EIS4
            P = X * H(I,K) + Y * H(I,K+1)                               EIS4
            H(I,K) = H(I,K) - P                                         EIS4
            H(I,K+1) = H(I,K+1) - P * Q                                 EIS4
  210    CONTINUE                                                       EIS4
         GO TO 255                                                      EIS4
  225    CONTINUE                                                       EIS4
C     .......... ROW MODIFICATION ..........                            EIS4
         DO 230 J = K, N                                                EIS4
            P = H(K,J) + Q * H(K+1,J) + R * H(K+2,J)                    EIS4
            H(K,J) = H(K,J) - P * X                                     EIS4
            H(K+1,J) = H(K+1,J) - P * Y                                 EIS4
            H(K+2,J) = H(K+2,J) - P * ZZ                                EIS4
  230    CONTINUE                                                       EIS4
C                                                                       EIS4
         J = MIN0(EN,K+3)                                               EIS4
C     .......... COLUMN MODIFICATION ..........                         EIS4
         DO 240 I = 1, J                                                EIS4
            P = X * H(I,K) + Y * H(I,K+1) + ZZ * H(I,K+2)               EIS4
            H(I,K) = H(I,K) - P                                         EIS4
            H(I,K+1) = H(I,K+1) - P * Q                                 EIS4
            H(I,K+2) = H(I,K+2) - P * R                                 EIS4
  240    CONTINUE                                                       EIS4
  255    CONTINUE                                                       EIS4
C                                                                       EIS4
  260 CONTINUE                                                          EIS4
C                                                                       EIS4
      GO TO 70                                                          EIS4
C     .......... ONE ROOT FOUND ..........                              EIS4
  270 WR(EN) = X + T                                                    EIS4
      WI(EN) = 0.0D0                                                    EIS4
      EN = NA                                                           EIS4
      GO TO 60                                                          EIS4
C     .......... TWO ROOTS FOUND ..........                             EIS4
  280 P = (Y - X) / 2.0D0                                               EIS4
      Q = P * P + W                                                     EIS4
      ZZ = DSQRT(DABS(Q))                                               EIS4
      X = X + T                                                         EIS4
      IF (Q .LT. 0.0D0) GO TO 320                                       EIS4
C     .......... REAL PAIR ..........                                   EIS4
      ZZ = P + DSIGN(ZZ,P)                                              EIS4
      WR(NA) = X + ZZ                                                   EIS4
      WR(EN) = WR(NA)                                                   EIS4
      IF (ZZ .NE. 0.0D0) WR(EN) = X - W / ZZ                            EIS4
      WI(NA) = 0.0D0                                                    EIS4
      WI(EN) = 0.0D0                                                    EIS4
      GO TO 330                                                         EIS4
C     .......... COMPLEX PAIR ..........                                EIS4
  320 WR(NA) = X + P                                                    EIS4
      WR(EN) = X + P                                                    EIS4
      WI(NA) = ZZ                                                       EIS4
      WI(EN) = -ZZ                                                      EIS4
  330 EN = ENM2                                                         EIS4
      GO TO 60                                                          EIS4
C     .......... SET ERROR -- ALL EIGENVALUES HAVE NOT                  EIS4
C                CONVERGED AFTER 30*N ITERATIONS ..........             EIS4
 1000 IERR = EN                                                         EIS4
 1001 RETURN                                                            EIS4
      END                                                               EIS4
