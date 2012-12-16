/* TODO: move to GMATHLIB */

#include <stdio.h>		/* needed here for ifdef/else */
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <grass/config.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/la.h>
#include "la_extra.h"


mat_struct *G_matrix_resize(mat_struct * in, int rows, int cols)
{
  mat_struct *matrix;
  matrix = G_matrix_init(rows, cols, rows);
  int i, j, p, index = 0;
  for (i = 0; i < rows; i++) 
  {
    for (j = 0; j < cols; j++)
    matrix->vals[index++] = in->vals[i + j * cols];
  }

  int old_size = in->rows * in->cols;
  int new_size = rows * cols;

  if (new_size > old_size)
    for (p = old_size; p < new_size; p++)
      matrix->vals[p] = 0.0;

  return (matrix);
}


mat_struct *G_matrix_scalar_mul(double scalar, mat_struct * matrix, mat_struct * out)
{
  int m, n, i, j;
  int index = 0;

  if (matrix == NULL)
	{
    G_warning (_("Input matrix is uninitialized"));
    return NULL;
  }      

  if (out == NULL)
	  out = G_matrix_init(matrix->rows, matrix->cols, matrix->rows);

  if (out->rows != matrix->rows || out->cols != matrix->cols)
	  out = G_matrix_resize(out, matrix->rows, matrix->cols);

  m = matrix->rows;
  n = matrix->cols;
  
  for (i = 0; i < m; i++) 
  {
  	for (j = 0; j < n; j++) 
  	{
  	  doublereal value = scalar * G_matrix_get_element(matrix, i, j);
	    G_matrix_set_element (out, i,j, value);
	  }
  }

  return (out);
}

vec_struct* G_mat_vector_product(mat_struct * A, vec_struct * b,vec_struct *out)
{
  unsigned int i, m, n, j;
  register doublereal sum;

  if (A->cols != b->ldim) {
    G_warning (_("Input matrix and vector have differing dimensions"));
    return NULL;
  }
  if (!out) {
    G_warning (_("Output vector is uninitialized"));
    return NULL;
  }
  if (out->ldim != A->rows) {
    G_warning (_("Output vector has incorrect dimension"));
    return NULL;
  }


  m = A->rows;
  n = A->cols;

  for (i = 0; i < m; i++) {
    sum = 0.0;
    int width = A->rows;
    for (j = 0; j < n; j++) {
	    sum += A->vals[i + j * width] * b->vals[j];
	    out->vals[i] = sum;
	  }
  }
  return (out);
}



vec_struct *
G_vector_product (vec_struct *v1, vec_struct *v2, vec_struct *out)
{
    int idx1, idx2, idx0;
    int i;

    if (!out->is_init) {
        G_warning (_("Output vector is uninitialized"));
        return NULL;
    }

    if (v1->type != v2->type) {
        G_warning (_("Vectors are not of the same type"));
        return NULL;
    }

    if (v1->type != out->type) {
        G_warning (_("Output vector is of incorrect type"));
        return NULL;
    }

    if (v1->type == MATRIX_) {
        G_warning (_("Matrices not allowed"));
        return NULL;
    }

    if ((v1->type == ROWVEC_ && v1->cols != v2->cols) ||
        (v1->type == COLVEC_ && v1->rows != v2->rows))
    {
        G_warning (_("Vectors have differing dimensions"));
        return NULL;
    }

    if ((v1->type == ROWVEC_ && v1->cols != out->cols) ||
        (v1->type == COLVEC_ && v1->rows != out->rows))
    {
        G_warning (_("Output vector has incorrect dimension"));
        return NULL;
    }

#if defined(HAVE_LAPACK) && defined(HAVE_LIBBLAS)
    f77_dhad (v1->cols, 1.0, v1->vals, 1, v2->vals, 1, 0.0, out->vals, 1.0);
#else
    idx1 = (v1->v_indx > 0) ? v1->v_indx : 0;
    idx2 = (v2->v_indx > 0) ? v2->v_indx : 0;
    idx0 = (out->v_indx > 0) ? out->v_indx : 0;

    if (v1->type == ROWVEC_) {
        for (i = 0; i < v1->cols; i++)
            G_matrix_set_element(out, idx0, i,
			   G_matrix_get_element(v1, idx1, i) *
			   G_matrix_get_element(v2, idx2, i));
    } else {
        for (i = 0; i < v1->rows; i++)
            G_matrix_set_element(out, i, idx0,
			   G_matrix_get_element(v1, i, idx1) *
			   G_matrix_get_element(v2, i, idx2));
    }
#endif

    return out;
}



