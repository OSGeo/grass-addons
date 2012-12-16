/* TODO: move to GMATHLIB */

#include <grass/config.h>
#include <stdio.h>
#include <grass/blas.h>
#include <grass/lapack.h>

mat_struct *G_matrix_scalar_mul(double scalar, mat_struct * matrix, mat_struct * out);
vec_struct* G_vector_product (vec_struct *v1, vec_struct *v2, vec_struct *out);
vec_struct* G_mat_vector_product(mat_struct * A, vec_struct * b,vec_struct *out);

