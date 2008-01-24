      SUBROUTINE BALBAK(NM,N,LOW,IGH,SCALE,M,Z)                         EIS0
C                                                                       EIS0
      INTEGER I,J,K,M,N,II,NM,IGH,LOW                                   EIS0
      DOUBLE PRECISION SCALE(N),Z(NM,M)                                 EIS0
      DOUBLE PRECISION S                                                EIS0
C                                                                       EIS0
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE BALBAK,   EIS0
C     NUM. MATH. 13, 293-304(1969) BY PARLETT AND REINSCH.              EIS0
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 315-326(1971).   EIS0
C                                                                       EIS0
C     THIS SUBROUTINE FORMS THE EIGENVECTORS OF A REAL GENERAL          EIS0
C     MATRIX BY BACK TRANSFORMING THOSE OF THE CORRESPONDING            EIS0
C     BALANCED MATRIX DETERMINED BY  BALANC.                            EIS0
C                                                                       EIS0
C     ON INPUT                                                          EIS0
C                                                                       EIS0
C        NM MUST BE SET TO THE ROW DIMENSION OF TWO-DIMENSIONAL         EIS0
C          ARRAY PARAMETERS AS DECLARED IN THE CALLING PROGRAM          EIS0
C          DIMENSION STATEMENT.                                         EIS0
C                                                                       EIS0
C        N IS THE ORDER OF THE MATRIX.                                  EIS0
C                                                                       EIS0
C        LOW AND IGH ARE INTEGERS DETERMINED BY  BALANC.                EIS0
C                                                                       EIS0
C        SCALE CONTAINS INFORMATION DETERMINING THE PERMUTATIONS        EIS0
C          AND SCALING FACTORS USED BY  BALANC.                         EIS0
C                                                                       EIS0
C        M IS THE NUMBER OF COLUMNS OF Z TO BE BACK TRANSFORMED.        EIS0
C                                                                       EIS0
C        Z CONTAINS THE REAL AND IMAGINARY PARTS OF THE EIGEN-          EIS0
C          VECTORS TO BE BACK TRANSFORMED IN ITS FIRST M COLUMNS.       EIS0
C                                                                       EIS0
C     ON OUTPUT                                                         EIS0
C                                                                       EIS0
C        Z CONTAINS THE REAL AND IMAGINARY PARTS OF THE                 EIS0
C          TRANSFORMED EIGENVECTORS IN ITS FIRST M COLUMNS.             EIS0
C                                                                       EIS0
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS0
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS0
C                                                                       EIS0
C     THIS VERSION DATED AUGUST 1983.                                   EIS0
C                                                                       EIS0
C     ------------------------------------------------------------------EIS0
C                                                                       EIS0
      IF (M .EQ. 0) GO TO 200                                           EIS0
      IF (IGH .EQ. LOW) GO TO 120                                       EIS0
C                                                                       EIS0
      DO 110 I = LOW, IGH                                               EIS0
         S = SCALE(I)                                                   EIS0
C     .......... LEFT HAND EIGENVECTORS ARE BACK TRANSFORMED            EIS0
C                IF THE FOREGOING STATEMENT IS REPLACED BY              EIS0
C                S=1.0D0/SCALE(I). ..........                           EIS0
         DO 100 J = 1, M                                                EIS0
  100    Z(I,J) = Z(I,J) * S                                            EIS0
C                                                                       EIS0
  110 CONTINUE                                                          EIS0
C     ......... FOR I=LOW-1 STEP -1 UNTIL 1,                            EIS0
C               IGH+1 STEP 1 UNTIL N DO -- ..........                   EIS0
  120 DO 140 II = 1, N                                                  EIS0
         I = II                                                         EIS0
         IF (I .GE. LOW .AND. I .LE. IGH) GO TO 140                     EIS0
         IF (I .LT. LOW) I = LOW - II                                   EIS0
         K = SCALE(I)                                                   EIS0
         IF (K .EQ. I) GO TO 140                                        EIS0
C                                                                       EIS0
         DO 130 J = 1, M                                                EIS0
            S = Z(I,J)                                                  EIS0
            Z(I,J) = Z(K,J)                                             EIS0
            Z(K,J) = S                                                  EIS0
  130    CONTINUE                                                       EIS0
C                                                                       EIS0
  140 CONTINUE                                                          EIS0
C                                                                       EIS0
  200 RETURN                                                            EIS0
      END                                                               EIS0
