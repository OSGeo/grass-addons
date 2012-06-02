/* PURPOSE:      Parse and validate the input, including opening input rasters and creating segmentation files */

#include <stdlib.h>
#include <string.h>
#include <fcntl.h>		/* needed for creat and open for the segmentation files.
				   used those functions per the programmer's manual, correct usage? */
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int parse_args(int argc, char *argv[], struct files *files,
	       struct functions *functions)
{
    /* reference: http://grass.osgeo.org/programming7/gislib.html#Command_Line_Parsing */

    struct Option *group, *subgroup, *seeds, *output, *method, *threshold;	/* Establish an Option pointer for each option */
    struct Flag *diagonal;	/* Establish a Flag pointer for each option */

    group = G_define_standard_option(G_OPT_I_GROUP);

    subgroup = G_define_standard_option(G_OPT_I_SUBGROUP);

    /* OK to require the user to create a group?  Otherwise later add an either/or option to give just a single raster map... */

    //~ input = G_define_standard_option(G_OPT_R_INPUT);   /* Request a pointer to memory for each option */
    //~ input->key = "input"; /* TODO: update to allow groups.  Maybe this needs a group/subgroup variables, or we can check if the input is group/subgroup/raster */
    //~ input->type = TYPE_STRING;
    //~ input->required = YES;
    //~ input->description = _("Raster map to be segmented.");

    /* Using raster for seeds, maybe consider allowing vector points/centroids later. */
    seeds = G_define_standard_option(G_OPT_R_INPUT);
    seeds->key = "seeds";
    seeds->type = TYPE_STRING;
    seeds->required = NO;
    seeds->description = _("Optional raster map with starting seeds.");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    //seems API handles this part ?
    //~ output->key = "output";
    //~ output->type = TYPE_STRING;
    //~ output->required = YES;
    //~ output->description = _("Name of output raster map.");

    //TODO: when put in a new raster map, error message:
    //~ Command 'd.rast map=testing@samples' failed
    //~ Details: Raster map <testing@samples> not found

    //Also, that error seems to be accumulated, putting in a new output map names results in:
    //~ Command 'd.rast map=testing@samples' failed
    //~ Details: Raster map <testing@samples> not found
    //~ Command 'd.rast map=test2@samples' failed
    //~ Details: Raster map <test2@samples> not found

    method = G_define_option();
    method->key = "method";
    method->type = TYPE_STRING;
    method->required = NO;
    method->answer = _("region_growing");
    method->options = "region_growing, mean_shift";
    method->description = _("Segmentation method.");

    threshold = G_define_option();
    threshold->key = "threshold";
    threshold->type = TYPE_DOUBLE;
    threshold->required = YES;
    threshold->description = _("Similarity threshold.");

    diagonal = G_define_flag();
    diagonal->key = 'd';
    diagonal->description =
	_
	("Use 8 neighbors (3x3 neighborhood) instead of the default 4 neighbors for each pixel.");


    //~ G_debug(1, "testing debug!");
    //~ When put this in, get an error (only when DEBUG is set, if not set, it runs fine)
    //~ 
    //~ Error box:
    //~ Unable to fetch interface description for command 'i.segment'.
    //~ Details: D1/1: testing debug!

    //~ G_debug(1, "For the option <%s> you chose: <%s>",
    //~ input->description, input->answer);
    //~ 
    //~ G_debug(1, "For the option <%s> you chose: <%s>",
    //~ seeds->description, seeds->answer);
    //~ 
    //~ G_debug(1, "For the option <%s> you chose: <%s>",
    //~ output->description, output->answer);
    //~ 
    //~ G_debug(1, "For the option <%s> you chose: <%s>",
    //~ method->description, method->answer);
    //~ 
    //~ G_debug(1, "For the option <%s> you chose: <%s>",
    //~ threshold->description, threshold->answer);
    //~ 
    //~ G_debug(1, "The value of the diagonal flag is: %d", diagonal->answer);


    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* Validation */

    /* use checker for any of the data validation steps!? */

    /* ToDo The most important things to check are if the
       input and output raster maps can be opened (non-negative file
       descriptor). */


    /* Check and save parameters */

    sscanf(threshold->answer, "%f", &functions->threshold);

    /* I'm assuming it is already validated as a number.  Is this OK, or is there a better way to cast the input? */
    /* r.cost line 313 
       if (sscanf(opt5->answer, "%d", &maxcost) != 1 || maxcost < 0)
       G_fatal_error(_("Inappropriate maximum cost: %d"), maxcost); */

    /* TODO: The following routines create a new raster map in the current mapset and open it for writing. G_legal_filename() should be called first to make sure that raster map name is a valid name. */

    files->out_name = output->answer;	/* name of output raster map */


    /* Open Files (file segmentation) */
    G_verbose_message("Checking image (sub)group...");
    /* references: i.cost and http://grass.osgeo.org/programming7/segmentlib.html */


    struct Ref Ref;		/* subgroup reference list */
    int *in_fd, *seg_in_fd, seg_out_fd;
    RASTER_MAP_TYPE data_type;
    int n, row, nrows, ncols, srows, scols, seg_in_mem;
    void *inbuf;
    const char *in_file[10], *out_file;	/* max 10 rasters in imagery group, until figure out how to do this dynamically */

