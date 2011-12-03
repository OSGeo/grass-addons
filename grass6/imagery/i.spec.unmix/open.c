/* Spextral unmixing with Singular Value Decomposition */
/* (c) 15. Jan. 1999 Markus Neteler, Hannover*/

/**************************************************************************
 ** Matrix computations based on Meschach Library
 ** Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
 **************************************************************************/

/* Cited references are from
     Steward, D.E, Leyk, Z. 1994: Meschach: Matrix computations in C.
        Proceedings of the centre for Mathematics and its Applicaions.
        The Australian National University. Vol. 32.
        ISBN 0 7315 1900 0
*/

#include "global.h"
#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include "matrix.h"
#include "matrix2.h"

int open_files()
{
    char *name, *mapset;
    FILE *fp;
    int i;
    MAT *A_input;
    
/* Read in matrix file with spectral library.
   Input matrix must contain spectra row-wise (for user's convenience)!
   Transposed here to col-wise orientation (for modules/mathematical 
   convenience).
 */

    fp=fopen(matrixfile,"r");
    if (fp == NULL)
    	{
    	 fprintf(stderr,"ERROR: Matrixfile %s not found.\n",matrixfile);
    	 exit(EXIT_FAILURE);
    	}
    A_input = m_finput(fp, MNULL);
    fclose (fp);

    if (!flag.quiet->answer)
    {
	fprintf(stderr, "Your spectral matrix = ");
	m_output(A_input);
    }
    
/* transpose input matrix from row orientation to col orientation.
 * Don't mix rows and cols in the source code and the modules
 *    messages output!  */
 
    A=m_get(A_input->m, A_input->n);
    m_transp(A_input, A);
    M_FREE(A_input);
    
    if ( A->m < A->n )
    {
	fprintf(stderr, "ERROR: Need number of cols >= rows to perform least squares fitting.\n");
	exit(EXIT_FAILURE);
    }
    matrixsize = A->m; /* number of rows must be equivalent to no. of bands */

/* open input files from group */
    if (!I_find_group(group))
    {
	fprintf (stderr, "group=%s - not found\n", group);
	exit(EXIT_FAILURE);
    }
    I_get_group_ref(group, &Ref);
    if (Ref.nfiles <= 1)
    {
	fprintf (stderr, "ERROR: Group %s\n", group);
	if (Ref.nfiles <= 0)
	    fprintf (stderr, "doesn't have any files\n");
	else
	    fprintf (stderr, "only has 1 file\n");
	fprintf (stderr, "The group must have at least 2 files\n");
	exit(EXIT_FAILURE);
    }
   /* Error check: input file number must be equal to matrix size */
    if (Ref.nfiles != matrixsize)
    {
	fprintf (stderr, "ERROR: Number of %i input files in group <%s>\n", Ref.nfiles, group);
 	fprintf (stderr, "       does not match no. of spectra in matrix \
 	                 (contains only %i cols).\n", A->m);
	exit(1);
    }

   /* get memory for input files */
    cell = (CELL **) G_malloc (Ref.nfiles * sizeof (CELL *));
    cellfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < Ref.nfiles; i++)
    {
	cell[i] = G_allocate_cell_buf();
	name = Ref.file[i].name;
	mapset = Ref.file[i].mapset;
	if (!flag.quiet->answer)
		fprintf (stderr,"Opening input file no. %i [%s]\n", (i+1), name);
	if ((cellfd[i] = G_open_cell_old (name, mapset)) < 0)
	{
	    fprintf (stderr, "Unable to proceed\n");
	    exit(1);
	}
    }

/* open files for results*/
    result_cell = (CELL **) G_malloc (Ref.nfiles * sizeof (CELL *));
    resultfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < (A->n); i++)      /* no. of spectra */
    {
	 sprintf(result_name, "%s.%d", result_prefix, (i+1));
	 if (!flag.quiet->answer)
		fprintf (stderr,"Opening output file [%s]\n", result_name);	 
	 result_cell[i] = G_allocate_cell_buf();
	 if ((resultfd[i] = G_open_cell_new (result_name)) <0)
	 {	 
	 	fprintf (stderr, "GRASS-Database internal error: Unable to proceed\n");
		exit(1) ;
	 }
    }


/* open file containing SMA error*/

    error_cell = (CELL *) G_malloc (sizeof (CELL *));
    if (error_name)
    {
	error_fd = G_open_cell_new (error_name);
	if (!flag.quiet->answer)
		fprintf (stderr,"Opening error file [%s]\n", error_name);
	if (error_fd < 0)
	    fprintf (stderr, "Unable to create error layer [%s]", error_name);
	else
	    error_cell = G_allocate_cell_buf();
    }
 
/* open file containing number of iterations */

    iter_cell = (CELL *) G_malloc (sizeof (CELL *));
    if (iter_name)
    {
	iter_fd = G_open_cell_new (iter_name);
	if (!flag.quiet->answer)
		fprintf (stderr,"Opening iteration file [%s]\n", iter_name);
	if (iter_fd < 0)
	    fprintf (stderr, "Unable to create iterations layer [%s]", iter_name);
	else
	    iter_cell = G_allocate_cell_buf();
    }

 return(matrixsize); /* give back number of output files (= Ref.nfiles) */
}
