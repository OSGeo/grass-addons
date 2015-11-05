/* Spectral angle mapping
 * (c) 1998 Markus Neteler, Hannover, Germany
 *          neteler@geog.uni-hannover.de
 * 
 * Dependency to Meschach Lib removed in 2015
 *-------------------------------------------------------------------
 * V 0.1 - 26. Oct.1998
 *
 * * Based on Meschach Library (matrix operations)
 * * Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
 *
 * Cited references are from
 *   Steward, D.E, Leyk, Z. 1994: Meschach: Matrix computations in C.
 *      Proceedings of the centre for Mathematics and its Applicaions.
 *      The Australian National University. Vol. 32.
 *      ISBN 0 7315 1900 0
 *
 ********************************************************************/
             
#include <stdio.h>
#include <stdlib.h>
#include <strings.h>
#include <math.h>

#include <grass/config.h>
#ifndef HAVE_LIBBLAS
#error GRASS is not configured with BLAS
#endif
#ifndef HAVE_LIBLAPACK
#error GRASS is not configured with LAPACK
#endif

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "local_proto.h"
#include "global.h"

struct GModule *module;

vec_struct *b, *Avector;
int matrixsize;
float curr_angle;

struct Ref Ref;

CELL **cell;
int *cellfd;

CELL **result_cell;
int *resultfd;

CELL **error_cell;
int  error_fd;

char result_name[80];
char *result_prefix;

mat_struct  *open_files(char * matrixfile, char *img_grp);
void spectral_angle();
CELL myround(double x);

