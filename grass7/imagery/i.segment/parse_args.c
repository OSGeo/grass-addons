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

    struct Option *group, *seeds, *bounds, *output, *method, *threshold, *min_segment_size, *endt;	/* Establish an Option pointer for each option */
    struct Flag *diagonal, *weighted, *path;	/* Establish a Flag pointer for each option */
    struct Option *outband;	/* TODO scrub: put all outband code inside of #ifdef DEBUG */

    /* required parameters */
    group = G_define_standard_option(G_OPT_I_GROUP);	/* TODO? Polish, consider giving the option to process just one raster directly, without creating an image group. */

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    /*TODO polish: any way to recommend a threshold to the user */
    threshold = G_define_option();
    threshold->key = "threshold";
    threshold->type = TYPE_DOUBLE;
    threshold->required = YES;
    threshold->description = _("Similarity threshold.");	/* TODO? Polish, should all descriptions get the _() locale macro? */

    method = G_define_option();
    method->key = "method";
    method->type = TYPE_STRING;
    method->required = YES;
    method->answer = "region_growing";
#ifdef DEBUG
    method->options = "region_growing, io_debug, ll_test, seg_time";
#else
    method->options = "region_growing";
#endif
    method->description = _("Segmentation method.");

    min_segment_size = G_define_option();
    min_segment_size->key = "min";	/*TODO Markus, is there a preference for long or short key names? min is pretty generic...but short... */
    min_segment_size->type = TYPE_INTEGER;
    min_segment_size->required = YES;
    min_segment_size->answer = "1";	/* default: no merges, a minimum of 1 pixel is allowed in a segment. */
    min_segment_size->options = "1-100000";
    min_segment_size->description =
	_("Minimum number of pixels (cells) in a segment.  The final merge step will ignore the threshold for any segments with fewer pixels.");

    /* optional parameters */

    diagonal = G_define_flag();
    diagonal->key = 'd';
    diagonal->description =
	_("Use 8 neighbors (3x3 neighborhood) instead of the default 4 neighbors for each pixel.");

    weighted = G_define_flag();
    weighted->key = 'w';
    weighted->description =
	_("Weighted input, don't perform the default scaling of input maps.");

    /* Raster for initial segment seeds *//* TODO polish: allow vector points/centroids for seed input. */
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

    /* TODO input for distance function */

    /* debug parameters */
    endt = G_define_option();
    endt->key = "endt";
    endt->type = TYPE_INTEGER;
    endt->required = NO;
    endt->answer = "1000";
    endt->description =
	_("Debugging...Maximum number of time steps to complete.");

    path = G_define_flag();
    path->key = 'p';
    path->description =
	_("temporary option, pathflag, select to use Rk as next Ri if not mutually best neighbors.");

    outband = G_define_standard_option(G_OPT_R_OUTPUT);
    outband->key = "final_mean";
    outband->required = NO;
    outband->description =
	_("debug - save band mean, currently implemented for only 1 band.");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* Validation */

    /* TODO: use checker for any of the data validation steps? */

    /* Check and save parameters */

    files->image_group = group->answer;

    if (G_legal_filename(output->answer) == TRUE)
	files->out_name = output->answer;	/* name of output (segment ID) raster map */
    else
	G_fatal_error("Invalid output raster name.");

    functions->threshold = atof(threshold->answer);	/* Note: this threshold is scaled after we know more at the beginning of create_isegs() */

    if (weighted->answer == FALSE &&
	(functions->threshold <= 0 || functions->threshold >= 1))
	G_fatal_error(_("threshold should be >= 0 and <= 1"));

    /* segmentation methods: 1 = region growing */
    if (strncmp(method->answer, "region_growing", 10) == 0)
	functions->method = 1;
#ifdef DEBUG
    else if (strncmp(method->answer, "io_debug", 5) == 0)
	functions->method = 0;
    else if (strncmp(method->answer, "ll_test", 5) == 0)
	functions->method = 2;
    else if (strncmp(method->answer, "seg_time", 5) == 0)
	functions->method = 3;
#endif
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
    /* TODO polish, check if function pointer or IF statement is faster */

    files->weighted = weighted->answer;	/* default/0 for performing the scaling, but selected/1 if user has weighted values so scaling should be skipped. */

    functions->calculate_similarity = &calculate_euclidean_similarity;	/* TODO add user input for this */

    files->seeds = seeds->answer;

    if (bounds->answer == NULL) {	/*no polygon constraints */
	files->bounds_map = NULL;
    }
    else {			/* polygon constraints given */
	files->bounds_map = bounds->answer;
	if ((files->bounds_mapset =
	     G_find_raster2(files->bounds_map, "")) == NULL) {
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

    if (endt->answer != NULL && atoi(endt->answer) >= 0)
	functions->end_t = atoi(endt->answer);
    else {
	functions->end_t = 1000;
	G_warning(_("invalid number of iterations, 1000 will be used."));
    }

    /* debug help */

	functions->path = path->answer;	/* default/0 for no pathflag, but selected/1 to use Rk as next Ri if not mutually best neighbors. */
    
    if (outband->answer == NULL)
	files->out_band = NULL;
    else {
	if (G_legal_filename(outband->answer) == TRUE)
	    files->out_band = outband->answer;	/* name of current means */
	else
	    G_fatal_error("Invalid output raster name for means.");
    }

    return TRUE;
}
