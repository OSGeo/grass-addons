      SUBROUTINE BALANC(NM,N,A,LOW,IGH,SCALE)                           EIS0
C                                                                       EIS0
      INTEGER I,J,K,L,M,N,JJ,NM,IGH,LOW,IEXC                            EIS0
      DOUBLE PRECISION A(NM,N),SCALE(N)                                 EIS0
      DOUBLE PRECISION C,F,G,R,S,B2,RADIX                               EIS0
      LOGICAL NOCONV                                                    EIS0
C                                                                       EIS0
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE BALANCE,  EIS0
C     NUM. MATH. 13, 293-304(1969) BY PARLETT AND REINSCH.              EIS0
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 315-326(1971).   EIS0
C                                                                       EIS0
C     THIS SUBROUTINE BALANCES A REAL MATRIX AND ISOLATES               EIS0
C     EIGENVALUES WHENEVER POSSIBLE.                                    EIS0
C                                                                       EIS0
C     ON INPUT                                                          EIS0
C                                                                       EIS0
C        NM MUST BE SET TO THE ROW DIMENSION OF TWO-DIMENSIONAL         EIS0
C          ARRAY PARAMETERS AS DECLARED IN THE CALLING PROGRAM          EIS0
C          DIMENSION STATEMENT.                                         EIS0
C                                                                       EIS0
C        N IS THE ORDER OF THE MATRIX.                                  EIS0
C                                                                       EIS0
C        A CONTAINS THE INPUT MATRIX TO BE BALANCED.                    EIS0
C                                                                       EIS0
C     ON OUTPUT                                                         EIS0
C                                                                       EIS0
C        A CONTAINS THE BALANCED MATRIX.                                EIS0
C                                                                       EIS0
C        LOW AND IGH ARE TWO INTEGERS SUCH THAT A(I,J)                  EIS0
C          IS EQUAL TO ZERO IF                                          EIS0
C           (1) I IS GREATER THAN J AND                                 EIS0
C           (2) J=1,...,LOW-1 OR I=IGH+1,...,N.                         EIS0
C                                                                       EIS0
C        SCALE CONTAINS INFORMATION DETERMINING THE                     EIS0
C           PERMUTATIONS AND SCALING FACTORS USED.                      EIS0
C                                                                       EIS0
C     SUPPOSE THAT THE PRINCIPAL SUBMATRIX IN ROWS LOW THROUGH IGH      EIS0
C     HAS BEEN BALANCED, THAT P(J) DENOTES THE INDEX INTERCHANGED       EIS0
C     WITH J DURING THE PERMUTATION STEP, AND THAT THE ELEMENTS         EIS0
C     OF THE DIAGONAL MATRIX USED ARE DENOTED BY D(I,J).  THEN          EIS0
C        SCALE(J) = P(J),    FOR J = 1,...,LOW-1                        EIS0
C                 = D(J,J),      J = LOW,...,IGH                        EIS0
C                 = P(J)         J = IGH+1,...,N.                       EIS0
C     THE ORDER IN WHICH THE INTERCHANGES ARE MADE IS N TO IGH+1,       EIS0
C     THEN 1 TO LOW-1.                                                  EIS0
C                                                                       EIS0
C     NOTE THAT 1 IS RETURNED FOR IGH IF IGH IS ZERO FORMALLY.          EIS0
C                                                                       EIS0
C     THE ALGOL PROCEDURE EXC CONTAINED IN BALANCE APPEARS IN           EIS0
C     BALANC  IN LINE.  (NOTE THAT THE ALGOL ROLES OF IDENTIFIERS       EIS0
C     K,L HAVE BEEN REVERSED.)                                          EIS0
C                                                                       EIS0
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS0
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS0
C                                                                       EIS0
C     THIS VERSION DATED AUGUST 1983.                                   EIS0
C                                                                       EIS0
C     ------------------------------------------------------------------EIS0
C                                                                       EIS0
      RADIX = 16.0D0                                                    EIS0
C                                                                       EIS0
      B2 = RADIX * RADIX                                                EIS0
      K = 1                                                             EIS0
      L = N                                                             EIS0
      GO TO 100                                                         EIS0
C     .......... IN-LINE PROCEDURE FOR ROW AND                          EIS0
C                COLUMN EXCHANGE ..........                             EIS0
   20 SCALE(M) = J                                                      EIS0
      IF (J .EQ. M) GO TO 50                                            EIS0
C                                                                       EIS0
      DO 30 I = 1, L                                                    EIS0
         F = A(I,J)                                                     EIS0
         A(I,J) = A(I,M)                                                EIS0
         A(I,M) = F                                                     EIS0
   30 CONTINUE                                                          EIS0
