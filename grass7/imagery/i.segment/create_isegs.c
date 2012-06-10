/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <float.h>		/* to get value of LDBL_MAX -> change this if there is a more usual grass way */
#include <math.h>		/* for sqrt() and pow() */
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
	successflag = io_debug(files, functions);	/* TODO: why does it want &files in main, but files here ??? */
    else if (functions->method == 1) {
	G_debug(1, "starting region_growing()");
	successflag = region_growing(files, functions);
    }
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
    int row, col, n, m, t;
    double threshold, Ri_similarity, Rk_similarity, tempsim;
    int endflag;		/* =1 if there were no merges on that processing iteration */
    int pathflag;		/* =1 if we didn't find mutual neighbors, and should continue with Rk */

    /*int mergeflag;    just did it based on if statment... *//* =1 if we have mutually agreeing best neighbors */

    /* Ri = current focus segment
     * Rk = Ri's most similar neighbor
     * Rkn = Rk's neighbors
     * Rin = Ri's neigbors (as pixels or segments ?!?
     */

    /* lets get this running, and just use fixed dimension arrays for now.  t is limited to 90, segments will be small. */

    int Ri[100][2], Rk[100][2], Rin[100][2], Rkn[100][2];	/* 100 or so maximum members, second dimension is for:  0: row  1:  col */
    int Ri_count, Rk_count, Rin_count, Rkn_count;	/*crutch for now, probably won't need later. */
    int Rk_id;

    G_verbose_message("Running region growing algorithm");

    t = 0;

    do {
	/* for loop on t to slowly lower threshold. also check that endflag=0 */

	threshold = functions->threshold;	/* when implement t loop, this will be a function of t. */

	endflag = 1;


	/* Set candidate flag to true/1 for all pixels TODO: for polygon group, need to just set to true for those being processed */

	/*      for (row = 0; row < files->nrows; row++) {
	   for (col = 0; col < files->ncols; col++) {   -----need to deal with edges.... */
	for (row = 1; row < files->nrows - 1; row++) {
	    for (col = 1; col < files->ncols - 1; col++) {
		segment_get(&files->out_seg, (void *)files->out_val, row, col);	/*need to get, since we only want to change the flag, and not overwrite the segment value. */
		/* TODO: if we are starting from seeds...and only allow merges between unassigned pixels
		 *  and seeds/existing segments, then this needs an if (and will be very inefficient)
		 * maybe consider the sorted array, btree, map... but the number of seeds could still be high for a large map */
		files->out_val[1] = 1;	/*candidate pixel flag */
		segment_put(&files->out_seg, (void *)files->out_val, row,
			    col);
	    }
	}
	G_debug(1, "Starting to process candidate pixels");
	/*process candidate pixels */

	/*check each pixel, start the processing only if it is a candidate pixel */
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
		segment_get(&files->out_seg, (void *)files->out_val, row,
			    col);
		if (files->out_val[1] == 1) {	/* out_val[1] is the candidate pixel flag */

		    /*need to empty/reset Ri, Rn, and Rk */
		    /* TODO: this will be different when Ri is different data structure. */
		    for (n = 0; n < 100; n++) {
			for (m = 0; m < 2; m++) {
			    Ri[n][m] = Rk[n][m] = Rin[n][m] = Rkn[n][m] = 0;
			}
		    }
		    Rin_count = Rkn_count = Rk_count = 0;
		    Ri_count = 1;	/*we'll have the focus pixel to start with. */

		    /* First pixel in Ri is current pixel.  We may add more later if it is part of a segment */
		    Ri[0][0] = row;
		    Ri[0][1] = col;
		    /* Ri_seg = files->out_val[0]; don't need this here -have it in merge_segments() *//* out_val[0] is segment ID, we still have data from call to check the flag. *//* TODO: if seperate segment ID from flag, need to get this value. */

		    pathflag = 1;

		    while (pathflag == 1) {	/*if don't find mutual neighbors on first try, will use Rk as next Ri. */
			G_debug(1, "just before find_segment_neighbors(Ri)");
			if (find_segment_neighbors
			    (Ri, Rin, Ri_count, Rin_count, files,
			     functions) != 0) {
			    G_debug(1, "Couldn't find neighbors");	/*this could happen if there is a pixel surrounded by pixels that have already been processed */
			    pathflag = 0;
			    Ri_count = 0;
			    set_candidate_flag(Ri, 0, files);	/* TODO: error trap? */
			}
			else {	/*found neighbors, go ahead until find mutually agreeing neighbors */
			    G_debug(1, "Found neighbors");
			    /* find Ri's most similar neighbor */
			    Rk_id = -1;
			    Ri_similarity = LDBL_MAX;	/* set current similarity to max value */
			    segment_get(&files->bands_seg, (void *)files->bands_val, Ri[0][0], Ri[0][1]);	/* current segment values */

			    for (n = 0; n < Rin_count; n++) {	/* for each of Ri's neighbors */
				tempsim = (*functions->calculate_similarity) (Ri[0], Rin[n], files, functions);	/*TODO: does this pass just the single point, row/col ???? */
				if (tempsim < Ri_similarity) {
				    Ri_similarity = tempsim;
				    Rk_id = n;
				}
			    }

			    if (Rk_id >= 0 && Ri_similarity < threshold) {	/* small TODO: should this be < or <= for threshold? */
				/*we'll have the neighbor pixel to start with. */
				Rk_count = 1;
				Rk[0][0] = Rin[Rk_id][0];
				Rk[0][1] = Rin[Rk_id][1];

				/* Rkn = Ri; *//* we know Ri should be a neighbor of Rk *//*Todo: is there a way to skip similarity calculations on these?  keep a count, and pop them before doing the similarity check? */
				find_segment_neighbors(Rk, Rkn, Rk_count, Rkn_count, files, functions);	/* data structure for Rk's neighbors, and pixels in Rk if we don't already have it */

				/*find Rk's most similar neighbor */
				Rk_similarity = Ri_similarity;	/*Ri gets first priority - ties won't change anything, so we'll accept Ri and Rk as mutually best neighbors */
				segment_get(&files->bands_seg, (void *)files->bands_val, Rk[0][0], Rk[0][1]);	/* current segment values */

				for (n = 0; n < Rkn_count; n++) {	/* for each of Rk's neighbors */
				    tempsim =
					functions->calculate_similarity(Rk[0],
									Rkn
									[n],
									files,
									functions);
				    if (tempsim < Rk_similarity) {
					Rk_similarity = tempsim;
					break;	/* exit for Rk's neighbors loop here, we know that Ri and Rk aren't mutually best neighbors */
				    }
				}

				if (Rk_similarity == Ri_similarity) {	/* so they agree, both are mutually most similar neighbors */
				    /* TODO: put these steps in merge_segments(Ri, Rk) function?  */
				    merge_values(Ri, Rk, Ri_count, Rk_count, files);	/* TODO error trap */
				    endflag = 0;	/* we've made at least one merge, so need another t iteration */
				    pathflag = 0;	/* go to next row,column pixel - end of Rk -> Ri chain since we found mutual best neighbors */
				}
				else {	/* they weren't mutually best neighbors */
				    set_candidate_flag(Ri, 0, files);	/* remove Ri from candidate pixels (set flag) */

				    /* Use Rk as next Ri:   this is the eCognition technique.  Seems this is a bit faster, we already have segment membership pixels */
				    Ri_count = Rk_count;
				    /* Ri = &Rk; *//* TODO fast/correct way to use arrays and pointers? Ri now will just point to Rk? */
				    /* at beginning, when initialize Rk ` Rk[n][m] = 0 ` ?? with that just remove the Rk pointer, and leave Ri pointing to the original Rk data? */
				    for (n = 0; n < 100; n++) {	/*TODO shortcut code...get rid of this... */
					for (m = 0; m < 2; m++) {
					    Ri[n][m] = Rk[n][m];
					}
				    }

				}
			    }	/*end if Rk exists and < threshold */
			}	/* end else - Ri did have neighbors */
		    }		/*end pathflag do loop */
		}		/*end if pixel is candidate pixel */
	    }			/*next column */
	}			/*next row */

	/* finished one pass for processing candidate pixels */

	t++;
    } while (t < 90 && endflag == 0);
    /*end t loop */

    /* TODO: free memory */

    return 0;
}

