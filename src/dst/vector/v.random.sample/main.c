/* s.random.sample */
/* Generate a random subset of vector points. */

/* TODO 
   - specifying -a automatically disregards the map as well.
   Is that good behaviour?
 */

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <math.h>
#include <time.h>
#include <sys/types.h>
#include <unistd.h>

#include <grass/gis.h>
#include <grass/Vect.h>

#include "gt/rowcache.h"

#define PROGVERSION 1.1

extern int errno;
int cachesize;

int debug_mode = 0;		/* 1 to enable writing debug output to logfile */

/* checks if user-supplied parameters are valid */
int
check_parms(char *map_answer, char *input_answer, char *output_answer,
	    int all)
{

    if (map_answer != NULL) {
	if ((G_find_file("fcell", map_answer, "") == NULL)
	    && (G_find_file("dcell", map_answer, "") == NULL)
	    && (G_find_file("cell", map_answer, "") == NULL)) {
	    /* no coverage map found */
	    G_fatal_error("No raster map exists with the given name.");
	}

	/* specifying all means to disregard the map! */
	if (all == 1) {
	    G_warning
		("Map was specified, but the -a flag disregards map values!\n Your results might not be what you expect.");
	}
    }

    /* check if sample sites exist */
    if (G_find_file("vector", input_answer, "") == NULL) {
	G_fatal_error("No sample/sites list exists with the given name!");
    }

    /* check if a legal file name was given for output map
       this just overwrites existing sites */
    if (G_legal_filename(output_answer) == -1) {
	G_fatal_error("Name chosen for result map is not a valid file name!");
    }

    /* return raster mode to caller */
    if (map_answer != NULL) {
	return (G_raster_map_type(map_answer, ""));
    }
    else
	return (-1);
}


