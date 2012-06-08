/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <float.h>		/* to get value of LDBL_MAX -> change this if there is a more usual grass way */
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include "iseg.h"

int create_isegs(struct files *files, struct functions *functions)
{

    int successflag = 1;

    /* method specific parameter set up and memory allocation */

    if (functions->method == 1) {	/*region growing */

	/* nothing yet */
    }

    /*TODO: implement outer loop to process polygon interior, then all remaining pixels */
    /* This loop could go in here, or outside in main (only make segmentation file for what is currently being processed.) */

    G_debug(1, "Threshold: %g", functions->threshold);
    G_debug(1, "segmentation method: %d", functions->method);


    if (functions->method == 0)
	successflag = io_debug(files, functions);
    else if (functions->method == 1)
	successflag = region_growing(files, functions);

    if (successflag != 0)
	G_fatal_error("Error creating segments");

    /* end outer loop for processing polygons */

    /* clean up */

    /* should there be a free() for every malloc?  Or only the large ones? */

    return 0;
}

int io_debug(struct files *files, struct functions *functions)
{
    int row, col;

    /* **************write fake data to test I/O portion of module */

    G_verbose_message("writing fake data to segmentation file");
    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);	/*this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    files->out_val[0] = col + row;
	    files->out_val[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)files->out_val, row, col);
	}
    }

    /* TODO: free memory */

    return 0;
}


int region_growing(struct files *files, struct functions *functions)
{
    int row, col, n, t, pixel_neighbors[8][2];	/* could dynamically declare to be only 4 or 8 elements, but this is shorter for now */
    double threshold, Ri_simularity, Rk_simularity, tempsim;
    int endflag;		/* =1 if there were no merges on that processing iteration */
    int pathflag;		/* =1 if we didn't find mutual neighbors, and should continue with Rk */
    int mergeflag;		/* =1 if we have mutually agreeing best neighbors */

    /* Ri = current focus segment
     * Rk = Ri's most similar neighbor
     * Rkn = Rk's neighbors
     * Rin = Ri's neigbors (as pixels or segments ?!?
     */

    G_verbose_message("Running region growing algorithm");

    t = 0;

    do {
	/* for loop on t to slowly lower threshold. also check that endflag=0 */

	threshold = functions->threshold;	/* when implement t loop, this will be a function of t. */

	endflag = 1;


	/* Set candidate flag to true/1 for all pixels TODO: for polygon group, need to just set to true for those being processed */

	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
		segment_get(&files->out_seg, (void *)files->out_val, row, col);	/*need to get, since we only want to change the flag, and not overwrite the segment value. */
		/* TODO: if we are starting from seeds...and only allow merges between unassigned pixels
		 *  and seeds/existing segments, then this needs an if (and will be very inefficient)
		 * maybe consider the sorted array, btree, map... but the number of seeds could still be high for a large map */
		files->out_val[1] = 1;	/*candidate pixel flag */
		segment_put(&files->out_seg, (void *)files->out_val, row,
			    col);
	    }
	}

	/*process candidate pixels */

	/*check each pixel, start the processing only if it is a candidate pixel */
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
		segment_get(&files->out_seg, (void *)files->out_val, row,
			    col);
		if (files->out_val[1] == 1) {	/* out_val[1] is the candidate pixel flag */

		    /*TODO: need to empty/reset Ri, Rn, and Rk */
		    Ri = Rin = Rk = Rkn = NULL;

		    pathflag = 1;

		    while (pathflag == 1) {	/*if don't find mutual neighbors on first try, will use Rk as next Ri. */

			if (find_segment_neighbors(Ri, Rin) != 0) {
			    G_debug(1, "Couldn't find neighbors");	/*this could happen if there is a pixel surrounded by pixels that have already been processed */
			    pathflag = 0;
			    set candidate flag to false for this pixel;
			}
			else {	/*found neighbors, go ahead until find mutually agreeing neighbors */

			    /* find Ri's most similar neighbor */
			    Ri_similarity
				= LDBL_MAX;

			    for (each Rin) {
				tempsim = calculate_simularity(Ri, one neighbor);	/*set up as function pointer... */
				if tempsim
				    <Ri_similarity {
				    Ri_similarity = tempsim;
				    Rk = current neighbor;
				    }
			    }

			    if (Rk != null(need correct null finding !) AND Ri_similarity < threshold) {	/* small TODO: should this be < or <=? */

				Rkn = Ri;	/* we know Ri should be a neighbor of Rk *//*Todo: is there a way to skip similarity calculations on these?  keep a count, and pop them before doing the similarity check? */
				find_segment_neighbors(Rk, Rkn);	/* data structure for Rk's neighbors, and pixels in Rk if we don't already have it */

				/*find Rk's most similar neighbor */
				Rk_similarity = Ri_simularity;	/*Ri gets first priority - ties won't change anything, so we'll accept Ri and Rk as mutually best neighbors */

				for (each Rkn) {
				    tempsim =
					calculate_similarity(Rk,
							     one neighbor);
				    if (tempsim < Rk_similarity) {
					Rk_similarity = tempsim;
					break;	/* exit loop here, we know that Ri and Rk aren't mutually best neighbors */
				    }
				}

				if (Rk_similarity == Ri_simularity) {	/* so they agree, both are mutually most similar neighbors */
				    /* put these steps in merge_segments(Ri, Rk) function?  */
				    update segment values for all pixels in Ri + Rk(mean)	/* I assume this is a weighted mean? */
					set candidate flag to false for all pixels in Ri + Rk	/* do this at the same time, so there is only one segment_put statement */
					  endflag = 0;	/* we've made at least one merge, so need another iteration */

				    pathflag = 0;	/* go to next row,column pixel - end of Rk -> Ri chain since we found neighbors */
				}
				else {	/* they weren't mutually best neighbors */
				    set candidate flag to false for all pixels in Ri;	/* TODO !!!!!!!!!!!! hmm, maybe this raster should be its own data structure */

				    Rk
					= Ri;	/* note, this is the eCognition technique.  Seems this is a bit faster, we already have segment membership pixels */
				}
			    }	/*end if Rk exists and < threshold */
			}	/* end else - Ri did have neighbors */
		    }		/*end pathflag do loop */
		}		/*end if pixel is candidate pixel */
	    }			/*next column */
	}			/*next row */

	/* finished one pass for processing candidate pixels */

	t++;
    } while (endflag == 0);
    /*end t loop */

    /* TODO: free memory */

    return 0;
}

