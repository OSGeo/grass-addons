/* Spectral mixture analysis of satellite/aerial images
 * (c) 1999-2000 Markus Neteler, Hannover, Germany
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team, Markus Neteler
 *               neteler cealp.it
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 * VERSION: Based on LAPACK/BLAS
 *
 * Module calculates
 *          -1
 *      x =A   b
 *
 *  A: matrix of reference spectra (endmembers)
 *  b: pixel vector from satellite image
 *  x: unknown fraction vector
 *
 * with two constraints:
 *    1. SUM x_i = 1     (max. 100%)              -> least square problem
 *    2. 0 <= x_i <= 1   (no negative fractions)  -> Steepest Descend of
 *                                                      error surface
 *
 *
 * IMPORTANT: Physical units of matrix file and image data set must fit
 *            otherwise the algorithm might run into endless loop!
 *
 * TODO: complete LAPACK/BLAS port. Check with Brad Douglas.
 ********************************************************************/
             
#define GLOBAL
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/la.h>
#include "global.h"

#define GAMMA 10   /* last row value in Matrix and last b vector element */
                   /* for constraint Sum xi = 1 (GAMMA=weight) */

int open_files();
void spectral_angle();

double find_max(double x, double y) 
{
 return((x*(x>y))+(y*(x<=y)));
}


CELL myround (x)
  double x;
  {
    CELL n;
    
    if (x >= 0.0)
        n = x + .5;
    else
       {
        n = -x + .5;
        n = -n;
       }
    return n;
  }


int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    int band;
    int i, j, k, iterations;
    mat_struct *A_tilde;
    vec_struct *b_gamma;
    vec_struct *startvector, *A_times_startvector, *errorvector, *temp;
    mat_struct *A_tilde_trans_mu;
    int *index;
    double max1, max2, max_total=0.0;
    double change, mu, deviation;
    float anglefield[255][255];
    double error;
    char command[80];
    struct
    {
	struct Option *group, *matrixfile, *result, *error, *iter;
    } parm;

    G_gisinit (argv[0]);

    parm.group = G_define_option();
    parm.group->key = "group";
    parm.group->type = TYPE_STRING;
    parm.group->required = YES;
    parm.group->description = "Imagery group to be analyzed with Spectral Mixture Analyis";

    parm.matrixfile = G_define_option();
    parm.matrixfile->key = "matrixfile";
    parm.matrixfile->type = TYPE_STRING;
    parm.matrixfile->required = YES;
    parm.matrixfile->description = "Matrix file containing spectral signatures ";

    parm.result = G_define_option();
    parm.result->key = "result";
    parm.result->type = TYPE_STRING;
    parm.result->required = YES;
    parm.result->description = "Raster map prefix to hold spectral unmixing results";

    parm.error = G_define_option();
    parm.error->key = "error";
    parm.error->type = TYPE_STRING;
    parm.error->required = YES;
    parm.error->description = "Raster map to hold unmixing error";

 
    parm.iter = G_define_option();
    parm.iter->key = "iter";
    parm.iter->type = TYPE_STRING;
    parm.iter->required = YES;
    parm.iter->description = "Raster map to hold number of iterations";

    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = "Run quietly (but with percentage output)";

    flag2.veryquiet = G_define_flag();
    flag2.veryquiet->key = 's';
    flag2.veryquiet->description = "Run silently (say nothing)";

    if (G_parser(argc,argv))
	exit(EXIT_FAILURE);

    result_prefix = parm.result->answer;
    error_name   = parm.error->answer;
    iter_name    = parm.iter->answer;
    group        = parm.group->answer;
    matrixfile   = parm.matrixfile->answer;
    if (flag2.veryquiet->answer)
    	flag.quiet->answer = 1;

