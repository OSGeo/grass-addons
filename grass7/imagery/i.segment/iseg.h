
/****************************************************************************
 *
 * MODULE:       i.segment
 * AUTHOR(S):    Eric Momsen <eric.momsen at gmail com>
 * PURPOSE:      structure definition and function listing
 * COPYRIGHT:    (C) 2012 by Eric Momsen, and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the COPYING file that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <grass/segment.h>
#include <grass/linkm.h>
#include "flag.h"

/* pixel stack */
struct pixels
{
    struct pixels *next;
    int row;
    int col;
};

/* input and output files, as well as some other processing info */
struct files
{
    /* user parameters */
    char *image_group;
    int weighted;		/* 0 if false/not selected, so we should scale input.  1 if the scaling should be skipped */

    /* region info */
    int nrows, ncols;

    /* files *//* TODO, for all map names, is this better for any reason, saw it in manual example: char name[GNAME_MAX]; */
    char *out_name;		/* name of output raster map */
    char *seeds, *bounds_map, *bounds_mapset;	/* optional segment seeds and polygon constraints/boundaries */
    char *out_band;		/* for debug */

    /* file processing *//* TODO decide if bounds should be RAM or SEG */
    /* input values initially, then bands_seg is updated with current mean values for the segment. */
    int nbands;			/* number of rasters in the image group */
    SEGMENT bands_seg, bounds_seg;	/* bands is for input, normal application is landsat bands, but other input can be included in the group. */
    double *bands_val;		/* array, to hold all input values at one pixel */
    double *second_val;		/* to hold values at second point for similarity comparison */
    int bounds_val, current_bound;

    /* results */
    int **iseg;			/*segment ID assignment. */

    /* processing flags */
    FLAG *candidate_flag, *null_flag;	/*TODO, need some way to remember MASK/NULL values.  Was using -1, 0, 1 in int array.  Better to use 2 FLAG structures, better readibility? */
    FLAG *no_check;		/* pixels that have already been checked during this neighbor finding routine */

    /* memory management, linked lists */
    struct link_head *token;	/* for linkm linked list memory management. */

    /* other info */
    int candidate_count;	/*how many candidate pixels remain */

    /* RASTER_MAP_TYPE data_type;       Removed: input is always DCELL, output is CELL. 
     *  TODO: if input might be smaller then DCELL, we could detect size and allocate accordingly. */
    /*
     * Todo: Memory managment:
     * If we want to implement the option to load directly to memory
     * instead of declaring "SEGMENT" could we declare as void
     * then assign either a SEGMENT or a matrix during the get_input procedure?
     */

    /* TODO: some parts of the data structure from i.smap
     * confirm if there is any reason to be using them here
     * struct Categories output_labels;
     * char *isdata;
     */

    /* Todo: Additional data to be stored in this structure:
     * seeds (Put directly into output map?)
     */

};

struct functions
{
    int method;			/* Segmentation method */
    int num_pn;			/* number of pixel neighbors  int, 4 or 8. TODO: can remove if pixel neighbors is list instead of array.  But maybe this one is small enough that is faster as array? */
    float threshold;		/* similarity threshold */
	int min_segment_size;		/* smallest number of pixels/cells allowed in a final segment */
	
    /* Some function pointers to set one time in parse_args() */
    int (*find_pixel_neighbors) (int, int, int[8][2], struct files *);	/*parameters: row, col, pixel_neighbors */
    double (*calculate_similarity) (struct pixels *, struct pixels *, struct files *, struct functions *);	/*parameters: two points (row,col) to compare */

    /* for debug */
    int end_t;
};


/* parse_args.c */
/* gets input from user, validates, and sets up functions */
int parse_args(int, char *[], struct files *, struct functions *);

/* open_files.c */
int open_files(struct files *);

/* create_isegs.c */
int create_isegs(struct files *, struct functions *);
int io_debug(struct files *, struct functions *);
int ll_test(struct files *, struct functions *);
int test_pass_token(struct pixels **, struct files *);
int region_growing(struct files *, struct functions *);
int find_segment_neighbors(struct pixels **, struct pixels **, int *,
			   struct files *, struct functions *);
int set_candidate_flag(struct pixels *, int, struct files *);
int merge_values(struct pixels *, struct pixels *, int, int, struct files *);
int find_four_pixel_neighbors(int, int, int[][2], struct files *);
int find_eight_pixel_neighbors(int, int, int[8][2], struct files *);
double calculate_euclidean_similarity(struct pixels *, struct pixels *,
				      struct files *, struct functions *);
int my_dispose_list(struct link_head *, struct pixels **);

/* write_output.c */
int write_output(struct files *);
int close_files(struct files *);