int find_segment_neighbors(Ri, Rin)
{

    /* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
     * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
     * But the list of points would NOT be inclusive - just the points bordering the current segment...
     */


    /* Ri could be single pixel or list of pixels. */
    /* Rin could have a list already, or could be empty ?  Or just the head?  */

    /*local data structures... but maybe they should be allocated out in the main function, is it really slow to create/free on each pass? */

    /* Ri : input parameter, list of pixels in the current segment */
    to_check;			/* queue or stack - need to check the neighbors of these pixels */
    no_check;			/* sorted array or btree: list of pixels (by row / column ?) that have been put into the to_check queue, been processed, or are not candidate pixels */

    current_pixel;		/*what data type?  This will be the popped pixel in each loop. */
    /* functions->pixel_neighbors  ...array, 4 or 8 long.  (Can be 4 or 8 neighbors to each pixel)
     * functions->num_pn  int, 4 or 8.

     to_check = Ri; /*need to copy data, not just pointer... */
    /* Put input in "current segment" list  NOTE: in pseudo code, but think we should just pass Ri and use it directly */
    no_check = Ri;		/*need to copy data, not just pointer... */
    /* empty "neighbor" list  Note: in pseudo code, but think we just pass in Rin - it was already initialized, and later could have Ri data available to start from */

    While(!empty(to_check)) {
	current_pixel = pop next to_check element;
	functions->(*find_pixel_neighbors) (current_pixel, pixel_neighbors);

	for (n = 0; n < functions->num_pn; n++) {
	    if (!pixel_neighbor[n] in "don't check" list) {
		put pixel_neighbor[n] in "don't check" list segment_get(&files->out_seg, (void *)files->out_val, pixel_neighbor[n][0], pixel_neighbor[n][1]);	/*TODO : do I need a second "out_val" data structure? */

		if (files->out_val[1] == 1) {	/* valid candidate pixel */
		    put pixel_neighbor[n] in to_check;	/*want to check this pixels neighbors */

		    if (files->out_val[0] = current segment ID)
			put pixel_neighbor[n] in Ri
			else
		  put pixel_neighbor[n] in Rin}
	    }			/*end if for pixel_neighbor was in "don't check" list */
	}			/* end for loop - next neighbor */
    }				/* while to_check has more elements */

    return 0;
}

find_four_pixel_neighbors(pixel, pixel_neighbors)
{
    /* north */
    pixel_neighbors[0][1] = pixel column;
    if (pixel row > 0)
	pixel_neighbors[0][0] = pixel row + 1;
    else
	pixel_neighbors[0][0] = pixel row;	/*This is itself, which will be in "already checked" list.  TODO: use null or -1 as flag to skip?  What is fastest to process? */

    /* east */
    pixel_neighbors[1][0] = pixel row;
    if (pixel column < files->ncols)
	pixel_neighbors[1][1] = pixel column + 1;
    else
	pixel_neighbors[1][1] = pixel column;	/* ditto... */

    /*TODO: continue for south and north */

    /*TODO: seems there should be a more elegent way to do this... */
    return 0;
}

find_eight_pixel_neighbors(pixel, neighbors)
{
    /* get the 4 orthogonal neighbors */
    find_four_pixel_neighbors(pixel, neighbors);

    /* get the 4 diagonal neighbors */

    /*TODO... continue as above */
    return 0;
}
