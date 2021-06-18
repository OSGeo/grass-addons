
/****************************************************************************
 *
 * MODULE:       i.spec.unmix
 *
 * AUTHOR(S):    Markus Neteler  <neteler osgeo.org>: Original GRASS 5 version
 *               Mohammed Rashad <rashadkm gmail.com> (update to GRASS 6)
 *
 * PURPOSE:      Spectral mixture analysis of satellite/aerial images
 * 
 * Notes:        The original version was implemented with MESCHACH, the actual
 *               version is instead using BLAS/LAPACK via GMATHLIB.
 *               An error minimization approach is used instead of Single Value
 *               Decomposition (SVD) which is numerically unstable. See the
 *               related journal publication from 2005 for details.
 *
 * COPYRIGHT:    (C) 1999-2012 by the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 *
 * TODO:         test with synthetic mixed pixels; speed up code
 *****************************************************************************/

#define GLOBAL

#include <grass/config.h>


#ifndef HAVE_LIBBLAS
#error GRASS is not configured with BLAS
#endif

#ifndef HAVE_LIBLAPACK
#error GRASS is not configured with LAPACK
#endif

#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "global.h"

#include "open.h"
#include "la_extra.h"


#define GAMMA 10		/* last row value in Matrix and last b vector element
				 * for constraint Sum xi = 1 (GAMMA=weight) */


static double find_max(double x, double y)
{
    return ((x * (x > y)) + (y * (x <= y)));
}


