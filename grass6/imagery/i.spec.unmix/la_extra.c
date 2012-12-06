/* TODO: move to GMATHLIB? */

#include <stdio.h>		/* needed here for ifdef/else */
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include <grass/config.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/la.h>
#include "la_extra.h"


vec_struct *G_matvect_get_column2(mat_struct * mt, int col)
{
    int i;			/* loop */
    vec_struct *vc1;

    if (col < 0 || col >= mt->cols) {
	G_warning(_("Specified matrix column index is outside range"));
	return NULL;
    }

    if (!mt->is_init) {
	G_warning(_("Matrix is not initialised"));
	return NULL;
    }

    if ((vc1 = G_vector_init(mt->rows, mt->ldim, CVEC)) == NULL) {
	G_warning(_("Could not allocate space for vector structure"));
	return NULL;
    }

    for (i = 0; i < mt->rows; i++) {
	double dd = G_matrix_get_element(mt, i, col);


	G_matrix_set_element((mat_struct *) vc1, i, 0, dd);

    }

    return vc1;
}


void G_matrix_print2(mat_struct * mt, const char *name)
{
    int i, j;


    if (mt != NULL) {
	G_message("start matrix(%s)", name);
	G_message("Size: %d x %d", mt->rows, mt->cols);

	for (i = 0; i < mt->rows; i++) {
	    char buf[2048], numbuf[640];

	    sprintf(buf, "row%d: ", i);
	    for (j = 0; j < mt->cols; j++) {

		double element = G_matrix_get_element(mt, i, j);

		sprintf(numbuf, "%14.6f", element);
		strcat(buf, numbuf);

	    }
	    G_message("%s", buf);
	}

	G_message("end matrix(%s)", name);
    }

}


mat_struct *G_matrix_resize(mat_struct * in, int rows, int cols)
{

    mat_struct *matrix;


    matrix = G_matrix_init(rows, cols, rows);


    int i, j, p, index = 0;

    for (i = 0; i < rows; i++) {




	for (j = 0; j < cols; j++) {

	    matrix->vals[index++] = in->vals[i + j * cols];

	}

    }

    int old_size = in->rows * in->cols;

    int new_size = rows * cols;

    if (new_size > old_size)
	for (p = old_size; p < new_size; p++)
	    matrix->vals[p] = 0.0;


    return matrix;
}



mat_struct *sm_mlt(double scalar, mat_struct * matrix, mat_struct * out)
{
    int m, n, i, j;

    int index = 0;

    if (matrix == NULL)
	G_fatal_error("sm_mlt1(error)");

    if (out == NULL)
	out = G_matrix_init(matrix->rows, matrix->cols, matrix->rows);

    if (out->rows != matrix->rows || out->cols != matrix->cols)
	out = G_matrix_resize(out, matrix->rows, matrix->cols);

    m = matrix->rows;
    n = matrix->cols;
    for (i = 0; i < m; i++) {
	/* __smlt__(matrix->me[i],(double)scalar,out->me[i],(int)n); */

		/**************************************************/
	for (j = 0; j < n; j++) {
	    out->vals[index++] = scalar * matrix->vals[i + j * m];
	}
    }

		/**************************************************/
    return (out);
}

VEC *G_vec_copy(VEC * in)
{
    int i;
    VEC *out;

    if (!in)
	G_fatal_error("v_copy(error1)");

    int dim = in->dim;

    out = G_vec_get(dim);


    for (i = 0; i < dim; i++) {
	out->ve[i] = in->ve[i];
    }

    return (out);
}


double v_norm2(VEC * x)
{
    int i, dim;
    double s, sum;

    if (!x)
	G_fatal_error("v_norm2(error1)");


    dim = x->dim;

    sum = 0.0;

    for (i = 0; i < dim; i++) {
	sum += x->ve[i] * x->ve[i];
    }



    return sqrt(sum);
}



VEC *v_sub(VEC * vec1, VEC * vec2, VEC * out)
{
    /* u_int        i, dim; */
    /* Real *out_ve, *vec1_ve, *vec2_ve; */

    if (!vec1 || !vec2)
	G_fatal_error("v_sub1(error)");

    if (vec1->dim != vec2->dim)
	G_fatal_error("v_sub2(error)");

    if (out == NULL)
	out = G_vec_get(vec1->dim);




    if (out->dim != vec1->dim)
	out = G_vec_resize(out, vec1->dim);

    int i;

    for (i = 0; i < vec1->dim; i++)
	out->ve[i] = vec1->ve[i] - vec2->ve[i];

	/************************************************************
	dim = vec1->dim;
	out_ve = out->ve;	vec1_ve = vec1->ve;	vec2_ve = vec2->ve;
	for ( i=0; i<dim; i++ )
		out->ve[i] = vec1->ve[i]-vec2->ve[i];
		(*out_ve++) = (*vec1_ve++) - (*vec2_ve++);
	************************************************************/

    return (out);
}



VEC *mv_mlt(mat_struct * A, VEC * b, VEC * out)
{
    unsigned int i, m, n, j;
    double **A_v, *b_v /*, *A_row */ ;

    /* register Real        sum; */

    /*

          if ( A==(MAT *)NULL || b==(VEC *)NULL )
          error(E_NULL,"mv_mlt");
    */


    if (A->cols != b->dim)

	G_fatal_error("mv_mlt1(error)");


    if (b == out)
	G_fatal_error("mv_mlt2(error)");

    if (!out) {
	G_fatal_error("mv_mltsss3(error)");
	out = G_vec_get2(A->rows, out);
    }
    if (out->dim != A->rows) {
	G_fatal_error("mv_mlt3(error)");
	out = G_vec_resize(out, A->rows);
    }




    m = A->rows;
    n = A->cols;
    A_v = A->vals;
    b_v = b->ve;



    for (i = 0; i < m; i++) {
	double sum = 0.0;
	int width = A->rows;


	for (j = 0; j < n; j++) {

	    sum += A->vals[i + j * width] * b->ve[j];
	    out->ve[i] = sum;


	}
    }



    return out;
}


