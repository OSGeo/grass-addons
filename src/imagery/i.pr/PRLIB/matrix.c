/*
   The following routines are written and tested by Stefano Merler

   for

   management of matrices and arrays

   Supported function for
   - product matrix matrix or vector matrix
   - transpose matrix
   - conversion of matrix to array
   - extraction of portion of matrix
 */

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>

void product_double_matrix_double_matrix(double **x, double **y, int r, int cr,
                                         int c, double **out)

/*
   product of matrices x * y,
   r = rows of x
   cr= cols of x = rows of y
   c = cols of y
   out is the r x c matrix.
 */
{
    int i, j, h;

    for (i = 0; i < r; i++)
        for (j = 0; j < c; j++) {
            out[i][j] = .0;
            for (h = 0; h < cr; h++)
                out[i][j] += x[i][h] * y[h][j];
        }
}

void product_double_matrix_double_vector(double **x, double *y, int r, int cr,
                                         double *out)

/*
   vector x matrix y * x,
   r = rows of x
   cr= cols of x = elements of y
   out is the output vector (r elements) . Memory for out is not stored.
 */
{
    int i, h;

    for (i = 0; i < r; i++) {
        out[i] = .0;
        for (h = 0; h < cr; h++)
            out[i] += x[i][h] * y[h];
    }
}

void product_double_vector_double_matrix(double **x, double *y, int rr, int c,
                                         double *out)

/*
   vector x matrix y * x,
   rr = rows of x = elements of y
   c= cols of x
   out is the output vector (c elements) . Memory for out is not stored.
 */
{
    int i, h;

    for (i = 0; i < c; i++) {
        out[i] = .0;
        for (h = 0; h < rr; h++)
            out[i] += x[h][i] * y[h];
    }
}

void transpose_double_matrix(double **x, int n)

/*
   transpose, and overwrite, the input matrix x
   of dimension n x n
 */
{
    double **trans;
    int i, j;

    trans = (double **)G_calloc(n, sizeof(double *));
    for (i = 0; i < n; i++)
        trans[i] = (double *)G_calloc(n, sizeof(double));
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            trans[j][i] = x[i][j];
    for (i = 0; i < n; i++)
        for (j = 0; j < n; j++)
            x[i][j] = trans[i][j];

    for (i = 0; i < n; i++)
        G_free(trans[i]);
    G_free(trans);
}

void double_matrix_to_vector(double **mat, int rows, int cols, double *vect)

/*
   transform matrix mat of dimension rows x cols in vector
   vect of length rows x cols.
   matrix is scanned by row
 */
{
    int i, j;

    for (i = 0; i < rows; i++)
        for (j = 0; j < cols; j++)
            vect[(i * cols) + j] = mat[i][j];
}

void extract_portion_of_double_matrix(int r, int c, int br, int bc,
                                      double **mat, double **wind)

/*
   extract a squared portion of a matrix mat
   given a the indeces of the center [r,c]
   and the semilength of the borders [br,bc]
   Output to array wind
 */
{
    int i, j;

    for (i = 0; i < 2 * br + 1; i++) {
        for (j = 0; j < 2 * bc + 1; j++) {
            wind[i][j] = mat[r - br + i][c - bc + j];
        }
    }
}

void transpose_double_matrix_rectangular(double **x, int n, int m,
                                         double ***trans)

/*
   transpose the input matrix x  of dimension n x m
   output to pointer to matrix trans
 */
{
    int i, j;

    (*trans) = (double **)G_calloc(m, sizeof(double *));
    for (i = 0; i < m; i++)
        (*trans)[i] = (double *)G_calloc(n, sizeof(double));

    for (i = 0; i < m; i++)
        for (j = 0; j < n; j++)
            (*trans)[i][j] = x[j][i];
}