int find_segment_neighbors(int Ri[][2], int Rin[][2], int seg_count,
			   int segn_count, struct files *files,
			   struct functions *functions)
{
    G_debug(1, "in find_segment_neighbors()");
    int n, m, Ri_seg_ID = -1;

    /* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
     * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
     * But the list of points would NOT be inclusive - just the points bordering the current segment...
     */


    /* Ri could be single pixel or list of pixels. */
    /* Rin could have a list already, or could be empty ?  Or just the head?  */

    /*local data structures... but maybe they should be allocated out in the main function, is it really slow to create/free on each pass? */

    /* Ri : input parameter, list of pixels in the current segment */
    int to_check[100][2];	/* queue or stack - need to check the neighbors of these pixels */

    /* int[100][2] no_check;    *//* sorted array or btree: list of pixels (by row / column ?) that have been put into the to_check queue, been processed, or are not candidate pixels */
    /* or use flag for no_check? ... need a better name for this variable??? */

    int pixel_neighbors[8][2];	/* data type?  put in files to allocate memory once? */

    int current_pixel = 0;	/*what data type?  This will be the popped pixel in each loop. */

    /* functions->pixel_neighbors  ...array, 4 or 8 long.  (Can be 4 or 8 neighbors to each pixel)
     * functions->num_pn  int, 4 or 8. */

