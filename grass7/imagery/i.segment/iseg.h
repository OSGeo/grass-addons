
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

struct files
{
    /* user parameters */
    char *image_group;

    /* region info */
    int nrows, ncols;

    /* files */
    int nbands;
    int candidate_count;	/*how many candidate pixels remain */
    SEGMENT bands_seg, out_seg;	/* bands is for input, normal application is landsat bands, but other input can be included in the group. */
    double *bands_val;		/* array, to hold all input values at one pixel */
    double *second_val;		/* to hold values at second point for similarity comparison */
    int *out_val;		/* array, to hold the segment ID and processing flag(s) */
    char *out_name;		/* name of output raster map */

    SEGMENT no_check;		/* pixels that have already been checked during this neighbor finding routine */

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
     * vector constraints
     * seeds (Put directly into output map?)
     * Need to consider if they should be put in RAM or SEGMENT?
     */

};

struct functions
{
    int method;			/* Segmentation method */

    /* Some function pointers to set one time in parse_args() */
    int (*find_pixel_neighbors) (int, int, int[8][2], struct files *);	/*parameters: row, col, pixel_neighbors */
    double (*calculate_similarity) (int[2], int[2], struct files *,	/*parameters: two points (row,col) to compare */
				    struct functions *);

    int num_pn;			/* number of pixel neighbors  int, 4 or 8. TODO: can remove if pixel neighbors is list instead of array.  But maybe this one is small enough that is faster as array? */
    float threshold;		/* similarity threshold */

};

/* pixel stack */
struct pixels
{
    int row;
    int col;
    struct pixels *next;
};

/* parse_args.c */
/* gets input from user, validates, and sets up functions */
int parse_args(int, char *[], struct files *, struct functions *);

/* open_files.c */
int open_files(struct files *);

/* create_isegs.c */
int create_isegs(struct files *, struct functions *);
int io_debug(struct files *, struct functions *);
int region_growing(struct files *, struct functions *);
int find_segment_neighbors(int[][2], struct pixels *, int *, struct files *, struct functions *, VOID_T *);	/* TODO: need data structure for Ri, Rin */
int set_candidate_flag(int[100][2], int, int, struct files *);
int merge_values(int[100][2], int[100][2], int, int, struct files *);	/* I assume this is a weighted mean? */
int find_four_pixel_neighbors(int, int, int[][2], struct files *);
int find_eight_pixel_neighbors(int, int, int[8][2], struct files *);
double calculate_euclidean_similarity(int[2], int[2], struct files *,
				      struct functions *);


/* write_output.c */
int write_output(struct files *);
int close_files(struct files *);
