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
             
#define GLOBAL
#include "global.h"
#include <stdio.h>
#include <strings.h>
#include <math.h>
#include "matrix.h"
#include "matrix2.h"
#include "local_proto.h"

int open_files();
void spectral_angle();
CELL myround (x);

int main(argc,argv) 
char *argv[];
{
    int nrows, ncols;
    int row, col;
    int band;
    int i, j, error=0;
    VEC *svd_values;
    char command[80];
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

    parm.result = G_define_option();
    parm.result->key = "result";
    parm.result->type = TYPE_STRING;
    parm.result->required = YES;
    parm.result->description = "Raster map prefix to hold spectral angles";

    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = "Run quietly";


    if (G_parser(argc,argv))
	exit(1);

    result_prefix = parm.result->answer;
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
	     V_FREE(b);
	    }
	}
     V_FREE(Avector);
    }

    /* print out the result */
    fprintf(stderr,"Orthogonality check of Matrix A:\n");
    for (i = 0; i < Ref.nfiles ; i++)
      for (j = 0; j < Ref.nfiles ; j++)
	{
         if (j !=i)
         	fprintf(stderr,"  Angle between row %i and row %i: %g\n", (i+1), (j+1), anglefield[i][j]);
        }
    fprintf(stderr,"\n");
    
   /* check it */
   for (i = 0; i < Ref.nfiles ; i++)
     for (j = 0; j < Ref.nfiles ; j++)
       if (j !=i)
         if (anglefield[i][j] < 10.0)
         {
	     fprintf(stderr,"ERROR: Spectral entries row %i|%i in your matrix are linear dependent!\n",i,j);
	     error=1;
	 }

   if (!error)
	fprintf(stderr,"Spectral matrix is o.k. Proceeding...\n");
   
/* check singular values of Matrix A
 * Ref: Boardman, J.W. 1989: Inversion of imaging spectrometry data
 *           using singular value decomposition.  IGARSS 1989: 12th Canadian
 *           symposium on Remote Sensing. Vol.4 pp.2069-2072
 */
    fprintf(stderr,"\n");
    fprintf(stderr,"Singular values of Matrix A:");
    svd_values = svd(A, MNULL, MNULL, VNULL);
    v_output(svd_values);
    fprintf(stderr,"\n");    
 if (error) 
 {
  fprintf(stderr,"Exiting...\n");
  exit(-1);
 }

 /* alright, start Spectral angle mapping */
    nrows = G_window_rows();
    ncols = G_window_cols();
    
    if (!flag.quiet->answer)
    	{
	 fprintf (stderr, "Calculating for %i x %i = %i pixels:\n",nrows,ncols, (ncols * ncols));
	 fprintf (stderr, "%s ... ", G_program_name());
	}
    for (row = 0; row < nrows; row++)                 /* rows loop*/
    {
	if (!flag.quiet->answer)
	    G_percent(row, nrows, 2);
	for (band = 0; band < Ref.nfiles; band++)     /* get row for all bands*/
	   {
	    if (G_get_map_row (cellfd[band], cell[band], row) < 0)
		exit(1);
	   }

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
	      V_FREE(Avector);
             }

	     V_FREE(b);
	     
	   } /* columns loop */

	/* write the resulting rows: */
        for (i = 0; i < Ref.nfiles; i++)
          G_put_map_row (resultfd[i], result_cell[i]);

    } /* rows loop */

    if (!flag.quiet->answer)
	G_percent(row, nrows, 2);
	
   /* close files */
    for (i = 0; i < Ref.nfiles; i++)
    	{
	  G_close_cell (resultfd[i]);
	  G_unopen_cell(cellfd[i]);
	  /* make grey scale color table */
	  sprintf(result_name, "%s.%d", result_prefix, (i+1));	               
          sprintf(command, "r.colors map=%s color=grey >/dev/null", result_name);
          system(command);
          /* write a color table */
	}

    M_FREE(A);
    make_history(result_name, group, matrixfile);
    exit(0);
} /* main*/


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
                                        
