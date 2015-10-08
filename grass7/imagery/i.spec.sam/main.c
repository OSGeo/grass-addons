/* Spectral angle mapping
 * (c) 1998 Markus Neteler, Hannover, Germany
 *          neteler@geog.uni-hannover.de
 *
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
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "local_proto.h"
#include "global.h"

mat_struct *A;
vec_struct *b, *Avector;
int matrixsize;
float curr_angle;

char *group;
struct Ref Ref;

CELL **cell;
int *cellfd;

CELL **result_cell;
int *resultfd;

CELL **error_cell;
int  error_fd;

char result_name[80];
char *result_prefix, *matrixfile;

int open_files();
void spectral_angle();
CELL myround(double x);

int main(int argc,char * argv[])
{
    int nrows, ncols;
    int row, col;
    int band;
    int i, j, error=0;
    VEC *svd_values;
    /*char command[80]; rm by Yann temporarily see grayscale palette*/
    float anglefield[255][255];
    struct
    {
	struct Option *group, *matrixfile, *result;
    } parm;

    G_gisinit (argv[0]);

    parm.group = G_define_option();
    parm.group->key = "group";
    parm.group->type = TYPE_STRING;
    parm.group->required = YES;
    parm.group->description = "Imagery group containing images to be analyzed with Spectral Mixture Analyis";

    parm.matrixfile = G_define_option();
    parm.matrixfile->key = "matrixfile";
    parm.matrixfile->type = TYPE_STRING;
    parm.matrixfile->required = YES;
    parm.matrixfile->description = "Matrix file containing spectral signatures ";

    parm.output = G_define_option();
    parm.output->key = "result";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->description = "Raster map prefix to hold spectral angles";

    if (G_parser(argc,argv))
	G_fatal_error("Parsing arguments error");

    result_prefix = parm.output->answer;
    group       = parm.group->answer;
    matrixfile  = parm.matrixfile->answer;


/* here we go... */

    open_files();
   /* Spectral Matrix is stored in A now */

  /* Check matrix orthogonality 
   * Ref: Youngsinn Sohn, Roger M. McCoy 1997: Mapping desert shrub rangeland
   *          using spectral unmixing and modeling spectral mixtrues with 
   *          TM data. Photogrammetric Engineering & Remote Sensing, Vol.63, No6.
   */
     
    for (i = 0; i < Ref.nfiles; i++) /* Ref.nfiles = matrixsize*/
    {
     Avector = get_row(A, i, VNULL);  /* go columnwise through matrix*/
     for (j = 0; j < Ref.nfiles ; j++)
	{
	 if (j !=i)
	    {
	     b = get_row(A, j, VNULL);      /* compare with next col in A */
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
    svd_values = svd(A, MNULL, MNULL, VNULL);
    v_output(svd_values);
 if (error) 
 {
  G_fatal_error("Exiting...\n");
 }

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
	     b = v_get(A->m);                     /* dimension of vector = matrix size = Ref.nfiles*/
	     for (band = 0; band < Ref.nfiles; band++)
		  b->ve[band] = cell[band][col];  /* read input vector */
	   
            /* calculate spectral angle for current pixel
             * between pixel spectrum and reference spectrum
             * and write result in full degree */
             
             for (i = 0; i < Ref.nfiles; i++) /* Ref.nfiles = matrixsize*/
             {
              Avector = get_row(A, i, VNULL);  /* go row-wise through matrix*/
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
    make_history(result_name, group, matrixfile);
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
                                        