int main(int argc,char * argv[])
{
    int nrows, ncols;
    int row, col;
    int band;
    int i, j, error=0;
    vec_struct *svd_values; /*la.h defines vec_struct as a typedef mat_struct*/
    /*char command[80]; rm by Yann temporarily see grayscale palette*/
    float anglefield[255][255];
    struct
    {
	struct Option *group, *matrixfile, *output;
    } parm;

    mat_struct *A; /*first use in open.c G_matrix_set()*/
    char *group;

    G_gisinit (argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("spectral angle mapping"));
    module->description =
        _("Performs Spectral angle mapping on satellite/aerial images");


    parm.group = G_define_standard_option(G_OPT_I_GROUP);
    parm.group->description = "Imagery group to target for Spectral Mixture Analyis";

    parm.matrixfile = G_define_standard_option(G_OPT_F_INPUT);
    parm.matrixfile->description = "Matrix file containing spectral signatures";

    parm.output = G_define_option();
    parm.output->key = "result";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->description = "Raster map prefix to hold spectral angles";

    if (G_parser(argc,argv))
	G_fatal_error("Parsing arguments error");

    result_prefix = parm.output->answer;

    G_message("%s",result_prefix);

    /*Creating A, the spectral signature matrix here*/
    A = open_files(parm.matrixfile->answer, parm.group->answer);
   /* Spectral Matrix is stored in A now */

  /* Check matrix orthogonality 
   * Ref: Youngsinn Sohn, Roger M. McCoy 1997: Mapping desert shrub rangeland
   *          using spectral unmixing and modeling spectral mixtrues with 
   *          TM data. Photogrammetric Engineering & Remote Sensing, Vol.63, No6.
   */
     
    G_message("/* Check matrix orthogonality*/"); 
    for (i = 0; i < Ref.nfiles; i++) /* Ref.nfiles = matrixsize*/
    {
     Avector = G_matvect_get_row(A, i);  /* go columnwise through matrix*/
     for (j = 0; j < Ref.nfiles ; j++)
	{
	 if (j !=i)
	    {
	     b = G_matvect_get_row(A, j);      /* compare with next col in A */
	     spectral_angle();
	     anglefield[i][j]= curr_angle;
	     G_vector_free(b);
	    }
	}
     G_vector_free(Avector);
    }

    /* print out the result */
    G_message("Orthogonality check of Matrix A:\n");
    for (i = 0; i < Ref.nfiles ; i++)
      for (j = 0; j < Ref.nfiles ; j++)
	{
         if (j !=i)
         	G_message("  Angle between row %i and row %i: %g\n", (i+1), (j+1), anglefield[i][j]);
        }
    G_message("\n");
    
   /* check it */
   for (i = 0; i < Ref.nfiles ; i++)
     for (j = 0; j < Ref.nfiles ; j++)
       if (j !=i)
         if (anglefield[i][j] < 10.0)
         {
	     G_message("ERROR: Spectral entries row %i|%i in your matrix are linear dependent!\n",i,j);
	     error=1;
	 }

    if (!error)
	G_message("Spectral matrix is o.k. Proceeding...\n");
   
    /* check singular values of Matrix A
     * Ref: Boardman, J.W. 1989: Inversion of imaging spectrometry data
     *        using singular value decomposition.  IGARSS 1989: 12th Canadian
     *           symposium on Remote Sensing. Vol.4 pp.2069-2072
     */
    G_message("Singular values of Matrix A:");
    G_math_svdval( (double *) svd_values->vals, (double **) A->vals, A->cols, A->rows);
    if (error) 
        G_fatal_error("Error in singular value decomposition, exiting...\n");
    /*Experimental: display values (replace v_output() in original version)*/
    for(i=0;i<svd_values->ldim;i++)
        G_message("%f", svd_values->vals[i]);

    /* alright, start Spectral angle mapping */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    
    G_verbose_message("Calculating for %i x %i = %i pixels:\n",nrows,ncols, (ncols * ncols));
    G_verbose_message("%s ... ", G_program_name());

    for (row = 0; row < nrows; row++)                 /* rows loop*/
    {
	G_percent(row, nrows, 2);
	for (band = 0; band < Ref.nfiles; band++)     /* get row for all bands*/
	    Rast_get_c_row (cellfd[band], cell[band], row);

	for (col = 0; col < ncols; col++)             /* cols loop, work pixelwise for all bands */
	{
	    /* get pixel values of each band and store in b vector: */
	     /*b = v_get(A->m);*/                   /* dimension of vector = matrix size = Ref.nfiles*/
	     G_matvect_extract_vector(A, CVEC, Ref.nfiles); /* Yann: Doubt on "cols/CVEC", TODO CHECK: dimension of vector = matrix size = Ref.nfiles*/
             b = G_vector_copy(A, NO_COMPACT);
             G_matvect_retrieve_matrix(A);
	     for (band = 0; band < Ref.nfiles; band++)
		  b->vals[band] = cell[band][col];  /* read input vector */
	   
            /* calculate spectral angle for current pixel
             * between pixel spectrum and reference spectrum
             * and write result in full degree */
             for (i = 0; i < Ref.nfiles; i++) /* Ref.nfiles = matrixsize*/
             {
              Avector = G_matvect_get_row(A, i);  /* go row-wise through matrix*/
	      spectral_angle();
	      result_cell[i][col] = myround (curr_angle);
	      G_vector_free(Avector);
             }
	     G_vector_free(b);
	     
	 } /* columns loop */

	/* write the resulting rows: */
        for (i = 0; i < Ref.nfiles; i++)
          Rast_put_c_row (resultfd[i], result_cell[i]);

    } /* rows loop */
    G_percent(row, nrows, 2);
	
   /* close files */
    for (i = 0; i < Ref.nfiles; i++)
    {
	  Rast_close (resultfd[i]);
	  Rast_unopen(cellfd[i]);
	  /* make grey scale color table */
	  /*sprintf(result_name, "%s.%d", result_prefix, (i+1));	               
          sprintf(command, "r.colors map=%s color=grey >/dev/null", result_name);
          system(command);*/ /*Commented by Yann*/
          /* write a color table */
    }
    G_matrix_free(A);
    make_history(result_name, parm.group->answer, parm.matrixfile->answer);
    return(EXIT_SUCCESS);
} /* main*/


CELL myround (double x)
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
                                        
