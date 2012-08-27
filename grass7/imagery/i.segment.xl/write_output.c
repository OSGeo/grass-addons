/* transfer the segmented regions from the segmented data file to a raster file */
/* close_files() function is at bottom */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include <grass/glocale.h>
#include "iseg.h"

/* TODO some time delay here with meanbuf, etc being processed.  I only put if statements on the actual files
 * to try and keep the code more clear.  Need to see if this raster makes stats processing easier?  Or IFDEF it out?
 */

int write_output(struct globals *globals)
{
    int out_fd, mean_fd, row, col;
    CELL *outbuf, rid;
    FCELL *meanbuf;
    struct Colors colors;
    double thresh, maxdev, sim, mingood;
    struct reg_stats *rs_found;
    struct ngbr_stats Ri, Rk;

    outbuf = Rast_allocate_c_buf();

    G_debug(1, "preparing output raster");
    /* open output raster map */
    out_fd = Rast_open_new(globals->out_name, CELL_TYPE);
    if (globals->out_band) {
	mean_fd = Rast_open_new(globals->out_band, FCELL_TYPE);
	meanbuf = Rast_allocate_f_buf();
    }
    else {
	mean_fd = -1;
	meanbuf = NULL;
    }

    /* goodness of fit for each cell: 1 = good fit, 0 = bad fit */
    /* similarity of each cell to region mean
     * max possible difference: globals->threshold
     * if similarity < globals->alpha * globals->alpha * globals->threshold
     * 1
     * else 
     * (similarity - globals->alpha * globals->alpha * globals->threshold) /
     * (globals->threshold * (1 - globals->alpha * globals->alpha) */

    thresh = globals->alpha * globals->alpha * globals->threshold;
    maxdev = globals->threshold * (1 - globals->alpha * globals->alpha);
    mingood = 1;

    G_debug(1, "start data transfer from segmentation file to raster");

    G_message(_("Writing output"));
    for (row = 0; row < globals->nrows; row++) {

	G_percent(row, globals->nrows, 9);

	Rast_set_c_null_value(outbuf, globals->ncols);
	if (globals->out_band)
	    Rast_set_f_null_value(meanbuf, globals->ncols);
	for (col = 0; col < globals->ncols; col++) {

	    if (!(FLAG_GET(globals->null_flag, row, col))) {
		segment_get(&globals->rid_seg, (void *) &rid, row, col);

		if (rid > 0) {
		    outbuf[col] = rid;

		    if (globals->out_band) {

			/* get values for Ri = larger region */
			globals->rs.id = rid;
			rs_found = rgtree_find(globals->reg_tree, &(globals->rs));

			if (rs_found != NULL) {
			    Ri.mean = rs_found->mean;

			    /* get values for Rk = this cell */
			    segment_get(&globals->bands_seg,
					(void *)globals->second_val, row, col);

			    Rk.mean = globals->second_val;

			    /* calculate similarity */
			    sim = (*globals->calculate_similarity) (&Ri, &Rk, globals);
			}
			else
			    /* region consists of only one cell */
			    sim = 0.;
			
			if (0) {
			    if (sim < thresh)
				meanbuf[col] = 1;
			    else {
				sim = 1. - (sim - thresh) / maxdev;
				meanbuf[col] = sim;
				if (mingood > sim)
				    mingood = sim;
			    }
			}
			else {
			    sim = 1 - sim / globals->threshold;
			    meanbuf[col] = sim;
			    if (mingood > sim)
				mingood = sim;
			}
		    }
		}
	    }
	}
	Rast_put_row(out_fd, outbuf, CELL_TYPE);
	if (globals->out_band)
	    Rast_put_row(mean_fd, meanbuf, FCELL_TYPE);
    }

    /* close and save file */
    Rast_close(out_fd);
    if (globals->out_band)
	Rast_close(mean_fd);

    /* set colors */
    Rast_init_colors(&colors);
    Rast_make_random_colors(&colors, 1, globals->nrows * globals->ncols);
    Rast_write_colors(globals->out_name, G_mapset(), &colors);
    
    if (globals->out_band) {
	Rast_init_colors(&colors);
	Rast_make_grey_scale_fp_colors(&colors, mingood, 1);
	Rast_write_colors(globals->out_band, G_mapset(), &colors);
    }

    /* free memory */
    G_free(outbuf);
    G_free(meanbuf);
    Rast_free_colors(&colors);

    return TRUE;
}

int close_files(struct globals *globals)
{
    /* close segmentation files and output raster */
    G_debug(1, "closing files");
    segment_close(&globals->bands_seg);
    if (globals->bounds_map)
	segment_close(&globals->bounds_seg);

    G_free(globals->bands_val);
    G_free(globals->second_val);

    segment_close(&globals->rid_seg);

    /*
    for (i = 0; i < globals->nrows; i++)
	G_free(globals->rid[i]);
    G_free(globals->rid);
    */

    flag_destroy(globals->null_flag);
    flag_destroy(globals->candidate_flag);

    /* anything else left to clean up? */

    return TRUE;
}
