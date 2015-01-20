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
#include <grass/raster.h>
#include "matrix.h"

int open_files()
{
    char *name, *mapset;
    FILE *fp;
    int i;

/* read in matrix file with spectral library */

    fp=fopen(matrixfile,"r");
    if (fp == NULL)
    	G_fatal_error("ERROR: Matrixfile %s not found.\n",matrixfile);
    A = m_finput(fp, MNULL);
    fclose (fp);
    if ( A->m < A->n )
	G_fatal_error("Need m (rows) >= n (cols) to obtain least squares fit\n");
    if (!flag_quiet->answer)
    {
	G_message("Your spectral matrix = ");
	m_output(A);
    }
    matrixsize = A->n;

/* open input files from group */
    if (!I_find_group(group))
    {
	G_message("group=%s - not found\n", group);
	exit(1);
    }
    I_get_group_ref(group, &Ref);
    if (Ref.nfiles <= 1)
    {
	G_message("Group %s\n", group);
	if (Ref.nfiles <= 0)
	    G_message("doesn't have any files\n");
	else
	    G_message("only has 1 file\n");
	G_fatal_error("The group must have at least 2 files\n");
    }
   /* Error check: input file number must be equal to matrix size */
    if (Ref.nfiles != matrixsize) 
    {
	G_message("Error: Number of %i input files in group <%s>\n", Ref.nfiles, group);
 	G_fatal_error("       does not match matrix size (%i cols).\n", A->n);
    }

   /* get memory for input files */
    cell = (CELL **) G_malloc (Ref.nfiles * sizeof (CELL *));
    cellfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < Ref.nfiles; i++)
    {
	cell[i] = Rast_allocate_c_buf();
	name = Ref.file[i].name;
	mapset = Ref.file[i].mapset;
	if (!flag_quiet->answer)
	    G_message("Opening input file no. %i [%s]\n", (i+1), name);
	if ((cellfd[i] = Rast_open_old (name, mapset)) < 0)
	    G_fatal_error("Unable to proceed\n");
    }

  /* open files for results*/
    result_cell = (CELL **) G_malloc (Ref.nfiles * sizeof (CELL *));
    resultfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < Ref.nfiles; i++)
    {
	sprintf(result_name, "%s.%d", result_prefix, (i+1));
	if (!flag_quiet->answer)
	    G_message("Opening output file [%s]\n", result_name);	 
	result_cell[i] = Rast_allocate_c_buf();
	resultfd[i] = Rast_open_c_new (result_name);
    }


 return(matrixsize); /* give back number of output files (= Ref.nfiles) */
}
