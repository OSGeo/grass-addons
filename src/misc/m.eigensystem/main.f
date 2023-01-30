       PROGRAM EIGEN
C
C Computes eigenvalues and eigenvectors for an NxN matrix
C
C AUTHOR: Michael Shapiro, U.S.Army Construction Engineering Research Laboratory
C
C COPYRIGHT:    (C) 1999 by the GRASS Development Team
C
C               This program is free software under the GNU General Public
C               License (>=v2). Read the file COPYING that comes with GRASS
C               for details.
C
C The input is from stdin and has the following format
C
C First line contains one positive integer N, the diminension of the matrix
C The the matrix of real values follows N reals per line each separated by
C white space:
C
C   3
C   1.2 2.3 3.4
C   0.1 12.3 34.5676
C   2 12.45 2
C
C
C Currently, the max value for N is 30
C
C The output is N sets of values. One E line and N V W lines
C
C  E   real  imaginary   percent-importance
C  V   real  imaginary
C  N   real  imaginary
C  W   real  imaginary
C      ...
C
C where E is the eigen value (and it relative importance)
C and   V are the eigenvector for this eigenvalue.
C       N are the normalized eigenvector for this eigenvalue.
C       W are the N vector multiplied by the square root of the magnitude
C         of the eigen value (E).

C
       DOUBLE PRECISION A(30,30),W1,W2,WR(30),WI(30),Z(30,30),FV1(30)
       DOUBLE PRECISION SUM1,SUM2
       INTEGER          IV1(30),N

C
C read the matrix size
       READ(5,*,END=1000) N
       IF(N.LT.1) GOTO 2000
       IF(N.GT.30) GOTO 3000
C      PRINT *,"N=",N

C
C read the matrix
       READ(5,*,END=1000) (( A(I,J),J=1,N),I=1,N)

C
C run the real-general eigen subroutine
       CALL RG(30,N,A,WR,WI,1,Z,IV1,FV1,IERR)
       IF (IERR.NE.0) WRITE(6,*) "? ERROR CODE",IERR


C
C WR and WI contain the real and imaginary parts of the eigenvalues
C Z contains the vectors
       SUM1 = 0.0
       DO 1 I=1,N
    1  SUM1 = SUM1 + SQRT(WR(I)*WR(I)+WI(I)*WI(I))
       DO 2 I=1,N
       W1 = SQRT(WR(I)*WR(I)+WI(I)*WI(I))
       W2 = SQRT(W1)
       WRITE(6,100) "E",WR(I),WI(I), W1/SUM1 * 100.0

C
C Normalize the eigenvectors before printing
       SUM2 = 0.0
       DO 6 J=1,N
       IF(WI(I))3,4,5
    3  SUM2 = SUM2 + Z(J,I-1) * Z(J,I-1) + Z(J,I) * Z(J,I)
       GOTO 6
    4  SUM2 = SUM2 + Z(J,I) * Z(J,I)
       GOTO 6
    5  SUM2 = SUM2 + Z(J,I+1) * Z(J,I+1) + Z(J,I) * Z(J,I)
    6  CONTINUE
       SUM2 = SQRT(SUM2)


       DO 16 J=1,N
       IF(WI(I))13,14,15
   13  WRITE(6,100) "V",Z(J,I-1),-Z(J,I)
       GOTO 16
   14  WRITE(6,100) "V",Z(J,I),0.0
       GOTO 16
   15  WRITE(6,100) "V",Z(J,I),Z(J,I+1)
   16  CONTINUE

       DO 26 J=1,N
       IF(WI(I))23,24,25
   23  WRITE(6,100) "N",Z(J,I-1)/SUM2,-Z(J,I)/SUM2
       GOTO 26
   24  WRITE(6,100) "N",Z(J,I)/SUM2,0.0
       GOTO 26
   25  WRITE(6,100) "N",Z(J,I)/SUM2,Z(J,I+1)/SUM2
   26  CONTINUE

       DO 36 J=1,N
       IF(WI(I))33,34,35
   33  WRITE(6,100) "W",W2*Z(J,I-1)/SUM2,-W2*Z(J,I)/SUM2
       GOTO 36
   34  WRITE(6,100) "W",W2*Z(J,I)/SUM2,0.0
       GOTO 36
   35  WRITE(6,100) "W",W2*Z(J,I)/SUM2,W2*Z(J,I+1)/SUM2
   36  CONTINUE

    2  CONTINUE


C
       CALL EXIT(0)
 1000  PRINT *,"Incomplete input file"
       CALL EXIT(1)
 2000  PRINT *,"N must be positive"
       CALL EXIT(1)
 3000  PRINT *,"Maximum array size is 30"
       CALL EXIT(1)

  100  FORMAT(A1,1x,F20.10,1x,F20.10,3x,F6.2)
       END
