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

struct files
{
	/* int *band_fd, out_fd;  /* Do I need these, or is the SEGMENT enough? */
	int nbands;
	SEGMENT *bands_seg, out_seg;
	
	// naming using "bands" to follow i.smap but it doesn't need to be just landsat bands
	
	// If we want to implement the option to load directly to memory
	// instead of declaring "SEGMENT" could we declare as void
	// then assign either a SEGMENT or a matrix during the get_input procedure?

	// i.smap has this:  struct Categories output_labels;
	// I don't think I'll be using categories...
	
	// i.smap has:  char *isdata;
	// not sure yet if I'll need that
	
	//will need to add something here for the vector contsraints and for seeds
	// store those directly in RAM instead of SEGMENT library?
};


// I think if I use function pointers, I can set up one time in the input
// what similarity function, etc, will be used later in the processing
// and make it easier to add additional variations later.

struct functions
{

//based on options, such as diagonal neighbors, etc:
//	find_neighbor
//	calc_simularity
		
	//not really a function, but input to the functions
	double threshold;
};

/* get_input.c */
/* gets input from user, validates, opens files, and sets up functions */
int get_input(int, char *[], struct files *, struct functions *);

