      SUBROUTINE RG(NM,N,A,WR,WI,MATZ,Z,IV1,FV1,IERR)                   EIS8
C                                                                       EIS8
      INTEGER N,NM,IS1,IS2,IERR,MATZ                                    EIS8
      DOUBLE PRECISION A(NM,N),WR(N),WI(N),Z(NM,N),FV1(N)               EIS8
      INTEGER IV1(N)                                                    EIS8
C                                                                       EIS8
C     THIS SUBROUTINE CALLS THE RECOMMENDED SEQUENCE OF                 EIS8
C     SUBROUTINES FROM THE EIGENSYSTEM SUBROUTINE PACKAGE (EISPACK)     EIS8
C     TO FIND THE EIGENVALUES AND EIGENVECTORS (IF DESIRED)             EIS8
C     OF A REAL GENERAL MATRIX.                                         EIS8
C                                                                       EIS8
C     ON INPUT                                                          EIS8
C                                                                       EIS8
C        NM  MUST BE SET TO THE ROW DIMENSION OF THE TWO-DIMENSIONAL    EIS8
C        ARRAY PARAMETERS AS DECLARED IN THE CALLING PROGRAM            EIS8
C        DIMENSION STATEMENT.                                           EIS8
C                                                                       EIS8
C        N  IS THE ORDER OF THE MATRIX  A.                              EIS8
C                                                                       EIS8
C        A  CONTAINS THE REAL GENERAL MATRIX.                           EIS8
C                                                                       EIS8
C        MATZ  IS AN INTEGER VARIABLE SET EQUAL TO ZERO IF              EIS8
C        ONLY EIGENVALUES ARE DESIRED.  OTHERWISE IT IS SET TO          EIS8
C        ANY NON-ZERO INTEGER FOR BOTH EIGENVALUES AND EIGENVECTORS.    EIS8
C                                                                       EIS8
C     ON OUTPUT                                                         EIS8
C                                                                       EIS8
C        WR  AND  WI  CONTAIN THE REAL AND IMAGINARY PARTS,             EIS8
C        RESPECTIVELY, OF THE EIGENVALUES.  COMPLEX CONJUGATE           EIS8
C        PAIRS OF EIGENVALUES APPEAR CONSECUTIVELY WITH THE             EIS8
C        EIGENVALUE HAVING THE POSITIVE IMAGINARY PART FIRST.           EIS8
C                                                                       EIS8
C        Z  CONTAINS THE REAL AND IMAGINARY PARTS OF THE EIGENVECTORS   EIS8
C        IF MATZ IS NOT ZERO.  IF THE J-TH EIGENVALUE IS REAL, THE      EIS8
C        J-TH COLUMN OF  Z  CONTAINS ITS EIGENVECTOR.  IF THE J-TH      EIS8
C        EIGENVALUE IS COMPLEX WITH POSITIVE IMAGINARY PART, THE        EIS8
C        J-TH AND (J+1)-TH COLUMNS OF  Z  CONTAIN THE REAL AND          EIS8
C        IMAGINARY PARTS OF ITS EIGENVECTOR.  THE CONJUGATE OF THIS     EIS8
C        VECTOR IS THE EIGENVECTOR FOR THE CONJUGATE EIGENVALUE.        EIS8
C                                                                       EIS8
C        IERR  IS AN INTEGER OUTPUT VARIABLE SET EQUAL TO AN ERROR      EIS8
C           COMPLETION CODE DESCRIBED IN THE DOCUMENTATION FOR HQR      EIS8
C           AND HQR2.  THE NORMAL COMPLETION CODE IS ZERO.              EIS8
C                                                                       EIS8
C        IV1  AND  FV1  ARE TEMPORARY STORAGE ARRAYS.                   EIS8
C                                                                       EIS8
C     QUESTIONS AND COMMENTS SHOULD BE DIRECTED TO BURTON S. GARBOW,    EIS8
C     MATHEMATICS AND COMPUTER SCIENCE DIV, ARGONNE NATIONAL LABORATORY EIS8
C                                                                       EIS8
C     THIS VERSION DATED AUGUST 1983.                                   EIS8
C                                                                       EIS8
C     ------------------------------------------------------------------EIS8
C                                                                       EIS8
      IF (N .LE. NM) GO TO 10                                           EIS8
      IERR = 10 * N                                                     EIS8
      GO TO 50                                                          EIS8
C                                                                       EIS8
   10 CALL  BALANC(NM,N,A,IS1,IS2,FV1)                                  EIS8
      CALL  ELMHES(NM,N,IS1,IS2,A,IV1)                                  EIS8
      IF (MATZ .NE. 0) GO TO 20                                         EIS8
C     .......... FIND EIGENVALUES ONLY ..........                       EIS8
      CALL  HQR(NM,N,IS1,IS2,A,WR,WI,IERR)                              EIS8
      GO TO 50                                                          EIS8
C     .......... FIND BOTH EIGENVALUES AND EIGENVECTORS ..........      EIS8
   20 CALL  ELTRAN(NM,N,IS1,IS2,A,IV1,Z)                                EIS8
      CALL  HQR2(NM,N,IS1,IS2,A,WR,WI,Z,IERR)                           EIS8
      IF (IERR .NE. 0) GO TO 50                                         EIS8
      CALL  BALBAK(NM,N,IS1,IS2,FV1,N,Z)                                EIS8
   50 RETURN                                                            EIS8
      END                                                               EIS8
