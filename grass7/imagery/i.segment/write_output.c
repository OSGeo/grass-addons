/* transfer the segmented regions from the segmented data file to a raster file */
/* put closing segment files here for now, OK to combine or better to put somewhere else? */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int write_output(struct files *files)
{
    int out_fd, row, col, nrows, ncols;
    CELL *outbuf;
    int *outval;

    outbuf = Rast_allocate_c_buf();	/*hold one row of data to put into raster */
    outval = (int *)G_malloc(2 * sizeof(int));	/* hold one "cell" from the segmentation file */

    /*picked this up in the file reading as well, just do it again? */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Todo: return codes are 1 for these, need to check and react to errors? programmer's manual didn't include it... */

    segment_flush(&files->out_seg);	/* force all data to disk */

    G_debug(1, "preparing output raster");
    /* open output raster map */
    out_fd = Rast_open_new(files->out_name, CELL_TYPE);	/* I assume even if it already exists, this will overwrite it... */

    G_debug(1, "start data transfer from segmentation file to raster");
    /* transfer data from segmentation file to raster */
    /* output segmentation file, each element includes the segment ID then the processing flag.  So just need the first part of it. */
    /* Hmm, does this mean I can't use a buffer, since the length isn't simply integer or float?! */

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 1);
	for (col = 0; col < ncols; col++) {
	    //~ G_debug(1, "got here");
	    /* didn't work?                 segment_get(&files->out_seg, &outval, row, col); */
	    segment_get(&files->out_seg, (void *)outval, row, col);	/* segment_get (&seg, &value, row, col); */
	    //~ G_debug(1, "segment_get() worked");
	    //~ G_debug(1, "outval[0] = %i", outval[0]); /*This didn't work - something is wrong with outval reference */
	    outbuf[col] = outval[0];	/*just want segment assignment, not the other processing flag(s) */
	}
	//~ G_debug(1, "just before Rast_put_row()");
	Rast_put_row(out_fd, outbuf, CELL_TYPE);
    }


    /* close segmentation files and output raster */
    G_debug(1, "closing files");
    segment_close(&files->bands_seg);
    segment_close(&files->out_seg);
    Rast_close(out_fd);

    /* TODO Note: The Segment Library does not know the name of the segment file. It does not attempt to remove the file. If the file is only temporary, the programmer should remove the file after closing it. */

    /* anything else left to clean up? */

    return 0;
}
