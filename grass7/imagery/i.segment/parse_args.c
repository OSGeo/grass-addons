/* PURPOSE:      Parse and validate the input */

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include "iseg.h"

int parse_args(int argc, char *argv[], struct files *files,
	       struct functions *functions)
{
    /* reference: http://grass.osgeo.org/programming7/gislib.html#Command_Line_Parsing */

    struct Option *group, *seeds, *bounds, *output, *method, *threshold, *min_segment_size;	/* Establish an Option pointer for each option */
    struct Flag *diagonal, *weighted;	/* Establish a Flag pointer for each option */
    struct Option *outband, *endt;	/* debugging parameters... TODO: leave in code or remove?  hidden options? */

    /* required parameters */
    group = G_define_standard_option(G_OPT_I_GROUP);	/* TODO: OK to require the user to create a group?  Otherwise later add an either/or option to give just a single raster map... */

    output = G_define_standard_option(G_OPT_R_OUTPUT);

/*TODO polish: any way to recommend a threshold to the user */
    threshold = G_define_option();
    threshold->key = "threshold";
    threshold->type = TYPE_DOUBLE;
    threshold->required = YES;
    threshold->description = _("Similarity threshold.");

    method = G_define_option();
    method->key = "method";
    method->type = TYPE_STRING;
    method->required = YES;
    method->answer = "region_growing";
    method->options = "region_growing, io_debug, ll_test";	/* TODO at end, remove these from list: io_debug just writes row+col to each output pixel, ll_test for testing linked list data structure */
    method->description = _("Segmentation method.");

	min_segment_size = G_define_option();
	min_segment_size->key = "min"; /*TODO is there a preference for long or short key names? min is pretty generic...but short... */
	min_segment_size->type = TYPE_INTEGER;
	min_segment_size->required = YES;
	min_segment_size->answer = "10"; /* TODO, should a "typical" default be provided? */
	min_segment_size->options = "1-100000"; /*must be positive number, is >0 allowed in "options" or is 100,000 suitably large? */
	min_segment_size->description = _("Minimum number of pixels (cells) in a segment.  The final merge step will ignore the threshold for any segments with fewer pixels.");
    
    /* optional parameters */

    diagonal = G_define_flag();
    diagonal->key = 'd';
    diagonal->description =
	_("Use 8 neighbors (3x3 neighborhood) instead of the default 4 neighbors for each pixel.");

    weighted = G_define_flag();
    weighted->key = 'w';
    weighted->description =
	_("Weighted input, don't perform the default scaling of input maps.");

    /* Using raster for seeds, Low priority TODO: allow vector points/centroids seed input. */
    seeds = G_define_standard_option(G_OPT_R_INPUT);
    seeds->key = "seeds";
    seeds->required = NO;
    seeds->description = _("Optional raster map with starting seeds.");

    /* Polygon constraints. */
    bounds = G_define_standard_option(G_OPT_R_INPUT);
    bounds->key = "bounds";
    bounds->required = NO;
    bounds->description =
	_("Optional bounding/constraining raster map, must be integer values, each area will be segmented independent of the others.");
    /*    bounds->description = _("Optional vector map with polygons to bound (constrain) segmentation."); */
    /* TODO: if performing second segmentation, will already have raster map from this module
     * If have preexisting boundaries (landuse, etc) will have vector map?
     * Seems we need to have it in raster format for processing, is it OK to have the user run v.to.rast before doing the segmentation?
     * Or for hierarchical segmentation, will it be easier to have the polygons?
     *  */

    /* TODO input for distance function */

    /* debug parameters */
    endt = G_define_option();
    endt->key = "endt";
    endt->type = TYPE_INTEGER;
    endt->required = NO;
    endt->answer = "10000";
    endt->description = _("Debugging...Maximum number of time steps to complete.");

    outband = G_define_standard_option(G_OPT_R_OUTPUT);
    outband->key = "final_mean";
    outband->required = NO;
    outband->description =
	_("debug - save band mean, currently implemented for only 1 band.");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* Validation */

    /* TODO: use checker for any of the data validation steps!? */

    /* ToDo The most important things to check are if the
       input and output raster maps can be opened (non-negative file
       descriptor).  ??? Do this here or in open_files?  */


    /* Check and save parameters */

    files->image_group = group->answer;

    if (G_legal_filename(output->answer) == TRUE)
	files->out_name = output->answer;	/* name of output raster map */
    else
	G_fatal_error("Invalid output raster name.");

    functions->threshold = atof(threshold->answer);	/* Note: this threshold is scaled after we know more at the beginning of create_isegs() */

    if (weighted->answer == FALSE &&
	(functions->threshold <= 0 || functions->threshold >= 1))
	G_fatal_error(_("threshold should be >= 0 and <= 1"));	/* TODO OK to have fatal error here, seems this would be an invalid entry. */

    /* segmentation methods:  0 = debug, 1 = region growing */
    /* TODO, instead of string compare, does the Option structure have these already numbered? */
    if (strncmp(method->answer, "io_debug", 5) == 0)
	functions->method = 0;
    else if (strncmp(method->answer, "region_growing", 10) == 0)
	functions->method = 1;
    else if (strncmp(method->answer, "ll_test", 5) == 0)
	functions->method = 2;
    else
	G_fatal_error("Couldn't assign segmentation method.");	/*shouldn't be able to get here */

    G_debug(1, "segmentation method: %d", functions->method);

	functions->min_segment_size = atoi(min_segment_size->answer);

    if (diagonal->answer == FALSE) {
	functions->find_pixel_neighbors = &find_four_pixel_neighbors;
	functions->num_pn = 4;
	G_debug(1, "four pixel neighborhood");
    }
    else if (diagonal->answer == TRUE) {
	functions->find_pixel_neighbors = &find_eight_pixel_neighbors;
	functions->num_pn = 8;
	G_debug(1, "eight (3x3) pixel neighborhood");
    }

    files->weighted = weighted->answer;	/* default/0 for performing the scaling, but selected/1 if user has weighted values so scaling should be skipped. */

    functions->calculate_similarity = &calculate_euclidean_similarity;	/* TODO add user input for this */

    files->seeds = seeds->answer;

    if (bounds->answer == NULL) {	/*no polygon constraints */
	files->bounds_map = NULL;
    }
    else {			/* polygon constraints given */
	files->bounds_map = bounds->answer;
	if ((files->bounds_mapset = G_find_raster(files->bounds_map, "")) == NULL) {	/* TODO, warning here:  parse_args.c:149:27: warning: assignment discards ‘const’ qualifier from pointer target type [enabled by default] */
	    G_fatal_error(_("Segmentation constraint/boundary map not found."));
	}
	if (Rast_map_type(files->bounds_map, files->bounds_mapset) !=
	    CELL_TYPE) {
	    G_fatal_error(_("Segmentation constraint map must be CELL type (integers)"));
	}
    }

    /* other data */
    files->nrows = Rast_window_rows();
    files->ncols = Rast_window_cols();

    /* debug help */
    if (outband->answer == NULL)
	files->out_band = NULL;
    else {
	if (G_legal_filename(outband->answer) == TRUE)
	    files->out_band = outband->answer;	/* name of current means */
	else
	    G_fatal_error("Invalid output raster name for means.");
    }

	if (endt->answer != NULL && endt->answer >= 0)
    functions->end_t = atoi(endt->answer);
	else {
		functions->end_t = 10000;
		G_warning(_("invalid number of iterations, 10000 will be used."));
	}
    return TRUE;
}
