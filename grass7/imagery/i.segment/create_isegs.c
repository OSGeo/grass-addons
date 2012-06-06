/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int create_isegs(struct files *files, struct functions *functions)
{
    int row, col, nrows, ncols;

    /* **************write fake data to test I/O portion of module */

    /*picked this up in the file reading as well, just do it again? */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* initialize data structure */
    files->out_val = (int *)G_malloc(2 * sizeof(int));

    G_verbose_message("writing fake data to segmentation file");
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 1);	/*this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < ncols; col++) {
	    //files->out_val[0] = files->out_val[0]; /*segment number */  /* just copying the map for testing. */
	    files->out_val[0] = col+2*row;
	    files->out_val[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)files->out_val, row, col);
	}
    }

    /* TODO: free memory */

    return 0;
}
