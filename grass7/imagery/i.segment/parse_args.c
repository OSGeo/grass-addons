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

    struct Option *group, *seeds, *output, *method, *threshold;	/* Establish an Option pointer for each option */
    struct Flag *diagonal;	/* Establish a Flag pointer for each option */

	/* for the opening files portion */
    struct Ref Ref;		/* group reference list */
    int *in_fd;
    RASTER_MAP_TYPE data_type;
    int n, row, col, nrows, ncols, srows, scols, inlen, outlen, nseg;
    DCELL **inbuf;  /* buffer array, to store lines from each of the imagery group rasters */
	double *inval;  /* array, to collect data from one column of inbuf to be put into segmentation file */
    char *in_file, *out_file;  /* original functions required const char, new segment_open() does not */



    group = G_define_standard_option(G_OPT_I_GROUP);

	/* deleted subgroup line, but still appears in input form */

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

    sscanf(threshold->answer, "%f", &functions->threshold);

    /* I'm assuming it is already validated as a number.  Is this OK, or is there a better way to cast the input? */
    /* r.cost line 313 
       if (sscanf(opt5->answer, "%d", &maxcost) != 1 || maxcost < 0)
       G_fatal_error(_("Inappropriate maximum cost: %d"), maxcost); */

    /* TODO: The following routines create a new raster map in the current mapset and open it for writing. G_legal_filename() should be called first to make sure that raster map name is a valid name. */

    files->out_name = output->answer;	/* name of output raster map */


    /* Open Files (file segmentation) */
    G_verbose_message("Checking image group...");
    /* references: i.cost and http://grass.osgeo.org/programming7/segmentlib.html */


    /* ****** open the input rasters ******* */

    /* TODO, this is from i.smap/openfiles.c  lines 17-23 checked if subgroup had maps, does API handles the checks? */

    if (!I_get_group_ref(group->answer, &Ref))
	G_fatal_error(_
		      ("Unable to read REF file for group <%s>"),
		      group->answer);

    if (Ref.nfiles <= 0)
	G_fatal_error(_
		      ("Group <%s> contains no raster maps"),
		      group->answer);

    /* Read Imagery Group */

    in_fd = G_malloc(Ref.nfiles * sizeof(int));
	inbuf = (DCELL **) G_malloc(Ref.nfiles * sizeof(DCELL *));
	inval = (double *) G_malloc(Ref.nfiles * sizeof(double));


    G_verbose_message("Opening input rasters...");
    for (n = 0; n < Ref.nfiles; n++) {
		inbuf[n] = Rast_allocate_d_buf();
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


	/* size of each element to be stored */
	
	inlen = sizeof(double) * Ref.nfiles;
	outlen = sizeof(int) * 2;


    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /*TODO: i.cost and i.watershed take different approaches...hardcode for now */
    /* when fine tuning, should be a power of 2 and not larger than 256 for speed reasons */
    srows = 64;
    scols = 64;

    /* TODO: make calculations for this */
    nseg = 8;


    /* ******* create temporary segmentation files ********* */
    G_verbose_message("Getting temporary file names...");
    /* Initalize access to database and create temporary files */


    in_file = G_tempfile();
    out_file = G_tempfile();

	G_debug(1, "Image size:  %d rows, %d cols", nrows, ncols);
	G_debug(1, "Segmented to tiles with size:  %d rows, %d cols", srows, scols);
	G_debug(1, "File names, in: %s, out: %s", in_file, out_file);
	G_debug(1, "Data element size, in: %d , out: %d ", inlen, outlen);
	G_debug(1, "number of segments to have in memory: %d", nseg);
	
	G_debug(1, "return code from segment_open(): %d", segment_open(files->bands_seg, in_file, nrows, ncols, srows, scols, inlen, nseg ));

/* don't seem to be getting an error code from segment_open().  Program just stops, without G_fatal_error() being called.*/
		
	/* size: reading all input bands as DCELL  TODO: could consider checking input to see if it is all FCELL or CELL, could reduce memory requirements.*/

/*	if (segment_open(files->bands_seg, in_file, nrows, ncols, srows, scols, inlen, nseg ) != 1)
		G_fatal_error("Unable to create input temporary files");
	*/
	G_debug(1, "finished segment_open(...bands_seg...)");
	
	/* TODO: signed integer gives a 2 billion segment limit, depending on how the initialization is done, this means 2 billion max input pixels. */
	if (segment_open(files->out_seg, out_file, nrows, ncols, srows, scols, outlen, nseg ) != 1)
		G_fatal_error("Unable to create output temporary files");
	
/*
int segment_open(SEGMENT *SEG, char *fname, off_t nrows, off_t ncols, int srows, int scols, int len, int nseg), open a new segment structure.

A new file with full path name fname will be created and formatted. The original nonsegmented data matrix consists of nrows and ncols. The segments consist of srows by scols. The data items have length len bytes. The number of segments to be retained in memory is given by nseg. This routine calls segment_format() and segment_init(), see below. If segment_open() is used, the routines segment_format() and segment_init() must not be used.
*/

    /* load input bands to segment structure */
    G_verbose_message("Reading input rasters into temporary data files...");

    for (row = 0; row < nrows; row++) {
		for (n = 0; n < Ref.nfiles; n++) {
			Rast_get_d_row(in_fd[n], inbuf[n], row);
		}
		for (col = 0; col < ncols; col++) {
			for (n = 0; n < Ref.nfiles; n++){
				inval[n] = inbuf[n][col];
			}
		   segment_put(files->bands_seg, (void *)inval, row, col);
		}
    }

    /* Don't need to do anything else for the output segmentation file?  It is initialized to zeros and will be written to later... */

    /* Free memory */

    for (n = 0; n < Ref.nfiles; n++) {
	Rast_close(in_fd[n]);
    }

    G_free(inbuf);
    G_free(in_fd);


    /* Need to clean up anything else?  Need to close segmentation files?  Or they should be open still since they will be used later?  Close after all processing is done? */

    /*
       from r.cost
       unlink(in_file); *//* remove submatrix files  */

    return 0;
}