VEC *G_vec_resize(VEC * in, int size)
{

    VEC *vector;


    vector = (VEC *) G_malloc(sizeof(VEC));


    vector->ve = (double *)G_malloc(size * sizeof(double));
    int i, j;

    G_message(":%d", in->dim);
    for (i = 0; i < in->dim; i++) {

	vector->ve[i] = in->ve[i];
	G_message("ss:%lf", in->ve[i]);

    }

    if (size > in->dim)
	for (j = i; j < size; j++)
	    vector->ve[j] = 0.0;

    vector->dim = vector->max_dim = size;

    return vector;
}







VEC *G_vec_get(int size)
{

    VEC *vector;


    vector = (VEC *) G_malloc(sizeof(VEC));


    vector->ve = (double *)G_malloc(size * sizeof(double));
    int i;

    for (i = 0; i < size; i++) {

	vector->ve[i] = 0.0;


    }

    vector->dim = vector->max_dim = size;

    return vector;
}


VEC *G_vec_get2(int size, VEC * vector)
{




    vector = (VEC *) G_malloc(sizeof(VEC));


    vector->ve = (double *)G_malloc(size * sizeof(double));
    int i;

    for (i = 0; i < size; i++) {

	vector->ve[i] = 0.0;


    }

    vector->dim = vector->max_dim = size;

    return vector;
}


void G_vec_print(VEC * vector, const char *name)
{
    int i;


    if (vector != NULL) {
	G_message("start vector(%s)", name);


	for (i = 0; i < vector->dim; i++) {
	    char buf[2048], numbuf[640];

	    sprintf(buf, "%lf ", vector->ve[i]);

	    G_message("%s", buf);
	}

	G_message("end vector(%s)", name);
    }

}




vec_struct *G_vector_product(vec_struct * v1, vec_struct * v2)
{
    int idx1, idx2, idx0;
    int i;


    vec_struct *out = G_vector_init(v1->rows, v1->ldim, CVEC);





    if (!out->is_init) {
	G_warning(_("Output vector is uninitialized"));
	return NULL;
    }

    if (v1->type != v2->type) {
	G_warning(_("Vectors are not of the same type"));
	return NULL;
    }

    if (v1->type != out->type) {
	G_warning(_("Output vector is of incorrect type"));
	return NULL;
    }

    if (v1->type == MATRIX_) {
	G_warning(_("Matrices not allowed"));
	return NULL;
    }

    if ((v1->type == ROWVEC_ && v1->cols != v2->cols) ||
	(v1->type == COLVEC_ && v1->rows != v2->rows)) {
	G_warning(_("Vectors have differing dimensions"));
	return NULL;
    }

    if ((v1->type == ROWVEC_ && v1->cols != out->cols) ||
	(v1->type == COLVEC_ && v1->rows != out->rows)) {
	G_warning(_("Output vector has incorrect dimension"));
	return NULL;
    }

#if defined(HAVE_LAPACK) && defined(HAVE_LIBBLAS)	/* && defined(HAVE_G2C_H) */
    f77_dhad(v1->cols, 1.0, v1->vals, 1, v2->vals, 1, 0.0, out->vals, 1.0);
#else
    idx1 = (v1->v_indx > 0) ? v1->v_indx : 0;
    idx2 = (v2->v_indx > 0) ? v2->v_indx : 0;
    idx0 = (out->v_indx > 0) ? out->v_indx : 0;

    if (v1->type == ROWVEC_) {
	for (i = 0; i < v1->cols; i++)
	    G_matrix_set_element(out, idx0, i,
				 G_matrix_get_element(v1, idx1, i) *
				 G_matrix_get_element(v2, idx2, i));
    }
    else {
	for (i = 0; i < v1->rows; i++)
	    G_matrix_set_element(out, i, idx0,
				 G_matrix_get_element(v1, i, idx1) *
				 G_matrix_get_element(v2, i, idx2));
    }
#endif

    return out;
}




int G_matrix_read2(FILE * fp, mat_struct * out)
{
    char buff[100];
    int rows, cols;
    int i, j, row;
    double val;

    /* skip comments */
    for (;;) {
	if (!G_getl(buff, sizeof(buff), fp))
	    return -1;
	if (buff[0] != '#')
	    break;
    }

    if (sscanf(buff, "Matrix: %d by %d", &rows, &cols) != 2) {
	G_warning(_("Input format error1"));
	return -1;
    }


    G_matrix_set(out, rows, cols, rows);



    for (i = 0; i < rows; i++) {
	if (fscanf(fp, "row%d:", &row) != 1) {
	    G_warning(_("Input format error"));
	    return -1;
	}

	for (j = 0; j < cols; j++) {
	    if (fscanf(fp, "%lf:", &val) != 1) {
		G_warning(_("Input format error"));
		return -1;
	    }

	    fgetc(fp);
	    G_matrix_set_element(out, i, j, val);
	}
    }

    return 0;
}

int vec_free(VEC *vec)
{
  if ( !vec || (vec->dim) < 0 )
    /* don't trust it */
    return -1;
   
	//G_free(vec->ve);

    G_free(vec);
      
  return 0;
}