    /* int buf[NCOLS]; */
    /* c question... will using void data type be the right way, until I know what the data type is? */
    /* that was in the developer's manual... but would void *buf also work? */
    /* void *buf; *//* for copying from raster into segmentation file */


    /* ****** open the input rasters ******* */

    /* i.smap/openfiles.c  lines 17-23 checked if subgroup had maps, does API handles the checks?
       can no subgroup be entered, just a group? */

    if (!I_get_subgroup_ref(group->answer, subgroup->answer, &Ref))
	G_fatal_error(_
		      ("Unable to read REF file for subgroup <%s> in group <%s>"),
		      subgroup->answer, group->answer);

    if (Ref.nfiles <= 0)
	G_fatal_error(_
		      ("Subgroup <%s> in group <%s> contains no raster maps"),
		      subgroup->answer, group->answer);

    /* open input group maps for reading */

    in_fd = G_malloc(Ref.nfiles * sizeof(seg_out_fd));	/* need sizeof( integer ) */

    G_verbose_message("Opening input rasters...");
    for (n = 0; n < Ref.nfiles; n++) {
	in_fd[n] = Rast_open_old(Ref.file[n].name, Ref.file[n].mapset);
    }


    /* ********** find out file segmentation size ************ */
    G_verbose_message("Calculate temp file sizes...");

    /*loop again... need to get largest option
       //for today assume all are the same
       //data_type = Rast_get_map_type(in_fd[n]); */
    files->nbands = Ref.nfiles;

    data_type = Rast_get_map_type(in_fd[0]);
    files->data_type = data_type;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /*TODO: i.cost and i.watershed take different approaches...
       //hardcode for now */
    srows = nrows / 8;
    scols = ncols / 8;

    /* TODO: make calculations for this */
    seg_in_mem = 4;

    /*    G_debug(1, "  %d rows, %d cols", nrows, ncols); ... never tried this, just copied from other module */


    /* ******* create temporary segmentation files ********* */
    G_verbose_message("Getting temp file names...");
    /* Initalize access to database and create temporary files */


    for (n = 0; n < Ref.nfiles; n++) {
	in_file[n] = G_tempfile();
    }
    out_file = G_tempfile();

    /* Format segmented files */

    seg_in_fd = G_malloc(Ref.nfiles * sizeof(seg_out_fd));	/* need sizeof( integer ) */
    G_verbose_message("Creating temporary data files...");
    for (n = 0; n < Ref.nfiles; n++) {
	seg_in_fd[n] = creat(&in_file[n], 0666);
	if (segment_format(seg_in_fd[n], nrows, ncols, srows, scols, sizeof(data_type)) != 1)	/* TODO: this data_type should be from each map */
	    G_fatal_error("can not create temporary file");
	close(seg_in_fd[n]);	/* why close when we just reopen again?  Different access mode between creat and open ? */
    }
    seg_out_fd = creat(out_file, 0666);
    if (segment_format
	(seg_out_fd, nrows, ncols, srows, scols, sizeof(data_type)) != 1)
	G_fatal_error("can not create temporary file");
    close(seg_out_fd);


    /* Open and initialize all segment files */
    G_debug(1, "Initializing temporary data files...");	/* program dies sometime after this point, and before line 234 */
    for (n = 0; n < Ref.nfiles; n++) {
	seg_in_fd[n] = open(&in_file[n], 2);	/* TODO: second parameter here is different in many places... */
	if (segment_init(&files->bands_seg[n], seg_in_fd[n], seg_in_mem) != 1)
	    G_fatal_error("can not initialize temporary file");
    }
    seg_out_fd = open(out_file, 2);
    if (segment_init(&files->out_seg, seg_out_fd, seg_in_mem) != 1)
	G_fatal_error("can not initialize temporary file");

    /* convert flat files to segmented files */
    G_verbose_message("Read input rasters into temporary data files...");
    inbuf = Rast_allocate_buf(data_type);	/* buffer from the raster file */

    /* buf = new data_type [ncols] *//* buffer to read data into, cell by cell.  But can I just write inbuf directly to the segmentation file??? */

    for (n = 0; n < Ref.nfiles; n++) {
	for (row = 0; row < nrows; row++) {
	    Rast_get_row(in_fd[n], inbuf, row, data_type);
	    //~ for (col = 0; col < ncols; col++)
	    //~ {
	    //~ /*fill buf */
	    //~ // G_incr_void_ptr
	    //~ }

	    segment_put_row(&files->bands_seg[n], inbuf, row);
	}
    }

    /* Don't need to do anything else for the output segmentation file?  It is initialized to zeros and will be written to later... */

    /* Free memory */

    for (n = 0; n < Ref.nfiles; n++) {
	Rast_close(in_fd[n]);
    }

    G_free(inbuf);
    G_free(in_fd);
    G_free(seg_in_fd);

    /* Need to clean up anything else?  Need to close segmentation files?  Or they should be open still since they will be used later?  Close after all processing is done? */

    /*
       from r.cost
       unlink(in_file); *//* remove submatrix files  */

    return 0;
}