    /*initialize data.... TODO: maybe remember min max row/col that was looked at each time, initialize in open_files, and reset smaller region at end of this functions */
    G_debug(1, "setting files->no_check to 0...");
    for (n = 0; n < files->nrows; n++)
	for (m = 0; n < files->ncols; n++)
	    files->no_check[n][m] = 0;	/* 0 means should be checked/expanded, 1 means it has already been checked/expanded. */

    G_debug(1, "setting to_check to 0");

    for (n = 0; n < 100; n++) {
	for (m = 0; m < 2; m++) {
	    to_check[n][m] = files->no_check[n][m] = 0;
	}
    }

    /* Put Ri in to be checked and no check lists (don't expand them if we find them again) */
    /* NOTE: in pseudo code also have a "current segment" list, but think we can just pass Ri and use it directly */
    G_debug(1, "Setting up Ri... ");
    for (n = 0; n < seg_count; n++) {
	to_check[n][0] = Ri[n][0];
	to_check[n][1] = Ri[n][1];

	files->no_check[Ri[n][0]][Ri[n][1]] = 1;
    }

    /* empty "neighbor" list  Note: in pseudo code, but think we just pass in Rin - it was already initialized, and later could have Ri data available to start from */

    /* get Ri's segment ID */
    segment_get(&files->out_seg, (void *)files->out_val, Ri[0][0], Ri[0][1]);
    Ri_seg_ID = files->out_val[1];
    G_debug(1, "initializing is done, start processing");
    while (current_pixel >= 0) {	/* change to not empty once there is a stack... */
	G_debug(1, "current_pixel: %d", current_pixel);
	/* current_pixel = pop next to_check element; */
	/*syntax for function pointer?  functions->(*find_pixel_neighbors) (to_check[current_pixel], pixel_neighbors, files); */
	functions->find_pixel_neighbors(to_check[current_pixel],
					pixel_neighbors, files);
	current_pixel--;	/* Done using this pixels coords, now check neighbors and add to the lists */
	G_debug(1, "found pixel neighbors");
	for (n = 0; n < functions->num_pn; n++) {	/*with pixel neighbors */
	    if (files->no_check[pixel_neighbors[n][0]][pixel_neighbors[n][1]] == 0) {	/* want to check this neighbor */
		files->no_check[pixel_neighbors[n][0]][pixel_neighbors[n][1]] = 1;	/* OK, check it, but don't check it again! */

		segment_get(&files->out_seg, (void *)files->out_val, pixel_neighbors[n][0], pixel_neighbors[n][1]);	/*TODO : do I need a second "out_val" data structure? */

		if (files->out_val[1] == 1) {	/* valid candidate pixel */

		    G_debug(1, "files->out_val[0] = %d Ri_seg_ID = %d",
			    files->out_val[0], Ri_seg_ID);
		    if (files->out_val[0] == Ri_seg_ID) {
			G_debug(1, "puting pixel_neighbor in Ri");
			/* put pixel_neighbor[n] in Ri */
			Ri[seg_count][0] = pixel_neighbors[n][0];
			Ri[seg_count][1] = pixel_neighbors[n][1];
			seg_count++;	/* zero index... so increment after save data. */

			/* put pixel_neighbor[n] in to_check -- want to check this pixels neighbors */
			current_pixel++;
			to_check[current_pixel][0] = pixel_neighbors[n][0];
			to_check[current_pixel][1] = pixel_neighbors[n][1];

		    }
		    else {
			/* put pixel_neighbor[n] in Rin */
			Rin[segn_count][0] = pixel_neighbors[n][0];
			Rin[segn_count][1] = pixel_neighbors[n][1];
			segn_count++;
		    }
		}		/*end if valid candidate pixel */
	    }			/*end if for pixel_neighbor was in "don't check" list */
	}			/* end for loop - next neighbor */
    }				/* while to_check has more elements */

    return 0;
}

int find_four_pixel_neighbors(int pixel[2], int pixel_neighbors[][2],
			      struct files *files)
{
    /*
       G_debug(1,"in find 4 pixel neighbors () ");
       G_debug(1,"pixel row: %d pixel col: %d", pixel[0], pixel[1]);
       G_debug(1, "Total rows: %d, total cols: %d", files->nrows, files->ncols); /*check that we have files... */

