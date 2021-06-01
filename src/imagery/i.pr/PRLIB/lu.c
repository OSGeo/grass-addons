/*
   Same of the following routines are borrowed from "Numerical Recipes in C"
   other are written and tested by Stefano Merler

   for

   LU matrix decomposition, linear equation solution (Ax=b), inversion
   of matrices and deteminant computation
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>


#define CTINY 1.0e-32

void ludcmp(a, n, indx, d)
     /*
        LU decomposition of n x n matrix a.
      */
     int n, *indx;
     double **a, *d;
{
    int i, imax = 0, j, k;
    double big, dum, sum, temp;
    double *vv;

    vv = (double *)calloc(n, sizeof(double));
    *d = 1.0;
    for (i = 0; i < n; i++) {
	big = 0;
	for (j = 0; j < n; j++)
	    if ((temp = fabs(a[i][j])) > big)
		big = temp;
	if (big == 0.0) {
	    fprintf(stderr, "Singular matrix in routine ludcmp\n");
	    exit(1);
	}
	vv[i] = 1.0 / big;
    }
    for (j = 0; j < n; j++) {
	for (i = 0; i < j; i++) {
	    sum = a[i][j];
	    for (k = 0; k < i; k++)
		sum -= a[i][k] * a[k][j];
	    a[i][j] = sum;
	}
	big = 0.0;
	for (i = j; i < n; i++) {
	    sum = a[i][j];
	    for (k = 0; k < j; k++)
		sum -= a[i][k] * a[k][j];
	    a[i][j] = sum;
	    if ((dum = vv[i] * fabs(sum)) >= big) {
		big = dum;
		imax = i;
	    }
	}
	if (j != imax) {
	    for (k = 0; k < n; k++) {
		dum = a[imax][k];
		a[imax][k] = a[j][k];
		a[j][k] = dum;
	    }
	    *d = -(*d);
	    vv[imax] = vv[j];
	}
	indx[j] = imax;
	if (a[j][j] == 0.0)
	    a[j][j] = CTINY;
	if (j != n) {
	    dum = 1.0 / a[j][j];
	    for (i = j + 1; i < n; i++)
		a[i][j] *= dum;
	}
    }
    free(vv);
}

#undef CTINY


void lubksb(a, n, indx, b)
     /* 
        Solve linear equation Ax=B
        a has to be a LU decomposed n x n matrix, and indx 
        is usually the output of ludcmp.
        On output, b contains the solution
      */
     double **a, b[];
     int n, *indx;
{
    int i, ii = -1, ip, j;
    double sum;

    for (i = 0; i < n; i++) {
	ip = indx[i];
	sum = b[ip];
	b[ip] = b[i];
	if (ii >= 0)
	    for (j = ii; j <= i - 1; j++)
		sum -= a[i][j] * b[j];
	else if (sum != 0.0)
	    ii = i;
	b[i] = sum;
    }
    for (i = n - 1; i >= 0; i--) {
	sum = b[i];
	for (j = i + 1; j < n; j++)
	    sum -= a[i][j] * b[j];
	b[i] = sum / a[i][i];
    }
}

void inverse_of_double_matrix(A, inv_A, n)
     /* 
        Inverse of a matrix A of dimension n x n.
        Output stored in inv_A
      */
     double **A, **inv_A;
     int n;
{
    double d, *col, **tmpA;
    int i, j, *indx;

    tmpA = (double **)calloc(n, sizeof(double *));
    for (j = 0; j < n; j++)
	tmpA[j] = (double *)calloc(n, sizeof(double));

    for (j = 0; j < n; j++)
	for (i = 0; i < n; i++)
	    tmpA[j][i] = A[j][i];

    col = (double *)calloc(n, sizeof(double));
    indx = (int *)calloc(n, sizeof(int));

    ludcmp(tmpA, n, indx, &d);
    for (j = 0; j < n; j++) {
	for (i = 0; i < n; i++)
	    col[i] = 0;
	col[j] = 1;
	lubksb(tmpA, n, indx, col);
	for (i = 0; i < n; i++)
	    inv_A[i][j] = col[i];
    }

    free(col);
    free(indx);
    for (j = 0; j < n; j++)
	free(tmpA[j]);
    free(tmpA);

}

double determinant_of_double_matrix(A, n)
     /* 
        determinant of a double matrix A of dimension n x n
      */
     double **A;
     int n;
{
    double d, **tmpA;
    int i, j, *indx;

    tmpA = (double **)calloc(n, sizeof(double *));
    for (j = 0; j < n; j++)
	tmpA[j] = (double *)calloc(n, sizeof(double));

    for (j = 0; j < n; j++)
	for (i = 0; i < n; i++)
	    tmpA[j][i] = A[j][i];

    indx = (int *)calloc(n, sizeof(int));

    ludcmp(tmpA, n, indx, &d);

    for (j = 0; j < n; j++)
	d *= tmpA[j][j];

    free(indx);
    for (j = 0; j < n; j++)
	free(tmpA[j]);
    free(tmpA);

    return (d);

}
