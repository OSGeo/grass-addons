      SUBROUTINE HQR2(NM,N,LOW,IGH,H,WR,WI,Z,IERR)                      EIS4
C                                                                       EIS4
      INTEGER I,J,K,L,M,N,EN,II,JJ,LL,MM,NA,NM,NN,                      EIS4
     X        IGH,ITN,ITS,LOW,MP2,ENM2,IERR                             EIS4
      DOUBLE PRECISION H(NM,N),WR(N),WI(N),Z(NM,N)                      EIS4
      DOUBLE PRECISION P,Q,R,S,T,W,X,Y,RA,SA,VI,VR,ZZ,NORM,TST1,TST2    EIS4
      LOGICAL NOTLAS                                                    EIS4
C                                                                       EIS4
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE HQR2,     EIS4
C     NUM. MATH. 16, 181-204(1970) BY PETERS AND WILKINSON.             EIS4
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 372-395(1971).   EIS4
C                                                                       EIS4
C     THIS SUBROUTINE FINDS THE EIGENVALUES AND EIGENVECTORS            EIS4
C     OF A REAL UPPER HESSENBERG MATRIX BY THE QR METHOD.  THE          EIS4
C     EIGENVECTORS OF A REAL GENERAL MATRIX CAN ALSO BE FOUND           EIS4
C     IF  ELMHES  AND  ELTRAN  OR  ORTHES  AND  ORTRAN  HAVE            EIS4
C     BEEN USED TO REDUCE THIS GENERAL MATRIX TO HESSENBERG FORM        EIS4
C     AND TO ACCUMULATE THE SIMILARITY TRANSFORMATIONS.                 EIS4
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
C        H CONTAINS THE UPPER HESSENBERG MATRIX.                        EIS4
C                                                                       EIS4
C        Z CONTAINS THE TRANSFORMATION MATRIX PRODUCED BY  ELTRAN       EIS4
C          AFTER THE REDUCTION BY  ELMHES, OR BY  ORTRAN  AFTER THE     EIS4
C          REDUCTION BY  ORTHES, IF PERFORMED.  IF THE EIGENVECTORS     EIS4
C          OF THE HESSENBERG MATRIX ARE DESIRED, Z MUST CONTAIN THE     EIS4
C          IDENTITY MATRIX.                                             EIS4
C                                                                       EIS4
C     ON OUTPUT                                                         EIS4
C                                                                       EIS4
C        H HAS BEEN DESTROYED.                                          EIS4
C                                                                       EIS4
C        WR AND WI CONTAIN THE REAL AND IMAGINARY PARTS,                EIS4
C          RESPECTIVELY, OF THE EIGENVALUES.  THE EIGENVALUES           EIS4
C          ARE UNORDERED EXCEPT THAT COMPLEX CONJUGATE PAIRS            EIS4
C          OF VALUES APPEAR CONSECUTIVELY WITH THE EIGENVALUE           EIS4
C          HAVING THE POSITIVE IMAGINARY PART FIRST.  IF AN             EIS4
C          ERROR EXIT IS MADE, THE EIGENVALUES SHOULD BE CORRECT        EIS4
C          FOR INDICES IERR+1,...,N.                                    EIS4
C                                                                       EIS4
C        Z CONTAINS THE REAL AND IMAGINARY PARTS OF THE EIGENVECTORS.   EIS4
C          IF THE I-TH EIGENVALUE IS REAL, THE I-TH COLUMN OF Z         EIS4
C          CONTAINS ITS EIGENVECTOR.  IF THE I-TH EIGENVALUE IS COMPLEX EIS4
C          WITH POSITIVE IMAGINARY PART, THE I-TH AND (I+1)-TH          EIS4
C          COLUMNS OF Z CONTAIN THE REAL AND IMAGINARY PARTS OF ITS     EIS4
C          EIGENVECTOR.  THE EIGENVECTORS ARE UNNORMALIZED.  IF AN      EIS4
C          ERROR EXIT IS MADE, NONE OF THE EIGENVECTORS HAS BEEN FOUND. EIS4
C                                                                       EIS4
C        IERR IS SET TO                                                 EIS4
C          ZERO       FOR NORMAL RETURN,                                EIS4
C          J          IF THE LIMIT OF 30*N ITERATIONS IS EXHAUSTED      EIS4
C                     WHILE THE J-TH EIGENVALUE IS BEING SOUGHT.        EIS4
C                                                                       EIS4
C     CALLS CDIV FOR COMPLEX DIVISION.                                  EIS4
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
   60 IF (EN .LT. LOW) GO TO 340                                        EIS4
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
C     .......... ACCUMULATE TRANSFORMATIONS ..........                  EIS4
         DO 220 I = LOW, IGH                                            EIS4
            P = X * Z(I,K) + Y * Z(I,K+1)                               EIS4
            Z(I,K) = Z(I,K) - P                                         EIS4
            Z(I,K+1) = Z(I,K+1) - P * Q                                 EIS4
  220    CONTINUE                                                       EIS4
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
C     .......... ACCUMULATE TRANSFORMATIONS ..........                  EIS4
         DO 250 I = LOW, IGH                                            EIS4
            P = X * Z(I,K) + Y * Z(I,K+1) + ZZ * Z(I,K+2)               EIS4
            Z(I,K) = Z(I,K) - P                                         EIS4
            Z(I,K+1) = Z(I,K+1) - P * Q                                 EIS4
            Z(I,K+2) = Z(I,K+2) - P * R                                 EIS4
  250    CONTINUE                                                       EIS4
  255    CONTINUE                                                       EIS4
