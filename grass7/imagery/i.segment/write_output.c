/* transfer the segmented regions from the segmented data file to a raster file */
/* close_files() function is at bottom */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int write_output(struct files *files)
{
    int out_fd, row, col, n;
    CELL *outbuf;

    outbuf = Rast_allocate_c_buf();	/*hold one row of data to put into raster */

    /* Todo: return codes are 1 for these, need to check and react to errors? programmer's manual didn't include it... */

    segment_flush(&files->out_seg);	/* force all data to disk */

    G_debug(1, "preparing output raster");
    /* open output raster map */
    out_fd = Rast_open_new(files->out_name, CELL_TYPE);

    G_debug(1, "start data transfer from segmentation file to raster");
    /* transfer data from segmentation file to raster */
    /* output segmentation file: each element includes the segment ID then processing flag(s).  So just need the first part of it. */

    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);	/*TODO: Why isn't this getting printed? */
	for (col = 0; col < files->ncols; col++) {
	    segment_get(&files->out_seg, (void *)files->out_val, row, col);
	    G_debug(5, "outval[0] = %i", files->out_val[0]);
	    outbuf[col] = files->out_val[0];	/*just want segment assignment, not the other processing flag(s) */
	}
	Rast_put_row(out_fd, outbuf, CELL_TYPE);
    }

    /* close and save file */
    Rast_close(out_fd);

    return 0;
}

int close_files(struct files *files)
{
    /* close segmentation files and output raster */
    G_debug(1, "closing files");
    segment_close(&files->bands_seg);
    segment_close(&files->out_seg);
    segment_close(&files->no_check);

    /* close segmentation files and output raster */

    G_free(files->bands_val);
    G_free(files->second_val);
    G_free(files->out_val);

    /* anything else left to clean up? */

    return 0;
}
