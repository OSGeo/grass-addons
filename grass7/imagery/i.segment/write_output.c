/* transfer the segmented regions from the segmented data file to a raster file */
/* close_files() function is at bottom */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

/* TODO some time delay here with meanbuf, etc being processed.  I only put if statements on the actual files
 * to try and keep the code more clear.  Need to see if this raster makes stats processing easier?  Or IFDEF it out?
 */

int write_output(struct files *files)
{
    int out_fd, mean_fd, row, col;	/* mean_fd for validiating/debug of means, todo, could add array... */
    CELL *outbuf;
    DCELL *meanbuf;
	struct Colors colors;
	
    outbuf = Rast_allocate_c_buf();	/*hold one row of data to put into raster */
    meanbuf = Rast_allocate_d_buf();

    /* Todo: return codes are 1 for these, need to check and react to errors? programmer's manual didn't include it... */

    /* force all data to disk */
    segment_flush(&files->bands_seg);	/* TODO use IFDEF or just delete for all these parts? for debug/validation output */

    G_debug(1, "preparing output raster");
    /* open output raster map */
    out_fd = Rast_open_new(files->out_name, CELL_TYPE);
    if (files->out_band != NULL)
	mean_fd = Rast_open_new(files->out_band, DCELL_TYPE);

    G_debug(1, "start data transfer from segmentation file to raster");
    /* transfer data from segmentation file to raster */

    for (row = 0; row < files->nrows; row++) {
	Rast_set_c_null_value(outbuf, files->ncols);	/*set buffer to NULLs, only write those that weren't originally masked */
	Rast_set_d_null_value(meanbuf, files->ncols);
	for (col = 0; col < files->ncols; col++) {
	    segment_get(&files->bands_seg, (void *)files->bands_val, row,
			col);
	    if (!(flag_get(files->null_flag, row, col))) {
		outbuf[col] = files->iseg[row][col];
		meanbuf[col] = files->bands_val[0];
	    }
	}
	Rast_put_row(out_fd, outbuf, CELL_TYPE);
	if (files->out_band != NULL)
	    Rast_put_row(mean_fd, meanbuf, DCELL_TYPE);

	G_percent(row, files->nrows, 1);
    }

    /* TODO: I don't understand the header/history/etc for raster storage.  Can/should we save any information about the segmentation
     * settings used to create the raster?  What the input image group was?  Anything else the statistics module would need?
     * check it with r.info to see what we have by default.
     */

    /* TODO after we have a count of create segments... if(total segments == 0) G_warning(_("No segments were created. Verify threshold and region settings.")); */

    /* close and save file */
    Rast_close(out_fd);
    if (files->out_band != NULL)
	Rast_close(mean_fd);

	/* set colors */
	Rast_init_colors(&colors);
	Rast_make_random_colors(&colors, 1, files->nrows*files->ncols); /* TODO polish - number segments from 1 - max ? and then can use that max here. */
	Rast_write_colors(files->out_name, G_mapset(), &colors); /* TODO, OK to just use G_mapset() here, seems I don't use it anywhere else, and that is where the output has to be written.  (Should the library allow changing colors to other mapsets???) */
	
    /* free memory */
    G_free(outbuf);
    G_free(meanbuf);
	Rast_free_colors(&colors);
	
    return TRUE;
}

int close_files(struct files *files)
{
    int i;

    /* close segmentation files and output raster */
    G_debug(1, "closing bands_seg...");
    segment_close(&files->bands_seg);
    G_debug(1, "closing bounds_seg...");
    if (files->bounds_map != NULL) 
        segment_close(&files->bounds_seg);
    
    G_debug(1, "freeing _val");
    G_free(files->bands_val);
    G_free(files->second_val);

    G_debug(1, "freeing iseg");
    for (i = 0; i < files->nrows; i++)
	G_free(files->iseg[i]);
    G_free(files->iseg);

    G_debug(1, "destroying flags");
    flag_destroy(files->null_flag);
    flag_destroy(files->candidate_flag);
//    flag_destroy(files->no_check);

    G_debug(1, "close_files() before link_cleanup()");
    link_cleanup(files->token);
    G_debug(1, "close_files() after link_cleanup()");

    /* anything else left to clean up? */

    return TRUE;
}