C                                                                       EIS4
  260 CONTINUE                                                          EIS4
C                                                                       EIS4
      GO TO 70                                                          EIS4
C     .......... ONE ROOT FOUND ..........                              EIS4
  270 H(EN,EN) = X + T                                                  EIS4
      WR(EN) = H(EN,EN)                                                 EIS4
      WI(EN) = 0.0D0                                                    EIS4
      EN = NA                                                           EIS4
      GO TO 60                                                          EIS4
C     .......... TWO ROOTS FOUND ..........                             EIS4
  280 P = (Y - X) / 2.0D0                                               EIS4
      Q = P * P + W                                                     EIS4
      ZZ = DSQRT(DABS(Q))                                               EIS4
      H(EN,EN) = X + T                                                  EIS4
      X = H(EN,EN)                                                      EIS4
      H(NA,NA) = Y + T                                                  EIS4
      IF (Q .LT. 0.0D0) GO TO 320                                       EIS4
C     .......... REAL PAIR ..........                                   EIS4
      ZZ = P + DSIGN(ZZ,P)                                              EIS4
      WR(NA) = X + ZZ                                                   EIS4
      WR(EN) = WR(NA)                                                   EIS4
      IF (ZZ .NE. 0.0D0) WR(EN) = X - W / ZZ                            EIS4
      WI(NA) = 0.0D0                                                    EIS4
      WI(EN) = 0.0D0                                                    EIS4
      X = H(EN,NA)                                                      EIS4
      S = DABS(X) + DABS(ZZ)                                            EIS4
      P = X / S                                                         EIS4
      Q = ZZ / S                                                        EIS4
      R = DSQRT(P*P+Q*Q)                                                EIS4
      P = P / R                                                         EIS4
      Q = Q / R                                                         EIS4
C     .......... ROW MODIFICATION ..........                            EIS4
      DO 290 J = NA, N                                                  EIS4
         ZZ = H(NA,J)                                                   EIS4
         H(NA,J) = Q * ZZ + P * H(EN,J)                                 EIS4
         H(EN,J) = Q * H(EN,J) - P * ZZ                                 EIS4
  290 CONTINUE                                                          EIS4
C     .......... COLUMN MODIFICATION ..........                         EIS4
      DO 300 I = 1, EN                                                  EIS4
         ZZ = H(I,NA)                                                   EIS4
         H(I,NA) = Q * ZZ + P * H(I,EN)                                 EIS4
         H(I,EN) = Q * H(I,EN) - P * ZZ                                 EIS4
  300 CONTINUE                                                          EIS4
C     .......... ACCUMULATE TRANSFORMATIONS ..........                  EIS4
      DO 310 I = LOW, IGH                                               EIS4
         ZZ = Z(I,NA)                                                   EIS4
         Z(I,NA) = Q * ZZ + P * Z(I,EN)                                 EIS4
         Z(I,EN) = Q * Z(I,EN) - P * ZZ                                 EIS4
  310 CONTINUE                                                          EIS4
C                                                                       EIS4
      GO TO 330                                                         EIS4
C     .......... COMPLEX PAIR ..........                                EIS4
  320 WR(NA) = X + P                                                    EIS4
      WR(EN) = X + P                                                    EIS4
      WI(NA) = ZZ                                                       EIS4
      WI(EN) = -ZZ                                                      EIS4
  330 EN = ENM2                                                         EIS4
      GO TO 60                                                          EIS4
C     .......... ALL ROOTS FOUND.  BACKSUBSTITUTE TO FIND               EIS4
C                VECTORS OF UPPER TRIANGULAR FORM ..........            EIS4
  340 IF (NORM .EQ. 0.0D0) GO TO 1001                                   EIS4
C     .......... FOR EN=N STEP -1 UNTIL 1 DO -- ..........              EIS4
      DO 800 NN = 1, N                                                  EIS4
         EN = N + 1 - NN                                                EIS4
         P = WR(EN)                                                     EIS4
         Q = WI(EN)                                                     EIS4
         NA = EN - 1                                                    EIS4
         IF (Q) 710, 600, 800                                           EIS4
