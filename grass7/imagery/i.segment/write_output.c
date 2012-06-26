/* transfer the segmented regions from the segmented data file to a raster file */
/* close_files() function is at bottom */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int write_output(struct files *files)
{
    int out_fd, mean_fd, row, col; /* mean_fd for validiating/debug of means, todo, could add array... */
    CELL *outbuf;
    DCELL *meanbuf;

    outbuf = Rast_allocate_c_buf();	/*hold one row of data to put into raster */
	meanbuf = Rast_allocate_d_buf();

    /* Todo: return codes are 1 for these, need to check and react to errors? programmer's manual didn't include it... */

    segment_flush(&files->out_seg);	/* force all data to disk */
    segment_flush(&files->bands_seg); /* TODO use IFDEF or just delete for all these parts? for debug/validation output */

    G_debug(1, "preparing output raster");
    /* open output raster map */
    out_fd = Rast_open_new(files->out_name, CELL_TYPE);
	mean_fd = Rast_open_new(files->out_band, DCELL_TYPE);
	
    G_debug(1, "start data transfer from segmentation file to raster");
    /* transfer data from segmentation file to raster */
    /* output segmentation file: each element includes the segment ID then processing flag(s).  So just need the first part of it. */

    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);
	Rast_set_c_null_value(outbuf, files->ncols); /*set buffer to NULLs, only write those that weren't originally masked */
	Rast_set_d_null_value(meanbuf, files->ncols);
	for (col = 0; col < files->ncols; col++) {
	    segment_get(&files->out_seg, (void *)files->out_val, row, col);
	    G_debug(5, "outval[0] = %i", files->out_val[0]);
	    if(files->out_val[0] >= 0) /* only write positive segment ID's, using -1 as indicator of Null/Masked pixels.  TODO: OK to use -1 as flag for this? */
	    {outbuf[col] = files->out_val[0];	/*just want segment assignment, not the other processing flag(s) */
	//	meanbuf[col] = files->out_val[0];
	}
		
		segment_get(&files->bands_seg, (void *)files->bands_val, row, col);
	    if(files->out_val[0] >= 0) 
	    meanbuf[col] = files->bands_val[0];
	    
	}
	Rast_put_row(out_fd, outbuf, CELL_TYPE);
	Rast_put_row(mean_fd, meanbuf, DCELL_TYPE);
    }

/* TODO: I don't understand the header/history/etc for raster storage.  Can/should we save any information about the segmentation
 * settings used to create the raster?  What the input image group was?  Anything else the statistics module would need?
 */

/* TODO after we have a count of create segments... if(total segments == 0) G_warning(_("No segments were created. Verify threshold and region settings.")); */

    /* close and save file */
    Rast_close(out_fd);
    Rast_close(mean_fd);

	/* free memory */
	G_free(outbuf);
	G_free(meanbuf);

    return 0;
}

int close_files(struct files *files)
{
    /* close segmentation files and output raster */
    G_debug(1, "closing files");
    segment_close(&files->bands_seg);
    segment_close(&files->out_seg);
    segment_close(&files->no_check);
    segment_close(&files->bounds_seg);

    G_free(files->bands_val);
    G_free(files->second_val);
    G_free(files->out_val);

    G_debug(1, "close_files() before link_cleanup()");
    /*    link_cleanup((struct link_head *)files->token); */
    link_cleanup(files->token);
    G_debug(1, "close_files() after link_cleanup()");


    /* anything else left to clean up? */

    return 0;
}
