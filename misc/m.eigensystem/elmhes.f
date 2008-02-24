      SUBROUTINE ELMHES(NM,N,LOW,IGH,A,INT)                             EIS3
C                                                                       EIS3
      INTEGER I,J,M,N,LA,NM,IGH,KP1,LOW,MM1,MP1                         EIS3
      DOUBLE PRECISION A(NM,N)                                          EIS3
      DOUBLE PRECISION X,Y                                              EIS3
      INTEGER INT(IGH)                                                  EIS3
C                                                                       EIS3
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE ELMHES,   EIS3
C     NUM. MATH. 12, 349-368(1968) BY MARTIN AND WILKINSON.             EIS3
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 339-358(1971).   EIS3
C                                                                       EIS3
C     GIVEN A REAL GENERAL MATRIX, THIS SUBROUTINE                      EIS3
C     REDUCES A SUBMATRIX SITUATED IN ROWS AND COLUMNS                  EIS3
C     LOW THROUGH IGH TO UPPER HESSENBERG FORM BY                       EIS3
C     STABILIZED ELEMENTARY SIMILARITY TRANSFORMATIONS.                 EIS3
C                                                                       EIS3
C     ON INPUT                                                          EIS3
C                                                                       EIS3
C        NM MUST BE SET TO THE ROW DIMENSION OF TWO-DIMENSIONAL         EIS3
C          ARRAY PARAMETERS AS DECLARED IN THE CALLING PROGRAM          EIS3
C          DIMENSION STATEMENT.                                         EIS3
C                                                                       EIS3
C        N IS THE ORDER OF THE MATRIX.                                  EIS3
C                                                                       EIS3
C        LOW AND IGH ARE INTEGERS DETERMINED BY THE BALANCING           EIS3
C          SUBROUTINE  BALANC.  IF  BALANC  HAS NOT BEEN USED,          EIS3
C          SET LOW=1, IGH=N.                                            EIS3
C                                                                       EIS3
C        A CONTAINS THE INPUT MATRIX.                                   EIS3
C                                                                       EIS3
C     ON OUTPUT                                                         EIS3
C                                                                       EIS3
C        A CONTAINS THE HESSENBERG MATRIX.  THE MULTIPLIERS             EIS3
C          WHICH WERE USED IN THE REDUCTION ARE STORED IN THE           EIS3
C          REMAINING TRIANGLE UNDER THE HESSENBERG MATRIX.              EIS3
C                                                                       EIS3
C        INT CONTAINS INFORMATION ON THE ROWS AND COLUMNS               EIS3
C          INTERCHANGED IN THE REDUCTION.                               EIS3
C          ONLY ELEMENTS LOW THROUGH IGH ARE USED.                      EIS3
C                                                                       EIS3
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS3
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS3
C                                                                       EIS3
C     THIS VERSION DATED AUGUST 1983.                                   EIS3
C                                                                       EIS3
C     ------------------------------------------------------------------EIS3
C                                                                       EIS3
      LA = IGH - 1                                                      EIS3
      KP1 = LOW + 1                                                     EIS3
      IF (LA .LT. KP1) GO TO 200                                        EIS3
C                                                                       EIS3
      DO 180 M = KP1, LA                                                EIS3
         MM1 = M - 1                                                    EIS3
         X = 0.0D0                                                      EIS3
         I = M                                                          EIS3
C                                                                       EIS3
         DO 100 J = M, IGH                                              EIS3
            IF (DABS(A(J,MM1)) .LE. DABS(X)) GO TO 100                  EIS3
            X = A(J,MM1)                                                EIS3
            I = J                                                       EIS3
  100    CONTINUE                                                       EIS3
C                                                                       EIS3
         INT(M) = I                                                     EIS3
         IF (I .EQ. M) GO TO 130                                        EIS3
C     .......... INTERCHANGE ROWS AND COLUMNS OF A ..........           EIS3
         DO 110 J = MM1, N                                              EIS3
            Y = A(I,J)                                                  EIS3
            A(I,J) = A(M,J)                                             EIS3
            A(M,J) = Y                                                  EIS3
  110    CONTINUE                                                       EIS3
C                                                                       EIS3
         DO 120 J = 1, IGH                                              EIS3
            Y = A(J,I)                                                  EIS3
            A(J,I) = A(J,M)                                             EIS3
            A(J,M) = Y                                                  EIS3
  120    CONTINUE                                                       EIS3
C     .......... END INTERCHANGE ..........                             EIS3
  130    IF (X .EQ. 0.0D0) GO TO 180                                    EIS3
         MP1 = M + 1                                                    EIS3
C                                                                       EIS3
         DO 160 I = MP1, IGH                                            EIS3
            Y = A(I,MM1)                                                EIS3
            IF (Y .EQ. 0.0D0) GO TO 160                                 EIS3
            Y = Y / X                                                   EIS3
            A(I,MM1) = Y                                                EIS3
C                                                                       EIS3
            DO 140 J = M, N                                             EIS3
  140       A(I,J) = A(I,J) - Y * A(M,J)                                EIS3
C                                                                       EIS3
            DO 150 J = 1, IGH                                           EIS3
  150       A(J,M) = A(J,M) + Y * A(J,I)                                EIS3
C                                                                       EIS3
  160    CONTINUE                                                       EIS3
C                                                                       EIS3
  180 CONTINUE                                                          EIS3
C                                                                       EIS3
  200 RETURN                                                            EIS3
      END                                                               EIS3
