
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

struct files
{
    /* user parameters */
    char *image_group;

    /* region info */
    int nrows, ncols;

    /* files */
    int nbands;
    SEGMENT bands_seg, out_seg;	/* bands is for input, normal application is landsat bands, but other input can be included in the group. */
    double *bands_val;		/* array, to hold all input values at one pixel */
    int *out_val;		/* array, to hold the segment ID and processing flag(s) */
    char *out_name;		/* name of output raster map */

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


/* I think if I use function pointers, I can set up one time in the input
 * what similarity function, etc, will be used later in the processing
 * and make it easier to add additional variations later.
 */

struct functions
{
    int method;			/* Segmentation method */
    int (*find_pixel_neighbors) (int *[], int *[][]);	/*pixel, pixel_neighbors *//*TODO need to define data types for these! */

    /*based on options, such as diagonal neighbors, etc, some function pointers:
     *      calc_simularity
     */

    int num_pn;			/* number of pixel neighbors  int, 4 or 8. */

    float threshold;		/* similarity threshold */

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
int find_segment_neighbors(Ri, Rin);	/* TODO: need data structure for Ri, Rin */

/* write_output.c */
/* also currently closes files */
int write_output(struct files *);