/* creates a vector site file in the user's mapset that contains */
/* 'percentage' objects randomly picked from input map */
/* useful to create randomised samples for statistical tests */
void do_split_sample(char *input, char *output, int in_types,
		     double percentage, char *map, int all,
		     int processing_mode, int quiet)
{
    CELL *cellbuf;
    DCELL *dcellbuf;
    GT_Row_cache_t *cache;
    int fd;
    int i, j, k, l;
    int no_sites;
    int sites_tried = 0;
    struct Cell_head region;
    int error;
    char *mapset, errmsg[200];
    unsigned int *taken;	/* this is an array of 0/1 which signals, if
				   a certain site has already been 'drawn' */
    long row_idx, col_idx;
    struct Map_info in_vect_map;
    struct Map_info out_vect_map;
    struct line_pnts *vect_points;
    struct line_cats *vect_cats;
    double x, y, z;
    int n_points = 1;
    int cur_type;


    cellbuf = NULL;
    dcellbuf = NULL;
    cache = NULL;

    /* get current region */
    G_get_window(&region);


    /* attempt to create new file for output */
    Vect_set_open_level(2);
    if (0 > Vect_open_new(&out_vect_map, output, 0)) {
	G_fatal_error("Could not open output vector map.\n");
    }

    /* open input vector map */
    if ((mapset = G_find_vector2(input, "")) == NULL) {
	sprintf(errmsg, "Could not find input %s\n", input);
	G_fatal_error("%s", errmsg);
    }

    if (1 > Vect_open_old(&in_vect_map, input, "")) {
	sprintf(errmsg, "Could not open input map %s.\n", input);
	G_fatal_error("%s", errmsg);
    }

    vect_points = Vect_new_line_struct();
    vect_cats = Vect_new_cats_struct();

    /* set constraints specified */
    if (in_types != 0) {
	Vect_set_constraint_type(&in_vect_map, in_types);
    }
    if (all != 1) {
	Vect_set_constraint_region(&in_vect_map, region.north, region.south,
				   region.east, region.west, 0.0, 0.0);
    }


    /* get total number of objects with constraints */
    i = 0;
    while ((cur_type =
	    Vect_read_next_line(&in_vect_map, vect_points, vect_cats) > 0)) {
	i++;
    }

    k = (((float)i / 100)) * percentage;	/* k now has the number of objects wanted */

    if (quiet != 1) {
	fprintf(stderr, "Creating randomised sample of size n = %i.\n", k);
    }

    /* now, we need to acquire exactly 'k' random objects that fall in NON-NULL */
    /* coverage raster cells. */
    taken = G_calloc(i, sizeof(unsigned int));
    for (l = 0; l < k; l++) {
	taken[l] = 0;
    }
    no_sites = i;		/* store this for later use */

    /* does user want to filter objects through a raster map? */
    if (map != NULL) {
	/* open raster map */
	fd = G_open_cell_old(map, G_find_cell(map, ""));
	if (fd < 0) {
	    G_fatal_error("Could not open raster map for reading!\n");
	}
	/* allocate cache and buffer, according to type of coverage */
	if (processing_mode == CELL_TYPE) {
	    /* INT coverage */
	    cache = (GT_Row_cache_t *) G_malloc(sizeof(GT_Row_cache_t));
	    /* TODO: check error value */
	    error = GT_RC_open(cache, cachesize, fd, CELL_TYPE);
	    cellbuf = G_allocate_raster_buf(CELL_TYPE);
	}
	if ((processing_mode == FCELL_TYPE) ||
	    (processing_mode == DCELL_TYPE)) {
	    /* FP coverage */
	    cache = (GT_Row_cache_t *) G_malloc(sizeof(GT_Row_cache_t));
	    /* TODO: check error value */
	    error = GT_RC_open(cache, cachesize, fd, DCELL_TYPE);
	    dcellbuf = G_allocate_raster_buf(DCELL_TYPE);
	}
    }

    srand(((unsigned int)time(NULL)) + getpid());	/* set seed for random number generator from system time and process ID */
    i = 0;

    /* MAIN LOOP */
    while (i < k) {
	/* get a random index, but one that was not taken already */
	l = 0;
	while (l == 0) {
	    j = rand() % (no_sites - 1 + 1) + 1;	/* j now has the random position to try */
	    if (taken[j - 1] == 0) {
		l = 1;		/* exit loop */
	    }
	}
	taken[j - 1] = 1;	/* mark this index as 'taken' */
	sites_tried++;		/* keep track of this so we do not enter an infinite loop */
	if (sites_tried > no_sites) {
	    /* could not create a large enough sample */
	    G_fatal_error
		("Could not find enough objects for split sampling.\nDecrease split sample size.\n");
	}
	/* get next vector object */
	cur_type = Vect_read_line(&in_vect_map, vect_points, vect_cats, j);
	if (cur_type < 0) {
	    G_fatal_error("Error reading vector map: premature EOF.\n");
	}
	/* now, check if coverage under site is NON-NULL and within region */
	/* convert site northing to row! */
	/* for this check, we use only the first pair of coordinates! */
	Vect_copy_pnts_to_xyz(vect_points, &x, &y, &z, &n_points);
	row_idx = (long)G_northing_to_row(y, &region);

	col_idx = (long)G_easting_to_col(x, &region);
	/* do region check, first... OBSOLETE */
	/* read row from cache and check for NULL */
	/* if required */
	if (map != NULL) {
	    if (processing_mode == CELL_TYPE) {
		cellbuf = GT_RC_get(cache, row_idx);
		if (!G_is_c_null_value(&cellbuf[col_idx])) {
		    i++;
		    Vect_write_line(&out_vect_map, cur_type,
				    vect_points, vect_cats);
		    fflush(stdout);
		}
	    }
	    if ((processing_mode == FCELL_TYPE) ||
		(processing_mode == DCELL_TYPE)) {
		dcellbuf = GT_RC_get(cache, row_idx);
		if (!G_is_d_null_value(&dcellbuf[col_idx])) {
		    i++;
		    Vect_write_line(&out_vect_map, cur_type,
				    vect_points, vect_cats);
		    fflush(stdout);
		}
	    }
	}
	else {
	    i++;
	    Vect_write_line(&out_vect_map, GV_POINT, vect_points, vect_cats);
	    fflush(stdout);
	}
	/* disregard region setting and map, if -a flag is given */
	if (all == 1) {
	    i++;
	    Vect_write_line(&out_vect_map, cur_type, vect_points, vect_cats);
	    fflush(stdout);
	}

	if (quiet != 1) {
	    G_percent(i, k, 1);
	}
    }
    /* END OF MAIN LOOP */
    Vect_copy_head_data(&in_vect_map, &out_vect_map);
    fprintf(stdout, "Building topology information for output map.\n");
    Vect_build(&out_vect_map);
    Vect_close(&in_vect_map);
    Vect_close(&out_vect_map);

    if (map != NULL) {
	/* close cache, free buffers! */
	GT_RC_close(cache);
	if (processing_mode == CELL_TYPE) {
	    G_free(cellbuf);
	}
	if ((processing_mode == FCELL_TYPE) ||
	    (processing_mode == DCELL_TYPE)) {
	    G_free(dcellbuf);
	}
	G_free(cache);
    }
}


