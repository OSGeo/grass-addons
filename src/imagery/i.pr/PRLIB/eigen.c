/*
   Same of the following routines are borrowed from "Numerical Recipes in C"
   other are written and tested by Stefano Merler

   for

   Eigenvalues and eigenvectors of simmetric matrices compution
   and management
 */

#include <math.h>
#include <stdlib.h>
#include <grass/gis.h>


#define MAX_ITERS 30
#define SIGN(a,b) ((b)<0 ? -fabs(a) : fabs(a))



void tred2(double **a, int n, double d[], double e[])

     /*
        Houserholder method for reduction of simmetric n x n matrix a to 
        tridiagonal form: on output a contains the ortogonal transformation
        matrix, d contains the diagonal elements, and e the off-diagonal.
      */
{
    int l, k, j, i;
    double scale, hh, h, g, f;

    for (i = n - 1; i >= 1; i--) {
	l = i - 1;
	h = scale = 0.0;
	if (l > 0) {
	    for (k = 0; k <= l; k++)
		scale += fabs(a[i][k]);
	    if (scale == 0.0)
		e[i] = a[i][l];
	    else {
		for (k = 0; k <= l; k++) {
		    a[i][k] /= scale;
		    h += a[i][k] * a[i][k];
		}
		f = a[i][l];
		g = f > 0 ? -sqrt(h) : sqrt(h);
		e[i] = scale * g;
		h -= f * g;
		a[i][l] = f - g;
		f = 0.0;
		for (j = 0; j <= l; j++) {
		    /* Next statement can be omitted if eigenvectors not wanted */
		    a[j][i] = a[i][j] / h;
		    g = 0.0;
		    for (k = 0; k <= j; k++)
			g += a[j][k] * a[i][k];
		    for (k = j + 1; k <= l; k++)
			g += a[k][j] * a[i][k];
		    e[j] = g / h;
		    f += e[j] * a[i][j];
		}
		hh = f / (h + h);
		for (j = 0; j <= l; j++) {
		    f = a[i][j];
		    e[j] = g = e[j] - hh * f;
		    for (k = 0; k <= j; k++)
			a[j][k] -= (f * e[k] + g * a[i][k]);
		}
	    }
	}
	else
	    e[i] = a[i][l];
	d[i] = h;
    }
    /* Next statement can be omitted if eigenvectors not wanted */
    d[0] = 0.0;
    e[0] = 0.0;
    /* Contents of this loop can be omitted if eigenvectors not
       wanted except for statement d[i]=a[i][i]; */
    for (i = 0; i < n; i++) {
	l = i - 1;
	if (d[i]) {
	    for (j = 0; j <= l; j++) {
		g = 0.0;
		for (k = 0; k <= l; k++)
		    g += a[i][k] * a[k][j];
		for (k = 0; k <= l; k++)
		    a[k][j] -= g * a[k][i];
	    }
	}
	d[i] = a[i][i];
	a[i][i] = 1.0;
	for (j = 0; j <= l; j++)
	    a[j][i] = a[i][j] = 0.0;
    }
}


int tqli(double d[], double e[], int n, double **z)

     /*
        QL algorithm: compute eigenvalues and eigenvectors 
        of simmetric tridiagonal matrix. On input, d diagonal 
        and e off-diagonal elements of the matrix (usually the 
        output of tred2), z the matrix output of tred2.
        On output d eigenvalues, z eigenvectors.
      */
{
    int m, l, iter, i, k;
    double s, r, p, g, f, dd, c, b;

    for (i = 1; i < n; i++)
	e[i - 1] = e[i];
    e[n - 1] = 0.0;
    for (l = 0; l < n; l++) {
	iter = 0;
	do {
	    for (m = l; m < n - 1; m++) {
		dd = fabs(d[m]) + fabs(d[m + 1]);
		if (fabs(e[m]) + dd == dd)
		    break;
	    }
	    if (m != l) {
		if (iter++ == MAX_ITERS)
		    return 0;	/* Too many iterations in TQLI */
		g = (d[l + 1] - d[l]) / (2.0 * e[l]);
		r = sqrt((g * g) + 1.0);
		g = d[m] - d[l] + e[l] / (g + SIGN(r, g));
		s = c = 1.0;
		p = 0.0;
		for (i = m - 1; i >= l; i--) {
		    f = s * e[i];
		    b = c * e[i];
		    if (fabs(f) >= fabs(g)) {
			c = g / f;
			r = sqrt((c * c) + 1.0);
			e[i + 1] = f * r;
			c *= (s = 1.0 / r);
		    }
		    else {
			s = f / g;
			r = sqrt((s * s) + 1.0);
			e[i + 1] = g * r;
			s *= (c = 1.0 / r);
		    }
		    g = d[i + 1] - p;
		    r = (d[i] - g) * s + 2.0 * c * b;
		    p = s * r;
		    d[i + 1] = g + p;
		    g = c * r - b;
		    /* Next loop can be omitted if eigenvectors not wanted */
		    for (k = 0; k < n; k++) {
			f = z[k][i + 1];
			z[k][i + 1] = s * z[k][i] + c * f;
			z[k][i] = c * z[k][i] - s * f;
		    }
		}
		d[l] = d[l] - p;
		e[l] = g;
		e[m] = 0.0;
	    }
	} while (m != l);
    }
    return 1;
}




void eigen_of_double_matrix(double **M, double **Vectors, double *lambda,
			    int n)

     /* 
        Computes eigenvalues (and eigen vectors if desired) for 
        symmetric matrix M of dimension n x n.
        Vectors and lambda contain the (obvious) output.
      */
{
    int i, j;
    double **a, *e;

    a = (double **)G_calloc(n, sizeof(double *));
    for (i = 0; i < n; i++)
	a[i] = (double *)G_calloc(n, sizeof(double));

    e = (double *)G_calloc(n, sizeof(double));

    for (i = 0; i < n; i++)
	for (j = 0; j < n; j++)
	    a[i][j] = M[i][j];

    tred2(a, n, lambda, e);
    tqli(lambda, e, n, a);

    /* Returns eigenvectors       */
    for (i = 0; i < n; i++)
	for (j = 0; j < n; j++)
	    Vectors[i][j] = a[i][j];

    for (i = 0; i < n; i++)
	G_free(a[i]);
    G_free(a);
    G_free(e);
}

void eigsrt(double *d, double **z, int bands)

     /* sort eigenvalues d in descending order, and rearranges 
        eigenvectors z correspondingly. bands contains the number 
        of eigenvalues = rows of z = cols of z
      */
{
    double p;
    long i, j, k;

    for (i = 0; i < (bands - 1); i++) {
	p = d[k = i];
	for (j = i + 1; j < bands; j++)
	    if (d[j] >= p)
		p = d[k = j];
	/*
	   interchange eigen values i and k and corresponding eigen vectors
	 */
	if (k != i) {
	    d[k] = d[i];
	    d[i] = p;
	    for (j = 0; j < bands; j++) {
		p = z[j][i];
		z[j][i] = z[j][k];
		z[j][k] = p;
	    }
	}
    }
}


#undef MAX_ITERS