C     .......... REAL VECTOR ..........                                 EIS4
  600    M = EN                                                         EIS4
         H(EN,EN) = 1.0D0                                               EIS4
         IF (NA .EQ. 0) GO TO 800                                       EIS4
C     .......... FOR I=EN-1 STEP -1 UNTIL 1 DO -- ..........            EIS4
         DO 700 II = 1, NA                                              EIS4
            I = EN - II                                                 EIS4
            W = H(I,I) - P                                              EIS4
            R = 0.0D0                                                   EIS4
C                                                                       EIS4
            DO 610 J = M, EN                                            EIS4
  610       R = R + H(I,J) * H(J,EN)                                    EIS4
C                                                                       EIS4
            IF (WI(I) .GE. 0.0D0) GO TO 630                             EIS4
            ZZ = W                                                      EIS4
            S = R                                                       EIS4
            GO TO 700                                                   EIS4
  630       M = I                                                       EIS4
            IF (WI(I) .NE. 0.0D0) GO TO 640                             EIS4
            T = W                                                       EIS4
            IF (T .NE. 0.0D0) GO TO 635                                 EIS4
               TST1 = NORM                                              EIS4
               T = TST1                                                 EIS4
  632          T = 0.01D0 * T                                           EIS4
               TST2 = NORM + T                                          EIS4
               IF (TST2 .GT. TST1) GO TO 632                            EIS4
  635       H(I,EN) = -R / T                                            EIS4
            GO TO 680                                                   EIS4
C     .......... SOLVE REAL EQUATIONS ..........                        EIS4
  640       X = H(I,I+1)                                                EIS4
            Y = H(I+1,I)                                                EIS4
            Q = (WR(I) - P) * (WR(I) - P) + WI(I) * WI(I)               EIS4
            T = (X * S - ZZ * R) / Q                                    EIS4
            H(I,EN) = T                                                 EIS4
            IF (DABS(X) .LE. DABS(ZZ)) GO TO 650                        EIS4
            H(I+1,EN) = (-R - W * T) / X                                EIS4
            GO TO 680                                                   EIS4
  650       H(I+1,EN) = (-S - Y * T) / ZZ                               EIS4
C                                                                       EIS4
C     .......... OVERFLOW CONTROL ..........                            EIS4
  680       T = DABS(H(I,EN))                                           EIS4
            IF (T .EQ. 0.0D0) GO TO 700                                 EIS4
            TST1 = T                                                    EIS4
            TST2 = TST1 + 1.0D0/TST1                                    EIS4
            IF (TST2 .GT. TST1) GO TO 700                               EIS4
            DO 690 J = I, EN                                            EIS4
               H(J,EN) = H(J,EN)/T                                      EIS4
  690       CONTINUE                                                    EIS4
C                                                                       EIS4
  700    CONTINUE                                                       EIS4
C     .......... END REAL VECTOR ..........                             EIS4
         GO TO 800                                                      EIS4
C     .......... COMPLEX VECTOR ..........                              EIS4
  710    M = NA                                                         EIS4
C     .......... LAST VECTOR COMPONENT CHOSEN IMAGINARY SO THAT         EIS4
C                EIGENVECTOR MATRIX IS TRIANGULAR ..........            EIS4
         IF (DABS(H(EN,NA)) .LE. DABS(H(NA,EN))) GO TO 720              EIS4
         H(NA,NA) = Q / H(EN,NA)                                        EIS4
         H(NA,EN) = -(H(EN,EN) - P) / H(EN,NA)                          EIS4
         GO TO 730                                                      EIS4
  720    CALL CDIV(0.0D0,-H(NA,EN),H(NA,NA)-P,Q,H(NA,NA),H(NA,EN))      EIS4
  730    H(EN,NA) = 0.0D0                                               EIS4
         H(EN,EN) = 1.0D0                                               EIS4
         ENM2 = NA - 1                                                  EIS4
         IF (ENM2 .EQ. 0) GO TO 800                                     EIS4
C     .......... FOR I=EN-2 STEP -1 UNTIL 1 DO -- ..........            EIS4
         DO 795 II = 1, ENM2                                            EIS4
            I = NA - II                                                 EIS4
            W = H(I,I) - P                                              EIS4
            RA = 0.0D0                                                  EIS4
            SA = 0.0D0                                                  EIS4
C                                                                       EIS4
            DO 760 J = M, EN                                            EIS4
               RA = RA + H(I,J) * H(J,NA)                               EIS4
               SA = SA + H(I,J) * H(J,EN)                               EIS4
  760       CONTINUE                                                    EIS4