C                                                                       EIS0
      DO 40 I = K, N                                                    EIS0
         F = A(J,I)                                                     EIS0
         A(J,I) = A(M,I)                                                EIS0
         A(M,I) = F                                                     EIS0
   40 CONTINUE                                                          EIS0
C                                                                       EIS0
   50 GO TO (80,130), IEXC                                              EIS0
C     .......... SEARCH FOR ROWS ISOLATING AN EIGENVALUE                EIS0
C                AND PUSH THEM DOWN ..........                          EIS0
   80 IF (L .EQ. 1) GO TO 280                                           EIS0
      L = L - 1                                                         EIS0
C     .......... FOR J=L STEP -1 UNTIL 1 DO -- ..........               EIS0
  100 DO 120 JJ = 1, L                                                  EIS0
         J = L + 1 - JJ                                                 EIS0
C                                                                       EIS0
         DO 110 I = 1, L                                                EIS0
            IF (I .EQ. J) GO TO 110                                     EIS0
            IF (A(J,I) .NE. 0.0D0) GO TO 120                            EIS0
  110    CONTINUE                                                       EIS0
C                                                                       EIS0
         M = L                                                          EIS0
         IEXC = 1                                                       EIS0
         GO TO 20                                                       EIS0
  120 CONTINUE                                                          EIS0
C                                                                       EIS0
      GO TO 140                                                         EIS0
C     .......... SEARCH FOR COLUMNS ISOLATING AN EIGENVALUE             EIS0
C                AND PUSH THEM LEFT ..........                          EIS0
  130 K = K + 1                                                         EIS0
C                                                                       EIS0
  140 DO 170 J = K, L                                                   EIS0
C                                                                       EIS0
         DO 150 I = K, L                                                EIS0
            IF (I .EQ. J) GO TO 150                                     EIS0
            IF (A(I,J) .NE. 0.0D0) GO TO 170                            EIS0
  150    CONTINUE                                                       EIS0
C                                                                       EIS0
         M = K                                                          EIS0
         IEXC = 2                                                       EIS0
         GO TO 20                                                       EIS0
  170 CONTINUE                                                          EIS0
C     .......... NOW BALANCE THE SUBMATRIX IN ROWS K TO L ..........    EIS0
      DO 180 I = K, L                                                   EIS0
  180 SCALE(I) = 1.0D0                                                  EIS0
C     .......... ITERATIVE LOOP FOR NORM REDUCTION ..........           EIS0
  190 NOCONV = .FALSE.                                                  EIS0
C                                                                       EIS0
      DO 270 I = K, L                                                   EIS0
         C = 0.0D0                                                      EIS0
         R = 0.0D0                                                      EIS0
C                                                                       EIS0
         DO 200 J = K, L                                                EIS0
            IF (J .EQ. I) GO TO 200                                     EIS0
            C = C + DABS(A(J,I))                                        EIS0
            R = R + DABS(A(I,J))                                        EIS0
  200    CONTINUE                                                       EIS0
C     .......... GUARD AGAINST ZERO C OR R DUE TO UNDERFLOW ..........  EIS0
         IF (C .EQ. 0.0D0 .OR. R .EQ. 0.0D0) GO TO 270                  EIS0
         G = R / RADIX                                                  EIS0
         F = 1.0D0                                                      EIS0
         S = C + R                                                      EIS0
  210    IF (C .GE. G) GO TO 220                                        EIS0
         F = F * RADIX                                                  EIS0
         C = C * B2                                                     EIS0
         GO TO 210                                                      EIS0
  220    G = R * RADIX                                                  EIS0
  230    IF (C .LT. G) GO TO 240                                        EIS0
         F = F / RADIX                                                  EIS0
         C = C / B2                                                     EIS0
         GO TO 230                                                      EIS0
C     .......... NOW BALANCE ..........                                 EIS0
  240    IF ((C + R) / F .GE. 0.95D0 * S) GO TO 270                     EIS0
         G = 1.0D0 / F                                                  EIS0
         SCALE(I) = SCALE(I) * F                                        EIS0
         NOCONV = .TRUE.                                                EIS0
C                                                                       EIS0
         DO 250 J = K, N                                                EIS0
  250    A(I,J) = A(I,J) * G                                            EIS0
C                                                                       EIS0
         DO 260 J = 1, L                                                EIS0
  260    A(J,I) = A(J,I) * F                                            EIS0
C                                                                       EIS0
  270 CONTINUE                                                          EIS0
C                                                                       EIS0
      IF (NOCONV) GO TO 190                                             EIS0
C                                                                       EIS0
  280 LOW = K                                                           EIS0
      IGH = L                                                           EIS0
      RETURN                                                            EIS0
      END                                                               EIS0
