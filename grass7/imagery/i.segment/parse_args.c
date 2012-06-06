/* PURPOSE:      Parse and validate the input */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "iseg.h"

int parse_args(int argc, char *argv[], struct files *files,
	       struct functions *functions)
{
    /* reference: http://grass.osgeo.org/programming7/gislib.html#Command_Line_Parsing */

    struct Option *group, *seeds, *output, *method, *threshold;	/* Establish an Option pointer for each option */
    struct Flag *diagonal;	/* Establish a Flag pointer for each option */

    group = G_define_standard_option(G_OPT_I_GROUP);

    /* TODO: OK to require the user to create a group?  Otherwise later add an either/or option to give just a single raster map... */

    /* Using raster for seeds, Low priority TODO: allow vector points/centroids seed input. */
    seeds = G_define_standard_option(G_OPT_R_INPUT);
    seeds->key = "seeds";
    seeds->type = TYPE_STRING;
    seeds->required = NO;
    seeds->description = _("Optional raster map with starting seeds.");

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    method = G_define_option();
    method->key = "method";
    method->type = TYPE_STRING;
    method->required = NO;
    method->answer = "region_growing";
    method->options = "region_growing, io_debug";
    method->description = _("Segmentation method.");

    threshold = G_define_option();
    threshold->key = "threshold";
    threshold->type = TYPE_DOUBLE;
    threshold->required = YES;
    threshold->description = _("Similarity threshold.");

    diagonal = G_define_flag();
    diagonal->key = 'd';
    diagonal->description =
	_("Use 8 neighbors (3x3 neighborhood) instead of the default 4 neighbors for each pixel.");


    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    G_debug(1, "For the option <%s> you chose: <%s>",
	    group->description, group->answer);

    G_debug(1, "For the option <%s> you chose: <%s>",
	    seeds->description, seeds->answer);

    G_debug(1, "For the option <%s> you chose: <%s>",
	    output->description, output->answer);

    G_debug(1, "For the option <%s> you chose: <%s>",
	    method->description, method->answer);

    G_debug(1, "For the option <%s> you chose: <%s>",
	    threshold->description, threshold->answer);

    G_debug(1, "The value of the diagonal flag is: %d", diagonal->answer);

    /* Validation */

    /* use checker for any of the data validation steps!? */

    /* ToDo The most important things to check are if the
       input and output raster maps can be opened (non-negative file
       descriptor). */


    /* Check and save parameters */
	
	files->image_group = group->answer;
	
    sscanf(threshold->answer, "%f", &functions->threshold);

    /* TODO: I'm assuming it is already validated as a number.  Is this OK, or is there a better way to cast the input? */
    /* reference r.cost line 313 
       if (sscanf(opt5->answer, "%d", &maxcost) != 1 || maxcost < 0)
       G_fatal_error(_("Inappropriate maximum cost: %d"), maxcost); */

	if (G_legal_filename(output->answer)==1)
		files->out_name = output->answer;	/* name of output raster map */
	else
		G_fatal_error("Invalid output raster name.");


    return 0;
}