    /* north */
    pixel_neighbors[0][1] = pixel[1];
    if (pixel[0] > 0)
	pixel_neighbors[0][0] = pixel[0] + 1;
    else
	pixel_neighbors[0][0] = pixel[0];	/*This is itself, which will be in "already checked" list.  TODO: use null or -1 as flag to skip?  What is fastest to process? */

    /* east */
    pixel_neighbors[1][0] = pixel[0];
    if (pixel[1] < files->ncols)
	pixel_neighbors[1][1] = pixel[1] + 1;
    else
	pixel_neighbors[1][1] = pixel[1];

    /* south */
    pixel_neighbors[2][1] = pixel[1];
    if (pixel[0] < files->nrows)
	pixel_neighbors[2][0] = pixel[0] - 1;
    else
	pixel_neighbors[2][0] = pixel[0];

    /* west */
    pixel_neighbors[3][0] = pixel[0];
    if (pixel[1] < 0)
	pixel_neighbors[3][1] = pixel[1] - 1;
    else
	pixel_neighbors[3][1] = pixel[1];

    /*TODO: seems there should be a more elegent way to do this... */
    return 0;
}

int find_eight_pixel_neighbors(int pixel[2], int pixel_neighbors[8][2],
			       struct files *files)
{
    /* get the 4 orthogonal neighbors */
    find_four_pixel_neighbors(pixel, pixel_neighbors, files);

    /* get the 4 diagonal neighbors */

    /*TODO... continue as above */
    return 0;
}

/* similarity / distance between two points based on their input raster values */
/* TODO: I pulled getting the a values into the main function, they are stored in files.  Remove a from these parameters */
double calculate_euclidean_similarity(int a[2], int b[2], struct files *files,
				      struct functions *functions)
{
    double val = 0;
    int n;

    /* get comparison values for point b (got values for a before loop on all neighbors... */
    segment_get(&files->bands_seg, (void *)files->second_val, b[0], b[1]);

    /* euclidean distance, sum the square differences for each dimension */
    for (n = 0; n < files->nbands; n++) {
	val = val + pow(files->bands_val[n] - files->second_val[n], 2);
    }

    val = sqrt(val);

    return val;

}

int merge_values(int Ri[100][2], int Rk[100][2], int Ri_count, int Rk_count,
		 struct files *files)
{				/* I assume this is a weighted mean? */
    int n;

    /*get input values, maybe if handle earlier gets correctly this can be avoided. */
    segment_get(&files->bands_seg, (void *)files->bands_val, Ri[0][0],
		Ri[0][1]);
    segment_get(&files->bands_seg, (void *)files->second_val, Rk[0][0],
		Rk[0][1]);

    for (n = 0; n < files->nbands; n++) {
	files->bands_val[n] =
	    (files->bands_val[n] * Ri_count +
	     files->second_val[n] * Rk_count) / (Ri_count + Rk_count);
    }

    /* update segment number and process flag ==0 */

    segment_get(&files->out_seg, (void *)files->out_val, Ri[0][0], Ri[0][1]);
    files->out_val[1] = 0;	/*candidate pixel flag, only one merge allowed per t iteration */


    /* for each member of Ri and Rk, write new average bands values and segment values */
    for (n = 0; n < Ri_count; n++) {
	segment_put(&files->bands_seg, (void *)files->bands_val, Ri[n][0],
		    Ri[n][1]);
	segment_put(&files->out_seg, (void *)files->out_val, Ri[n][0],
		    Ri[n][1]);
    }
    for (n = 0; n < Rk_count; n++) {
	segment_put(&files->bands_seg, (void *)files->bands_val, Rk[n][0],
		    Rk[n][1]);
	segment_put(&files->out_seg, (void *)files->out_val, Rk[n][0],
		    Rk[n][1]);
    }

    return 0;
}

/* TODO.. helper function, maybe make more general? */
int set_candidate_flag(int Ri[100][2], int value, struct files *files)
{
    /* Ri is list of pixels, value is new value of flag */
    int n;

    /* TODO: Ri data structure... eventually just need to process all pixels in Ri. */
    for (n = 0; n < 100; n++) {
	segment_get(&files->out_seg, (void *)files->out_val, Ri[n][0], Ri[n][1]);	/* this may change... */
	files->out_val[1] = value;	/*candidate pixel flag */
	segment_put(&files->out_seg, (void *)files->out_val, Ri[n][0],
		    Ri[n][1]);

    }
    return 0;
}