C                                                                       EIS4
            IF (WI(I) .GE. 0.0D0) GO TO 770                             EIS4
            ZZ = W                                                      EIS4
            R = RA                                                      EIS4
            S = SA                                                      EIS4
            GO TO 795                                                   EIS4
  770       M = I                                                       EIS4
            IF (WI(I) .NE. 0.0D0) GO TO 780                             EIS4
            CALL CDIV(-RA,-SA,W,Q,H(I,NA),H(I,EN))                      EIS4
            GO TO 790                                                   EIS4
C     .......... SOLVE COMPLEX EQUATIONS ..........                     EIS4
  780       X = H(I,I+1)                                                EIS4
            Y = H(I+1,I)                                                EIS4
            VR = (WR(I) - P) * (WR(I) - P) + WI(I) * WI(I) - Q * Q      EIS4
            VI = (WR(I) - P) * 2.0D0 * Q                                EIS4
            IF (VR .NE. 0.0D0 .OR. VI .NE. 0.0D0) GO TO 784             EIS4
               TST1 = NORM * (DABS(W) + DABS(Q) + DABS(X)               EIS4
     X                      + DABS(Y) + DABS(ZZ))                       EIS4
               VR = TST1                                                EIS4
  783          VR = 0.01D0 * VR                                         EIS4
               TST2 = TST1 + VR                                         EIS4
               IF (TST2 .GT. TST1) GO TO 783                            EIS4
  784       CALL CDIV(X*R-ZZ*RA+Q*SA,X*S-ZZ*SA-Q*RA,VR,VI,              EIS4
     X                H(I,NA),H(I,EN))                                  EIS4
            IF (DABS(X) .LE. DABS(ZZ) + DABS(Q)) GO TO 785              EIS4
            H(I+1,NA) = (-RA - W * H(I,NA) + Q * H(I,EN)) / X           EIS4
            H(I+1,EN) = (-SA - W * H(I,EN) - Q * H(I,NA)) / X           EIS4
            GO TO 790                                                   EIS4
  785       CALL CDIV(-R-Y*H(I,NA),-S-Y*H(I,EN),ZZ,Q,                   EIS4
     X                H(I+1,NA),H(I+1,EN))                              EIS4
C                                                                       EIS4
C     .......... OVERFLOW CONTROL ..........                            EIS4
  790       T = DMAX1(DABS(H(I,NA)), DABS(H(I,EN)))                     EIS4
            IF (T .EQ. 0.0D0) GO TO 795                                 EIS4
            TST1 = T                                                    EIS4
            TST2 = TST1 + 1.0D0/TST1                                    EIS4
            IF (TST2 .GT. TST1) GO TO 795                               EIS4
            DO 792 J = I, EN                                            EIS4
               H(J,NA) = H(J,NA)/T                                      EIS4
               H(J,EN) = H(J,EN)/T                                      EIS4
  792       CONTINUE                                                    EIS4
C                                                                       EIS4
  795    CONTINUE                                                       EIS4
C     .......... END COMPLEX VECTOR ..........                          EIS4
  800 CONTINUE                                                          EIS4
C     .......... END BACK SUBSTITUTION.                                 EIS4
C                VECTORS OF ISOLATED ROOTS ..........                   EIS4
      DO 840 I = 1, N                                                   EIS4
         IF (I .GE. LOW .AND. I .LE. IGH) GO TO 840                     EIS4
C                                                                       EIS4
         DO 820 J = I, N                                                EIS4
  820    Z(I,J) = H(I,J)                                                EIS4
C                                                                       EIS4
  840 CONTINUE                                                          EIS4
C     .......... MULTIPLY BY TRANSFORMATION MATRIX TO GIVE              EIS4
C                VECTORS OF ORIGINAL FULL MATRIX.                       EIS4
C                FOR J=N STEP -1 UNTIL LOW DO -- ..........             EIS4
      DO 880 JJ = LOW, N                                                EIS4
         J = N + LOW - JJ                                               EIS4
         M = MIN0(J,IGH)                                                EIS4
C                                                                       EIS4
         DO 880 I = LOW, IGH                                            EIS4
            ZZ = 0.0D0                                                  EIS4
C                                                                       EIS4
            DO 860 K = LOW, M                                           EIS4
  860       ZZ = ZZ + Z(I,K) * H(K,J)                                   EIS4
C                                                                       EIS4
            Z(I,J) = ZZ                                                 EIS4
  880 CONTINUE                                                          EIS4
C                                                                       EIS4
      GO TO 1001                                                        EIS4
C     .......... SET ERROR -- ALL EIGENVALUES HAVE NOT                  EIS4
C                CONVERGED AFTER 30*N ITERATIONS ..........             EIS4
 1000 IERR = EN                                                         EIS4
 1001 RETURN                                                            EIS4
      END                                                               EIS4
