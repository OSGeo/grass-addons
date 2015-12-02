/* Spectral angle mapping 
 * (c) Oct/1998 Markus Neteler, Hannover
*/

#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "global.h"

int G_matrix_read2(FILE * fp, mat_struct * out); /* Modified version of G_matrix_read(..). */

mat_struct *open_files(char *matrixfile, char *img_grp, int type)
{
    char *name, *mapset;
    FILE *fp;
    int i;
    mat_struct A_input, *A;

    /* read in matrix file with spectral library */

    fp=fopen(matrixfile,"r");
    if (fp == NULL)
    	G_fatal_error("ERROR: Matrixfile %s not found.\n",matrixfile);
    /* Read data and close file */
    if ((G_matrix_read2(fp, &A_input) < 0))
	G_fatal_error(_("Unable to read matrix file %s."), matrixfile);
    fclose(fp);

    G_message("matrixfile read");

    A = G_matrix_init(A_input.cols, A_input.rows, A_input.cols);/*changed r/c*/
    if (A == NULL)
        G_fatal_error(_("Unable to allocate memory for matrix"));
    if(type==1)
        A = G_matrix_transpose(&A_input);/*transposed for spec angle process*/
    if(type==0){
        A = G_matrix_copy(&A_input);/*for matrix orthogonality check*/
        return A;
    }
/*    if(A->rows < A->cols)
	G_fatal_error("Need m (rows) >= n (cols) to obtain least squares fit\n");*/
    /*Only for debug, so temporary disabled*/
    /*
    G_verbose_message("Your spectral matrix = ");
    if (G_verbose() > G_verbose_std())
    {
	m_output(A);
    }
    */
    matrixsize=A->rows;

    G_message("/* open input files from group */");
/* open input files from group */
    if (!I_find_group(img_grp))
    {
	G_fatal_error("group=%s - not found\n", img_grp);
    }
    I_get_group_ref(img_grp, &Ref);
    if (Ref.nfiles <= 1)
    {
	G_message("Group %s\n", img_grp);
	if (Ref.nfiles <= 0)
	    G_message("doesn't have any files\n");
	else
	    G_message("only has 1 file\n");
	G_fatal_error("The group must have at least 2 files\n");
    }
   /* Error check: input file number must be equal to matrix size */
    if (Ref.nfiles != matrixsize) 
    {
	G_message("Error: Number of %i input files in group <%s>\n", Ref.nfiles, img_grp);
 	G_fatal_error("       does not match matrix size (%i cols).\n", A->cols);
    }

   G_message("/* get memory for input files */");
   /* get memory for input files */
    cell = (DCELL **) G_malloc (Ref.nfiles * sizeof (DCELL *));
    cellfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < Ref.nfiles; i++)
    {
	cell[i] = Rast_allocate_d_buf();
	name = Ref.file[i].name;
	mapset = Ref.file[i].mapset;
	G_verbose_message("Opening input file no. %i [%s]\n", (i+1), name);
	if ((cellfd[i] = Rast_open_old (name, mapset)) < 0)
	    G_fatal_error("Unable to proceed\n");
    }

    G_message("/* open files for results*/");
  /* open files for results*/
    result_cell = (DCELL **) G_malloc (Ref.nfiles * sizeof (DCELL *));
    resultfd = (int *) G_malloc (Ref.nfiles * sizeof (int));
    for (i=0; i < Ref.nfiles; i++)
    {
	sprintf(result_name, "%s.%d", result_prefix, (i+1));
	G_verbose_message("Opening output file [%s]\n", result_name);	 
	result_cell[i] = Rast_allocate_d_buf();
	resultfd[i] = Rast_open_new (result_name, DCELL_TYPE);
    }

    G_message("open.c: Returning A");
 return A; /* give back number of output files (= Ref.nfiles) */
}

int G_matrix_read2(FILE * fp, mat_struct * out)
{
    char buff[100];
    int rows, cols;
    int i, j, row;
    double val;
    int err;

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

    G_message("Set Matrix rows:%d by cols:%d",rows,cols);
    err = G_matrix_set(out, rows, cols, rows);
    G_message("Set Matrix rows:%d by cols:%d is done (err:%d)",rows,cols,err);


    for (i = 0; i < rows; i++) {
	if (fscanf(fp, "row%d:", &row) != 1) {
	    G_warning(_("Input format error at row %d"),row);
	    return -1;
	}

	for (j = 0; j < cols; j++) {
	    if (fscanf(fp, " %lf", &val) != 1) {
		G_warning(_("Input format error at col %d"),j);
		return -1;
	    }

	    fgetc(fp);
	    G_matrix_set_element(out, i, j, val);
	}
    }

    return 0;
}
