      SUBROUTINE ELTRAN(NM,N,LOW,IGH,A,INT,Z)                           EIS4
C                                                                       EIS4
      INTEGER I,J,N,KL,MM,MP,NM,IGH,LOW,MP1                             EIS4
      DOUBLE PRECISION A(NM,IGH),Z(NM,N)                                EIS4
      INTEGER INT(IGH)                                                  EIS4
C                                                                       EIS4
C     THIS SUBROUTINE IS A TRANSLATION OF THE ALGOL PROCEDURE ELMTRANS, EIS4
C     NUM. MATH. 16, 181-204(1970) BY PETERS AND WILKINSON.             EIS4
C     HANDBOOK FOR AUTO. COMP., VOL.II-LINEAR ALGEBRA, 372-395(1971).   EIS4
C                                                                       EIS4
C     THIS SUBROUTINE ACCUMULATES THE STABILIZED ELEMENTARY             EIS4
C     SIMILARITY TRANSFORMATIONS USED IN THE REDUCTION OF A             EIS4
C     REAL GENERAL MATRIX TO UPPER HESSENBERG FORM BY  ELMHES.          EIS4
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
C        A CONTAINS THE MULTIPLIERS WHICH WERE USED IN THE              EIS4
C          REDUCTION BY  ELMHES  IN ITS LOWER TRIANGLE                  EIS4
C          BELOW THE SUBDIAGONAL.                                       EIS4
C                                                                       EIS4
C        INT CONTAINS INFORMATION ON THE ROWS AND COLUMNS               EIS4
C          INTERCHANGED IN THE REDUCTION BY  ELMHES.                    EIS4
C          ONLY ELEMENTS LOW THROUGH IGH ARE USED.                      EIS4
C                                                                       EIS4
C     ON OUTPUT                                                         EIS4
C                                                                       EIS4
C        Z CONTAINS THE TRANSFORMATION MATRIX PRODUCED IN THE           EIS4
C          REDUCTION BY  ELMHES.                                        EIS4
C                                                                       EIS4
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS4
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS4
C                                                                       EIS4
C     THIS VERSION DATED AUGUST 1983.                                   EIS4
C                                                                       EIS4
C     ------------------------------------------------------------------EIS4
C                                                                       EIS4
C     .......... INITIALIZE Z TO IDENTITY MATRIX ..........             EIS4
      DO 80 J = 1, N                                                    EIS4
C                                                                       EIS4
         DO 60 I = 1, N                                                 EIS4
   60    Z(I,J) = 0.0D0                                                 EIS4
C                                                                       EIS4
         Z(J,J) = 1.0D0                                                 EIS4
   80 CONTINUE                                                          EIS4
C                                                                       EIS4
      KL = IGH - LOW - 1                                                EIS4
      IF (KL .LT. 1) GO TO 200                                          EIS4
C     .......... FOR MP=IGH-1 STEP -1 UNTIL LOW+1 DO -- ..........      EIS4
      DO 140 MM = 1, KL                                                 EIS4
         MP = IGH - MM                                                  EIS4
         MP1 = MP + 1                                                   EIS4
C                                                                       EIS4
         DO 100 I = MP1, IGH                                            EIS4
  100    Z(I,MP) = A(I,MP-1)                                            EIS4
C                                                                       EIS4
         I = INT(MP)                                                    EIS4
         IF (I .EQ. MP) GO TO 140                                       EIS4
C                                                                       EIS4
         DO 130 J = MP, IGH                                             EIS4
            Z(MP,J) = Z(I,J)                                            EIS4
            Z(I,J) = 0.0D0                                              EIS4
  130    CONTINUE                                                       EIS4
C                                                                       EIS4
         Z(I,MP) = 1.0D0                                                EIS4
  140 CONTINUE                                                          EIS4
C                                                                       EIS4
  200 RETURN                                                            EIS4
      END                                                               EIS4