/* here we go... */

    open_files(); /*A is created here */

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
   **/

  /* 1. Check matrix orthogonality: 
   *    Ref: Youngsinn Sohn, Roger M. McCoy 1997: Mapping desert shrub
   *    rangeland using spectral unmixing and modeling spectral
   *    mixtrues with TM data. Photogrammetric Engineering &
   *    Remote Sensing,  Vol.63,  No6.
   *
   *
   * 2. Beside checking matrix orthogonality we find out the maximum
   *    entry of the matrix for configuring stepsize mu later.  */
     
    for (i = 0; i < A->cols; i++) /* go columnwise through matrix*/
    {
     Avector1 = G_matvect_get_column(A, i);
     max1 = G_vector_norm_maxval(Avector1, index); /* get the max. element of this vector */
     for (j = 0; j < A->cols ; j++)
	{
	 if (j !=i)
	    {
	     Avector2 = G_matvect_get_column(A, j);  /* get next col in A */
	     max2 = G_vector_norm_maxval(Avector2, index); /* get the max. element of this vector */
	     max_total=(find_max(max1,max2),max_total); /* find max of matrix A */

	     spectral_angle();                 /* check vector angle */
	     anglefield[i][j]= curr_angle;     /* save angle in degree */
	     G_vector_free(Avector2);
	    }
	}
     G_vector_free(Avector1);
     G_vector_free(Avector2);
    }

    /* print out the result */
    if (!flag.quiet->answer)
    	{
         fprintf(stderr,"Checking linear dependencies (orthogonality check) of Matrix A:\n");
         for (i = 0; i < A->cols ; i++)
            for (j = 0; j < A->cols ; j++)
	    {
             if (j !=i)
              fprintf(stderr,"  Angle between row %i and row %i: %g degree\n", \
                                         (i+1), (j+1), anglefield[i][j]);
                               /* internally this is col and not row certainly */
            }
         fprintf(stderr,"\n");
        }
   /* check it */
   error=0;
   for (i = 0; i < A->cols ; i++)
     for (j = 0; j < A->cols ; j++)
       if (j !=i)
         if (anglefield[i][j] < 8.0)
         {
	     fprintf(stderr,"ERROR: Spectral entries row%i: and row%i: in your matrix \
                                    are linear dependent!\n",i,j);
	     fprintf(stderr,"       You have to revise your reference spectra.\n");
	     error=1;
	     exit(EXIT_FAILURE);
	 }

   if (!error)
     if (!flag.quiet->answer)
	 fprintf(stderr,"Spectral matrix is o.k. Proceeding...\n\n");


/* Begin calculations */
   /* 1. contraint SUM xi = 1
    *   add last row "1" elements to Matrix A, store in A_tilde
    *   A_tilde is one row-dimension more than A */
   A_tilde = m_get(A->rows+1, A->cols);  /* memory allocation */

   for (i=0; i < A->rows ; i++)   /* copy rowwise */
     for (j=0; j < A->cols; j++)  /* copy colwise */
          G_matrix_get_element(A_tilde, i, j)= A->G_matrix_get_element[i][j];

   /* fill last row with 1 elements */
   for (j=0; j < A->cols ; j++)
      G_matrix_get_element(A_tilde, [A->rows][j])= GAMMA;
   /* now we have an overdetermined (non-square) system */


/* We have a least square problem here: error minimization
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

   /* calculate the transpose of A_tilde*/
    A_tilde_trans = G_matrix_transpose(A_tilde);

/* initialize some values */
  /* step size must be small enough for covergence  of iteration:
   *  mu=0.000001;      step size for spectra in range of W/m^2/um
   *  mu=0.000000001;   step size for spectra in range of mW/m^2/um
   *  mu=0.000001;      step size for spectra in range of reflectance   
   ***/
   /* check  max_total for number of digits to configure mu size*/
    mu=0.0001 * pow(10,-1*ceil(log10(max_total)));
    startvector = v_get(A->cols);                /* length: no. of spectra */
    A_times_startvector = v_get(A_tilde->m);  /* length: no. of bands   */
    errorvector = v_get(A_tilde->m);          /* length: no. of bands   */
    temp = v_get(A_tilde->n);                 /* length: no. of spectra */
    A_tilde_trans_mu = m_get(A_tilde->m,A_tilde->n);

