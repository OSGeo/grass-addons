
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

/* DEBUG will add some additional testing options to the segmentation method drop down.
 * it also add some while loops that just have G_debug statements in them. */
/* #define DEBUG */

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

    /* files */
    char *out_name;		/* name of output raster map */
    const char *seeds, *bounds_map;
    const char *bounds_mapset;	/* optional segment seeds and polygon constraints/boundaries */
    char *out_band;		/* for debug */

    /* file processing */
    /* bands_seg is initialized with the input raster valuess, then is updated with current mean values for the segment. */
    int nbands;			/* number of rasters in the image group */
    SEGMENT bands_seg, bounds_seg;	/* bands is for input, normal application is landsat bands, but other input can be included in the group. */
    double *bands_val;		/* array, to hold all input values at one pixel */
    double *second_val;		/* to hold values at second point for similarity comparison */
    int bounds_val, current_bound;
    int minrow, maxrow, mincol, maxcol;

    /* results */
    int **iseg;			/* segment ID assignment */
    int nsegs;			/* number of segments */

    /* processing flags */
    FLAG *candidate_flag, *null_flag, *orig_null_flag;

    /* memory management, linked lists */
    struct link_head *token;	/* for linkm.h linked list memory management. */

    /* other info */
    int candidate_count;	/*Number of remaining candidate pixels */

};

struct functions
{
    int method;			/* Segmentation method */
    int num_pn;			/* number of pixel neighbors  int, 4 or 8. */
    float threshold;		/* similarity threshold */
    int min_segment_size;	/* smallest number of pixels/cells allowed in a final segment */

    /* Some function pointers to set one time in parse_args() */
    int (*find_pixel_neighbors) (int, int, int[8][2], struct files *);	/*parameters: row, col, pixel_neighbors */
    double (*calculate_similarity) (struct pixels *, struct pixels *, struct files *, struct functions *);	/*parameters: two points (row,col) to compare */

    /* max number of iterations/passes */
    int end_t;

    /* todo remove when decide on pathflag */
    int path;
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
int seg_speed_test(struct files *, struct functions *);
int get_segID_SEG(struct files *, int, int);
int get_segID_RAM(struct files *, int, int);
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
int compare_ids(const void *, const void *);
int compare_pixels(const void *, const void *);
int set_all_candidate_flags(struct files *);

/* write_output.c */
int write_output(struct files *);
int close_files(struct files *);