int main(int argc, char *argv[])
{
    char result_name[80];
    int nrows, ncols;
    int row;
    int i, j, k;
    VEC *b, *b_gamma;
    VEC *startvector, *A_times_startvector, *errorvector, *temp;
    mat_struct *A, *A_tilde, *A_tilde_trans_mu, *A_tilde_trans;

    mat_struct B, B_tilde, B_tilde_trans_mu;

    struct GModule *module;

    double max_total = 0.0;
    double mu;
    float anglefield[255][255];
    double error = 0.0;
    struct
    {
	struct Option *group, *matrixfile, *result, *error, *iter;
    } parm;

    /* initialize GIS engine */
    G_gisinit(argv[0]);
    module = G_define_module();

    module->keywords = _("imagery, spectral unmixing");
    module->description =
	_("Performs Spectral mixture analysis of satellite/aerial images");

    parm.group = G_define_standard_option(G_OPT_I_GROUP);

    parm.matrixfile = G_define_standard_option(G_OPT_F_INPUT);
    parm.matrixfile->key = "matrix";
    parm.matrixfile->type = TYPE_STRING;
    parm.matrixfile->required = YES;
    parm.matrixfile->label = _("Open Matrix file");
    parm.matrixfile->description =
	_("Matrix file containing spectral signatures");

    parm.result = G_define_option();
    parm.result->key = "result";
    parm.result->description =
	_("Name of raster map prefix to hold spectral unmixing results");
    parm.result->guisection = _("Required");

    parm.error = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.error->key = "error";
    parm.error->description = _("Name of raster map to hold unmixing error");

    parm.iter = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.iter->key = "iter";
    parm.iter->description = _("Name of raster map to hold number of iterations");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    /* here we go... A is created here */
    A = open_files2(parm.matrixfile->answer,
		    parm.group->answer,
		    parm.result->answer,
		    parm.iter->answer, parm.error->answer);
             

    /* ATTENTION: Internally we work here with col-oriented matrixfile,
     *  but the user has to enter the spectra row-wise for his/her's
     *  convenience...  That means: Don't mix row- and col-orientation
     *  in source code and modules messages output!
     *
     * Spectral Matrix is stored in A now (diagonally flipped to input
     * file) Generally:    n: cols ....  for matrix A
     *             m: rows
     *                 |
     *                 |
     */

    /* 1. Check matrix orthogonality: 
     *    Ref: Youngsinn Sohn, Roger M. McCoy 1997: Mapping desert shrub
     *    rangeland using spectral unmixing and modeling spectral
     *    mixtrues with TM data. Photogrammetric Engineering &
     *    Remote Sensing,  Vol.63,  No6.
     *
     *
     * 2. Beside checking matrix orthogonality we find out the maximum
     *    entry of the matrix for configuring stepsize mu later.  
     */

    /* go columnwise through matrix */


    for (i = 0; i < A->cols; i++) {
	vec_struct *Avector1, *Avector2;
	double max1, max2;

	Avector1 = G_matvect_get_column2(A, i);


	/* get the max. element of this vector */
	max1 = G_vector_norm_maxval(Avector1, 1);

	double temp = max1;

	for (j = 0; j < A->cols; j++) {
	    if (j != i) {
		/* get next col in A */
		Avector2 = G_matvect_get_column(A, j);

		/*  get the max. element of this vector */
		max2 = G_vector_norm_maxval(Avector2, 1);

		if (max2 > max1)
		    temp = max2;

		/* find max of matrix A */

		if (temp > max_total)
		    max_total = temp;

		/* G_warning("max_total: %lf", max_total); */
		/* save angle in degree */
		anglefield[i][j] = spectral_angle(Avector1, Avector2);
		/* G_warning("anglefield[i][j]: %lf", anglefield[i][j]); */

	    }
	}

	G_vector_free(Avector1);
	G_vector_free(Avector2);
    }

    G_message(_("Checking linear dependencies (orthogonality check) of Matrix A..."));

    for (i = 0; i < A->cols; i++)
	for (j = 0; j < A->cols; j++)
	    if (j != i)
		// internally this is col and not row certainly 
		G_message(_("Angle between row %i and row %i: %g degree"),
			  (i + 1), (j + 1), anglefield[i][j]);

    for (i = 0; i < A->cols; i++)
	for (j = 0; j < A->cols; j++)
	    if (j != i)
		if (anglefield[i][j] < 8.0)
		    G_fatal_error(_("Spectral entries row %i: and row %i: in "
				    "your matrix are linear dependent!\nYou "
				    "have to revise your reference spectra."),
				  i, j);

    if (!error)
	G_message(_("Spectral matrix is o.k. Proceeding..."));

  /* Begin calculations 
   * 1. contraint SUM xi = 1
   *   add last row "1" elements to Matrix A, store in A_tilde
   *   A_tilde is one row-dimension more than A 
   */


    /* memory allocation */
    A_tilde = G_matrix_init(A->rows + 1, A->cols, A->rows + 1);
    if (A_tilde == NULL)
    {
	    G_fatal_error(_("Unable to allocate memory for matrix"));
	    exit(1);
	  }  

    for (i = 0; i < A->rows; i++)
	for (j = 0; j < A->cols; j++)
	    G_matrix_set_element(A_tilde, i, j,
				 G_matrix_get_element(A, i, j));

    /* fill last row with 1 elements  */

    for (j = 0; j < A_tilde->cols; j++) {

	G_matrix_set_element(A_tilde, i, j, GAMMA);
    }
    /* G_matrix_print2(A_tilde, "A_tilde"); */


    /* now we have an overdetermined (non-square) system 

    * We have a least square problem here: error minimization
    *                             T          -1         T
    * unknown fraction = [A_tilde * A_tilde]  * A_tilde * b
    *
    * A_tilde is the non-square matrix with first constraint in last row.
    * b is pixel vector from satellite image
    *
    * Solve this by deriving above equation and searching the
    * minimum of this error function in an iterative loop within
    * both constraints.
    */

    /* calculate the transpose of A_tilde */

    A_tilde_trans = G_matrix_transpose(A_tilde);

    /* initialize some values

    *  step size must be small enough for covergence  of iteration:
    *  mu = 0.000001;      step size for spectra in range of W/m^2/um
    *  mu = 0.000000001;   step size for spectra in range of mW/m^2/um
    *  mu = 0.000001;      step size for spectra in range of reflectance   
    *  check  max_total for number of digits to configure mu size
    */
    mu = 0.0001 * pow(10, -1 * ceil(log10(max_total)));
    /*G_message("mu = %lf", mu); */

    // Missing? startvector = G_vector_init (0, 0, RVEC); 
    startvector = G_vec_get2(A->cols, startvector);



    if (startvector == NULL)
    {
	    G_fatal_error(_("Unable to allocate memory for vector"));
	    exit(1);
	  }  


    // Missing? A_times_startvector = G_vector_init (0, 0, RVEC);
    A_times_startvector = G_vec_get2(A_tilde->rows, A_times_startvector);	/* length: no. of bands   */
    // Missing? errorvector = G_vector_init (0, 0, RVEC);
    errorvector = G_vec_get2(A_tilde->rows, errorvector);	/* length: no. of bands   */
    // Missing? temp = G_vector_init (0, 0, RVEC);
    temp = G_vec_get2(A_tilde->cols, temp);	/* length: no. of spectra */
    /*  A_tilde_trans_mu = m_get(A_tilde->m,A_tilde->n); */

    /* length: no. of bands   */

    if (A_times_startvector == NULL)
	G_fatal_error(_("Unable to allocate memory for vector"));

    /* length: no. of bands   */

    if (errorvector == NULL)
	G_fatal_error(_("Unable to allocate memory for vector"));

    /* length: no. of spectra */

    if (temp == NULL)
	G_fatal_error(_("Unable to allocate memory for vector"));

    A_tilde_trans_mu =
	G_matrix_init(A_tilde->rows, A_tilde->cols, A_tilde->rows);
    if (A_tilde_trans_mu == NULL)
	G_fatal_error(_("Unable to allocate memory for matrix"));

    /* Now we can calculated the fractions pixelwise */
    nrows = G_window_rows();	/* get geographical region  */
    ncols = G_window_cols();

    G_message(_("Calculating for %i x %i pixels (%i bands) = %i pixelvectors."),
	      nrows, ncols, Ref.nfiles, (ncols * ncols));

    for (row = 0; row < nrows; row++) {
	int col, band;

	G_percent(row, nrows, 1);

	/* get one row for all bands */
	for (band = 0; band < Ref.nfiles; band++)
	    if (G_get_map_row(cellfd[band], cell[band], row) < 0)
		G_fatal_error(_("Unable to get map row [%d]"), row);

	/* for (band = 0; band < Ref.nfiles; band++)                
	* {
	*  if (G_get_map_row (cellfd[band], cell[band], row) < 0)
	*  G_fatal_error (_("Unable to get map row [%d]"), row);
	*/
	for (col = 0; col < ncols; col++) {

	    double change = 1000;
	    double deviation = 1000;
	    int iterations = 0;

	    /* get pixel values of each band and store in b vector: */
	    /* length: no. of bands + 1 (GAMMA) */

	    b_gamma = G_vec_get2(A_tilde->rows, b_gamma);

	    /* b_gamma = G_vector_init (A_tilde->rows, 1, RVEC); */
	    if (b_gamma == NULL)
		G_fatal_error(_("Unable to allocate memory for matrix"));

	    /* G_message("%d", A_tilde->rows);   */
	    for (band = 0; band < Ref.nfiles; band++) {
		b_gamma->ve[band] = cell[band][col];

		/*G_matrix_set_element (b_gamma, 0, band, cell[band][col]); */
	    }

	    /* add GAMMA for 1. constraint as last element */
	    b_gamma->ve[Ref.nfiles] = GAMMA;
	    /* G_matrix_set_element (b_gamma, 0, Ref.nfiles, GAMMA); */


	    for (k = 0; k < A_tilde->cols; k++)
		startvector->ve[k] = (1.0 / A_tilde->cols);
	    /* G_matrix_set_element (startvector, k,0, (1.0 / A_tilde->cols)); */
	    /* G_matrix_print(startvector,"startvector1");  */

	    /* calculate fraction vector for current pixel
	    * Result is stored in fractions vector       
	    * with second constraint: Sum x_i = 1

	    * get start vector and initialize it with equal fractions:
	    * using the neighbor pixelvector as startvector 
	    */


	    /* solve with iterative solution: */
	    while (fabs(change) > 0.0001) {



		A_times_startvector = mv_mlt(A_tilde, startvector, A_times_startvector);


		errorvector = v_sub(A_times_startvector, b_gamma, errorvector);


		A_tilde_trans_mu =  sm_mlt(mu, A_tilde_trans, A_tilde_trans_mu);


		temp = mv_mlt(A_tilde_trans_mu, errorvector, temp);
		startvector = v_sub(startvector, temp, startvector);	/* update startvector */

		/* if one element gets negative, set it to zero */
		for (k = 0; k < (A_tilde->cols); k++)	/* no. of spectra times */
		    if (startvector->ve[k] < 0)
			startvector->ve[k] = 0;

		/* Check the deviation */
		double norm2 = v_norm2(errorvector);

		change = deviation - norm2;
		deviation = norm2;

		iterations++;

      /* G_debug (5, "Change: %g - deviation: %g",   change, deviation); */

	  }

	    /*----------  end of second contraint -----------------------
	    * store fractions in resulting rows of resulting files
	    * (number of bands = vector dimension) 
	    */


	    VEC *fraction;

	    fraction = G_vec_get(A->cols);	/* length: no. of spectra */
	    error = deviation / v_norm2(b_gamma);
	    fraction = G_vec_copy(startvector);

	    /* write result in full percent */
	    for (i = 0; i < A->cols; i++)	/* no. of spectra */
		result_cell[i][col] = (CELL) (100 * fraction->ve[i]);

	    /* save error and iterations */
	    error_cell[col] = (CELL) (100 * error);
	    iter_cell[col] = iterations;
	    
	    
	    vec_free(fraction);


	} /* end cols loop */


	/* write the resulting rows into output files: */
	for (i = 0; i < A->cols; i++)	/* no. of spectra */
	    G_put_map_row(resultfd[i], result_cell[i]);

	if (error_fd > 0)
	    G_put_map_row(error_fd, error_cell);

	if (iter_fd > 0)
	    G_put_map_row(iter_fd, iter_cell);

    }		/* end rows loop */
    G_percent(row, nrows, 2);

    /* close files */
    for (i = 0; i < Ref.nfiles; i++)	/* no. of bands */
	G_unopen_cell(cellfd[i]);

    for (i = 0; i < A->cols; i++)	/* no. of spectra */
    {
	char command[1080];

	G_close_cell(resultfd[i]);

	/* make grey scale color table */
	sprintf(result_name, "%s.%d", parm.result->answer, (i + 1));
	sprintf(command, "r.colors map=%s color=rules <<EOF\n"
		"0 0 0 0 \n" "201 0 255 0\n" "end\n" "EOF", result_name);

	/* G_system (command); */
	
	
    vec_free(startvector);

    vec_free(A_times_startvector);

	/* create histogram */
	do_histogram(result_name, Ref.file[i].mapset);
    }

    if (error_fd > 0) {
	char command[80];

	G_close_cell(error_fd);
    /* TODO
	sprintf(command, "r.colors map=%s color=gyr >/dev/null",
		parm.error->answer);
	G_system (command);
    */
    }

    if (iter_fd > 0)
	G_close_cell(iter_fd);

    G_matrix_free(A);
   
    vec_free(errorvector);

    vec_free(temp);
    
    vec_free(b_gamma);

    make_history(result_name, parm.group->answer, parm.matrixfile->answer);

    exit(EXIT_SUCCESS);
}