/* Now we can calculated the fractions pixelwise */
    nrows = G_window_rows(); /* get geographical region */
    ncols = G_window_cols();
    
    if (!flag.quiet->answer)
    	{
	 fprintf (stderr, "Calculating for %i x %i pixels (%i bands) = %i pixelvectors:\n",\
	 		nrows,ncols, Ref.nfiles, (ncols * ncols));
	 fprintf (stderr, "%s ... ", G_program_name());
	}
    for (row = 0; row < nrows; row++)             /* rows loop in images */
    {
	if (!flag2.veryquiet->answer)
	    G_percent(row, nrows, 1);
	for (band = 0; band < Ref.nfiles; band++) /* get one row for all bands*/
	{
	 if (G_get_map_row (cellfd[band], cell[band], row) < 0)
		exit(EXIT_FAILURE);
	}

	for (col = 0; col < ncols; col++)
             /* cols loop, work pixelwise for all bands */
	{

	    /* get pixel values of each band and store in b vector: */
	     b_gamma = v_get(A_tilde->m);              /* length: no. of bands + 1 (GAMMA)*/
	     for (band = 0; band < Ref.nfiles; band++)
		  b_gamma->ve[band] = cell[band][col];  
            /* add GAMMA for 1. constraint as last element*/
	     b_gamma->ve[Ref.nfiles] = GAMMA;    

            /* calculate fraction vector for current pixel
             * Result is stored in fractions vector       
	     * with second constraint: Sum x_i = 1 */

	     change=1000;  /* initialize */
	     deviation=1000;
             iterations = 0;
             for (k = 0; k < (A_tilde->n); k++)  /* no. of spectra times */
                  startvector->ve[k] = (1./A_tilde->n);

	    /* get start vector and initialize it with equal fractions:
	     * using the neighbor pixelvector as startvector*/

	      /* solve with iterative solution: */
	     while( fabs(change) > 0.0001 )
		{
		 /* go a small step into direction of negative gradient
                  * errorvector = A_tilde * startvector - b_gamma */
		 mv_mlt(A_tilde, startvector, A_times_startvector);
		 v_sub(A_times_startvector, b_gamma, errorvector);
                 sm_mlt(mu, A_tilde_trans, A_tilde_trans_mu);
                 mv_mlt(A_tilde_trans_mu, errorvector, temp);
                 v_sub(startvector,temp,startvector); /* update startvector */

                 /* if one element gets negative, set it to zero */
                 for (k = 0; k < (A_tilde->n); k++)  /* no. of spectra times */
                   if (startvector->ve[k] < 0)
                        startvector->ve[k] = 0;

                 /* Check the deviation */
                 change = deviation - G_vector_norm_euclid(errorvector);
                 deviation = G_vector_norm_euclid(errorvector);

		 /* debug output */
		 /*fprintf(stderr, "Change: %g - deviation: %g\n", \
		  *change, deviation); */

                 iterations++;
	        } /* while */

	     fraction=v_get(A->cols);     /* length: no. of spectra */
             error = deviation / G_vector_norm_euclid(b_gamma);
             v_copy(startvector, fraction);

            /*----------  end of second contraint -----------------------*/
            /* store fractions in resulting rows of resulting files
             * (number of bands = vector dimension) */

	    /* write result in full percent */
	     for (i = 0; i < A->cols; i++)  /* no. of spectra */
		  result_cell[i][col] = (CELL)(100 * fraction->ve[i]); 
  


	    /* save error and iterations*/
             error_cell[col] = (CELL) (100 * error);
             iter_cell[col] = iterations;

	     G_vector_free(fraction);
	     G_vector_free(b);	     
	   } /* columns loop */

	  /* write the resulting rows into output files: */
	  for (i = 0; i < A->cols; i++)   /* no. of spectra */
	      G_put_map_row (resultfd[i], result_cell[i]);
	  if (error_fd > 0)
	      G_put_map_row (error_fd, error_cell);
	  if (iter_fd > 0)
	      G_put_map_row (iter_fd, iter_cell);

	} /* rows loop */

    if (!flag2.veryquiet->answer)
	G_percent(row, nrows, 2);
	
  /* close files */
    for (i = 0; i < Ref.nfiles; i++)   /* no. of bands */
  	  G_unopen_cell(cellfd[i]);
  	  
    for (i = 0; i < A->cols; i++)   /* no. of spectra */
    	{
	  G_close_cell (resultfd[i]);
	  /* make grey scale color table */
	  sprintf(result_name, "%s.%d", result_prefix, (i+1));	               
          sprintf(command, "r.colors map=%s color=rules 2>&1> /dev/null <<EOF\n
			    0 0 0 0 \n
			    100 0 255 0\n
			    end\n
			    EOF", result_name);
          system(command);
         /* create histogram */
          do_histogram(result_name, Ref.file[i].mapset);
	}
    if (error_fd > 0)
    	{
	 G_close_cell (error_fd);
	 sprintf(command, "r.colors map=%s color=gyr >/dev/null", error_name);
	 system(command);
	}
    if (iter_fd > 0)
    	{
	 G_close_cell (iter_fd);
	/* sprintf(command, "r.colors map=%s color=gyr >/dev/null", iter_name);
	 system(command);*/
	}

    G_matrix_free(A);

    make_history(result_name, group, matrixfile);
    exit(EXIT_SUCCESS);
} /* main*/

