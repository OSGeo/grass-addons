/* Spectral angle mapping 
 * (c) Oct/1998 Markus Neteler, Hannover
 *
 **************************************************************************
 ** Matrix computations based on Meschach Library
 ** Copyright (C) 1993 David E. Steward & Zbigniew Leyk, all rights reserved.
 **************************************************************************
 *
 * Cited references are from
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

int open_files()
{
    char *name, *mapset;
    FILE *fp;
    int i;

/* read in matrix file with spectral library */

    fp=fopen(matrixfile,"r");
    if (fp == NULL)
    	{
    	 fprintf(stderr,"ERROR: Matrixfile %s not found.\n",matrixfile);
    	 exit(1);
    	}
    A = m_finput(fp, MNULL);
    fclose (fp);
    if ( A->m < A->n )
    {
	fprintf(stderr, "Need m (rows) >= n (cols) to obtain least squares fit\n");
	exit(1);
    }
    if (!flag.quiet->answer)
    {
	fprintf(stderr, "Your spectral matrix = ");
	m_output(A);
    }
    matrixsize = A->n;

/* open input files from group */
    if (!I_find_group(group))
    {
	fprintf (stderr, "group=%s - not found\n", group);
	exit(1);
    }
    I_get_group_ref(group, &Ref);
    if (Ref.nfiles <= 1)
    {
	fprintf (stderr, "Group %s\n", group);
	if (Ref.nfiles <= 0)
	    fprintf (stderr, "doesn't have any files\n");
	else
	    fprintf (stderr, "only has 1 file\n");
	fprintf (stderr, "The group must have at least 2 files\n");
	exit(1);
    }
   /* Error check: input file number must be equal to matrix size */
    if (Ref.nfiles != matrixsize) 
    {
	fprintf (stderr, "Error: Number of %i input files in group <%s>\n", Ref.nfiles, group);
 	fprintf (stderr, "       does not match matrix size (%i cols).\n", A->n);
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
    for (i=0; i < Ref.nfiles; i++)
    {
	 sprintf(result_name, "%s.%d", result_prefix, (i+1));
	 if (!flag.quiet->answer)
		fprintf (stderr,"Opening output file [%s]\n", result_name);	 
	 result_cell[i] = G_allocate_cell_buf();
	 if ((resultfd[i] = G_open_cell_new (result_name)) <0)
	 {	 
	 	fprintf (stderr, "Unable to proceed\n");
		exit(1) ;
	 }
    }


 return(matrixsize); /* give back number of output files (= Ref.nfiles) */
}
