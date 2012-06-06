/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int create_isegs(struct files *files, struct functions *functions)
{
    int row, col, nrows, ncols, *segval;
    double *bandsval;

    /* **************write fake data to test I/O portion of module */

    /*picked this up in the file reading as well, just do it again? */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* initialize data structure */
    segval = (int *)G_malloc(2 * sizeof(int));
    /* TODO why didn't this work?  error: request fof member 'nbands' in something not a structure or union */
    /* bandsval = (double *) G_malloc(files.nbands * sizeof(double)); */
    bandsval = (double *)G_malloc(1 * sizeof(double));

    G_verbose_message("writing fake data");
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 1);	/*this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < ncols; col++) {
	    //segval[0] = bandsval[0]; /*segment number */  /* just copying the map for testing. */
	    segval[0] = 42;
	    segval[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)segval, row, col);
	}
    }

    /* TODO: free memory */

    return 0;
}
