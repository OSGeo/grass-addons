#include <grass/config.h>
#include <stdio.h>
#include <grass/blas.h>
#include <grass/lapack.h>
typedef struct VEC_
{
    int dim, max_dim;
    double *ve;
} VEC;

int G_matrix_read2(FILE * fp, mat_struct * out);
void G_matrix_print2(mat_struct * mt, const char *name);
vec_struct *G_matvect_get_column2(mat_struct * mt, int col);
vec_struct *G_vector_product(vec_struct *, vec_struct *);

VEC *G_vec_get(int size);
VEC *G_vec_get2(int size, VEC * vector);
void G_vec_print(VEC * vector, const char *name);
VEC *G_vec_resize(VEC * in, int size);

VEC *v_sub(VEC * vec1, VEC * vec2, VEC * out);
VEC *mv_mlt(mat_struct * A, VEC * b, VEC * out);
mat_struct *sm_mlt(double scalar, mat_struct * matrix, mat_struct * out);
mat_struct *G_matrix_resize(mat_struct * in, int rows, int cols);
double v_norm2(VEC * x);
VEC *G_vec_copy(VEC * in);
int vec_free(VEC *vec);