int main(int argc, char *argv[])
{
    struct GModule *module;
    struct
    {
	struct Option *input;	/* name of input site map */
	struct Option *output;	/* name of output site map */
	struct Option *type;
	struct Option *where;
	struct Option *size;	/* size of sample (%input) */
	struct Option *map;	/* optional raster to check for NULL */
	struct Option *cachesize;
    }
    parm;
    struct
    {
	struct Flag *quiet;
	struct Flag *all;	/* disregard region settings */
    }
    flag;
    int processing_mode = 0;
    int vect_types;

    /* setup some basic GIS stuff */
    G_gisinit(argv[0]);
    module = G_define_module();
    module->description =
	"Generates a random sample from a map of vector objects";
    /* do not pause after a warning message was displayed */
    G_sleep_on_error(0);


    /* Module Parameters: */

    parm.input = G_define_standard_option(G_OPT_V_INPUT);
    parm.input->key = "input";
    parm.input->type = TYPE_STRING;
    parm.input->required = YES;
    parm.input->description = "Vector map to draw sample from";

    /* name of output map */
    parm.output = G_define_standard_option(G_OPT_V_OUTPUT);
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->description = "Vector map to store random sample in";

    /* type of objects */
    parm.type = G_define_standard_option(G_OPT_V_TYPE);

    /* filter objects by sql statement */
    parm.where = G_define_standard_option(G_OPT_WHERE);

    /* percentage of input objects to include for random sample */
    parm.size = G_define_option();
    parm.size->key = "size";
    parm.size->type = TYPE_DOUBLE;
    parm.size->required = YES;
    parm.size->description = "Size of the sample (% of input vector objects)";
    parm.size->options = "0-100";

    /* map = an optional raster map. Samples will not be generated */
    /*       in cells where this map fprintf (stderr, "HI\n");is NULL */
    parm.map = G_define_standard_option(G_OPT_R_INPUT);
    parm.map->key = "raster";
    parm.map->type = TYPE_STRING;
    parm.map->required = NO;
    parm.map->description =
	"Sampling cannot be done on NULL cells in this raster map";

    /* number of lines to store in cache */
    parm.cachesize = G_define_option();
    parm.cachesize->key = "cachesize";
    parm.cachesize->type = TYPE_INTEGER;
    parm.cachesize->answer = "-1";
    parm.cachesize->required = NO;
    parm.cachesize->description =
	"Number of raster rows to store in cache (-1 for auto)";

    flag.all = G_define_flag();
    flag.all->key = 'a';
    flag.all->description = "Sample outside the current region's limits";

    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = "Quiet operation: no progress display";

    /* parse command line */
    if (G_parser(argc, argv)) {
	exit(-1);
    }

    vect_types = Vect_option_to_types(parm.type);

    /* check if given parameters are valid */
    processing_mode =
	check_parms(parm.map->answer, parm.input->answer, parm.output->answer,
		    flag.all->answer);

    if (parm.map->answer != NULL) {
	/* set cachesize */
	cachesize = atoi(parm.cachesize->answer);
	if ((cachesize < -1) || (cachesize > G_window_rows())) {
	    /* if cache size is invalid, just set to auto-mode (-1) */
	    G_warning
		("Invalid cache size requested (must be between 0 and %i or -1).\n",
		 G_window_rows());
	    cachesize = -1;
	}
    }

    do_split_sample(parm.input->answer, parm.output->answer, vect_types,
		    atof(parm.size->answer), parm.map->answer,
		    flag.all->answer, processing_mode, flag.quiet->answer);

    return (EXIT_SUCCESS);
}
