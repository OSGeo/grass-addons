/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <float.h>		/* to get value of LDBL_MAX -> change this if there is a more usual grass way */
#include <math.h>		/* for sqrt() and pow() */
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include <grass/linkm.h>	/* memory manager for linked lists */
#include "iseg.h"

#define LINKM

int create_isegs(struct files *files, struct functions *functions)
{

    int successflag = 1;

    /* TODO consider if there are _method specific_ parameter set up and memory allocation, should that happen here? */

    if (functions->method == 1) {	/*region growing */

	/* nothing yet */
    }

    /*TODO: implement outer loop to process polygon interior, then all remaining pixels */
    /* This loop could go in here, or in main to contain open/create/write to reduced memory reqs.  But how merge the writes? */

    G_debug(1, "Threshold: %g", functions->threshold);
    G_debug(1, "segmentation method: %d", functions->method);


    if (functions->method == 0)
	successflag = io_debug(files, functions);	/* TODO: why does it want `&files` in main, but `files` here ??? */
    else if (functions->method == 1) {
	G_debug(1, "starting region_growing()");
	successflag = region_growing(files, functions);
    }
    else if (functions->method == 2)
	successflag = ll_test(files, functions);

    /* end outer loop for processing polygons */

    /* clean up */


    return successflag;
}

int io_debug(struct files *files, struct functions *functions)
{
    int row, col;

    /* for testing other stuff */


    /* from speed.c to test speed of malloc vs. memory manager */
    register int i;
    struct link_head *head;
    struct pixels *p;

    /* **************write fake data to test I/O portion of module */

    G_verbose_message("writing fake data to segmentation file");
    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);	/* TODO this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    files->out_val[0] = col + row;
	    files->out_val[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)files->out_val, row, col);
	}
    }

    /* spot to test things... */

    /*speed test... showed a difference of 1min 9s for G_malloc and 34s for linkm. (with i < 2000000000   */
    /* TODO: fine tune the chunk size */

#ifdef LINKM
    head = (struct link_head *)link_init(sizeof(struct pixels));
#endif

    for (i = 0; i < 10; i++) {
#ifdef LINKM
	p = (struct pixels *)link_new(head);
	link_dispose((struct link_head *)head, (VOID_T *) p);
#else
	p = (struct pixels *)G_malloc(sizeof(struct pixels));
	G_free(p);
#endif
    }

#ifdef LINKM
    link_cleanup(head);
    G_message("used linkm");
#else
    G_message("used G_malloc");
#endif

    G_message("end speed test");
    return 0;
}

int ll_test(struct files *files, struct functions *functions)
{
    int row, col, n, count;
    struct pixels *Rkn, *current, *newpixel, *Rin_head;	/*current will be used to iterate over any of the linked lists. */

    G_verbose_message("testing linked lists");

    /*allocate linked list memory */
    /*todo: should the be done in open_files, where other memory things go? or just leave here, data structure / memory for the actual segmentation? */
    //~ G_debug(1, "setting up linked lists");
    //~ Token = (struct link_head *)link_init(sizeof(struct pixels));
    //~ G_debug(1, "have token");

    Rin_head = NULL;
    Rkn = NULL;

    /* make a neighbor list */
    for (n = 0; n < 5; n++) {
	newpixel = (struct pixels *)link_new(files->token);
	newpixel->next = Rin_head;	/*point the new pixel to the current first pixel */
	newpixel->row = n;
	newpixel->col = n + 2;
	Rin_head = newpixel;	/*change the first pixel to be the new pixel. */

	G_message("Added: Rin %d: row: %d, col: %d", n,
		  Rin_head->row, Rin_head->col);

    }

    for (n = 0; n < 5; n++) {
	newpixel = (struct pixels *)link_new(files->token);
	newpixel->next = Rkn;	/*point the new pixel to the current first pixel */
	newpixel->row = 5 * n;
	newpixel->col = n;
	Rkn = newpixel;		/*change the first pixel to be the new pixel. */

	G_message("Added: Rkn %d: row: %d, col: %d", n, Rkn->row, Rkn->col);

    }


    G_message(" Test pass token result: %d",
	      test_pass_token(&Rin_head, files));

    G_message("Printing out:");
    /*print out neighbors */
    for (current = Rin_head; current != NULL; current = current->next)
	G_debug(1, "Rin: row: %d, col: %d", current->row, current->col);

    for (current = Rkn; current != NULL; current = current->next)
	G_debug(1, "Rkn: row: %d, col: %d", current->row, current->col);

    /* remove all from Rkn list, 5 from Rin list */

    for (n = 0; n < 5; n++) {
	current = Rin_head;	/* get first in list */
	Rin_head = current->next;	/* point head to the next one *//*pop */
	link_dispose((struct link_head *)current, (VOID_T *) files->token);
    }

    for (current = Rkn; current != NULL; current = current->next) {
	link_dispose((struct link_head *)current, (VOID_T *) files->token);
    }
    Rkn = NULL;			/* TODO: if emptying whole list - can just empty and then set head to null ? */

    G_message("Printing out, after removed:");
    /*print out neighbors */
    for (current = Rin_head; current != NULL; current = current->next)
	G_debug(1, "Rin: row: %d, col: %d", current->row, current->col);

    for (current = Rkn; current != NULL; current = current->next)
	G_debug(1, "Rkn: row: %d, col: %d", current->row, current->col);


    /* **************write fake data to test I/O portion of module */

    G_verbose_message("writing fake data to segmentation file");
    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);	/* TODO this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    files->out_val[0] = col + row;
	    files->out_val[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)files->out_val, row, col);
	}
    }

    /*test how many pixels can be made and disposed of */

    for (n = 0; n < functions->threshold; n++) {
	/*make tokens */
	test_pass_token(&Rkn, files);
	count += 5;
	G_debug(1, "estimate of tokens created %d", count);
	/*dispose tokens */
	for (current = Rkn; current != NULL; current = current->next)
	    link_dispose((struct link_head *)Rkn, (VOID_T *) files->token);

	G_debug(1, "are they gone?");
	for (current = Rkn; current != NULL; current = current->next)
	    G_debug(1, "Rkn: row: %d, col: %d", current->row, current->col);

	Rkn = NULL;		/* TODO: if emptying whole list - can just empty and then set head to null ? */

	G_debug(1,
		"Checking after set head to null.... TODO: anyway to find out if linkm memory manager knows they are gone???");
	for (current = Rkn; current != NULL; current = current->next)
	    G_debug(1, "Rkn: row: %d, col: %d", current->row, current->col);


    }


    G_message("end linked list test");
    return 0;
}

int test_pass_token(struct pixels **head, struct files *files)
{
    int n;
    struct pixels *newpixel;

    for (n = 10; n < 15; n++) {
	newpixel = (struct pixels *)link_new(files->token);
	newpixel->next = *head;	/*point the new pixel to the current first pixel */
	newpixel->row = n;
	newpixel->col = n * 2;
	*head = newpixel;	/*change the first pixel to be the new pixel. */

	G_message("Added: Rin %d: row: %d, col: %d", n,
		  newpixel->row, newpixel->col);
    }
    return 0;

}

int region_growing(struct files *files, struct functions *functions)
{
    int row, col, t;
    double threshold, Ri_similarity, Rk_similarity, tempsim;
    int endflag;		/* =1 if there were no merges on that processing iteration */
    int pathflag;		/* =1 if we didn't find mutual neighbors, and should continue with Rk */

    /*int mergeflag;    just did it based on if statment... *//* =1 if we have mutually agreeing best neighbors */

    /* Ri = current focus segment
     * Rk = Ri's most similar neighbor
     * Rkn = Rk's neighbors
     * Rin = Ri's neigbors (as pixels or segments ?) currently as pixels, so repeat calculations are made when multiple neighbors in same segment
     */

    /* lets get this running, and just use fixed dimension arrays for now.  t is limited to 90, segments will be small. */

    /* linkm - linked list memory allocation. */
    //~ struct link_head *Token;        /* seems we can "manage multiple lists" will use one token for all lists, since all have same size elements. */
    struct pixels *Ri_head, *Rk_head, *Rin_head, *Rkn_head, *current, *newpixel;	/*current will be used to iterate over any of the linked lists. */
    int Ri_count, Rk_count;	/*TODO when to calculate these. */
    struct pixels *Ri_bestn;	/* best neighbor pixel for Ri, don't use as a linked list, just one pixel... */

    G_verbose_message("Running region growing algorithm");

    t = 0;
    files->candidate_count = 0;


    /*allocate linked list memory */
    /* done in open_files() */

    /*set next pointers to null. */
    Ri_head = NULL;
    Rk_head = NULL;
    Rin_head = NULL;
    Rkn_head = NULL;
    Ri_bestn = NULL;

    do {
	/* do while loop on t to slowly lower threshold. also check that endflag==0 (no merges were made) */

	G_debug(1,
		"#############   Starting outer do loop! t = %d ###############",
		t);

	threshold = functions->threshold;	/* TODO, consider making this a function of t. */

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

		files->candidate_count++;	/*TODO this assumes full grid with no null or mask!! But need something to prevent "pathflag" infinite loop */

	    }
	}
	G_debug(1, "Starting to process %d candidate pixels",
		files->candidate_count);

	/*process candidate pixels */

	/*check each pixel, start the processing only if it is a candidate pixel */
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {

		G_verbose_message("Completion for pass number %d: ", t);
		G_percent(row, files->nrows, 1);	/*this didn't get displayed in the output??? Does it get erased when done? */

		G_debug(1,
			"Next starting pixel from next row/col, not from Rk");
		segment_get(&files->out_seg, (void *)files->out_val, row, col);	/*TODO small time savings - if candidate_count reaches zero, bail out of these loops too? */
		if (files->out_val[1] == 1) {	/* out_val[1] is the candidate pixel flag, want to process the 1's */

		    /*free memory for linked lists */
		    my_dispose(&Ri_head, files);
		    my_dispose(&Rk_head, files);
		    my_dispose(&Rin_head, files);
		    my_dispose(&Rkn_head, files);	/* TODO, better style for repeating this for all structures? */
		    Rk_count = 0;


		    /* First pixel in Ri is current pixel.  We may add more later if it is part of a segment */
		    Ri_count = 1;	/* TODO, count as we go, or when process?  */
		    newpixel = (struct pixels *)link_new(files->token);
		    newpixel->next = Ri_head;
		    newpixel->row = row;
		    newpixel->col = col;
		    Ri_head = newpixel;

		    pathflag = 1;

		    //      while (pathflag == 1 && files->candidate_count > 0) {   /*if don't find mutual neighbors on first try, will use Rk as next Ri. */

		    G_debug(1, "Next starting pixel: row, %d, col, %d",
			    Ri_head->row, Ri_head->col);

		    /* Setting Ri to be not a candidate allows using "itself" when at edge of raster.
		     * Otherwise need to use a list/count/something to know the number of pixel neighbors */
		    set_candidate_flag(Ri_head, 0, files);	/* TODO: error trap? */
		    G_debug(1, "line 165, \t\t\t\tcc = %d",
			    files->candidate_count);


		    /* find segment neighbors */
		    if (find_segment_neighbors
			(&Ri_head, &Rin_head, &Ri_count, files,
			 functions) != 0) {
			G_fatal_error("find_segment_neighbors() failed");
		    }

		    if (Rin_head == NULL) {
			G_debug(1, "2a, Segment had no valid neighbors");	/*this could happen if there is a segment surrounded by pixels that have already been processed */
			pathflag = 0;
			Ri_count = 0;
			set_candidate_flag(Ri_head, 0, files);	/* TODO: error trap? */
			files->candidate_count++;	/* already counted out Ri[0]; */
			G_debug(1, "line 176, \t\t\t\tcc = %d",
				files->candidate_count);
		    }
		    else {	/*found neighbors, go ahead until find mutually agreeing neighbors */

			G_debug(1, "2b, Found Ri's pixels");
			/*print out neighbors */

			for (current = Ri_head; current != NULL;
			     current = current->next)
			    G_debug(1, "Ri: row: %d, col: %d", current->row,
				    current->col);


			G_debug(1, "2b, Found Ri's neighbors");
			/*print out neighbors */
			for (current = Rin_head; current != NULL;
			     current = current->next)
			    G_debug(1, "Rin: row: %d, col: %d", current->row,
				    current->col);

			/* find Ri's most similar neighbor */
			Ri_bestn = NULL;
			Ri_similarity = LDBL_MAX;	/* set current similarity to max value */
			segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row, Ri_head->col);	/* current segment values */

			for (current = Rin_head; current != NULL; current = current->next) {	/* for each of Ri's neighbors */
			    tempsim =
				(*functions->calculate_similarity) (Ri_head,
								    current,
								    files,
								    functions);
			    G_debug(1,
				    "simularity = %g for neighbor : row: %d, col %d.",
				    tempsim, current->row, current->col);
			    if (tempsim < Ri_similarity) {
				Ri_similarity = tempsim;
				Ri_bestn = current;	/*TODO want to point to the current pixel...confirm  when current changes need this to stay put! */
				G_debug(1,
					"Current lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
					Ri_similarity, Ri_bestn->row,
					Ri_bestn->col);
			    }
			}

			if (Ri_bestn != NULL)
			    G_debug(1,
				    "Lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
				    Ri_similarity, Ri_bestn->row,
				    Ri_bestn->col);

			if (Ri_bestn != NULL && Ri_similarity < threshold) {	/* small TODO: should this be < or <= for threshold? */
			    /* we'll have the neighbor pixel to start with. */
			    G_debug(1, "3a: Working with Rk");
			    Ri_bestn->next = NULL;	/* Don't want to carry any of the other pixels with this one... */
			    Rk_count = 1;

			    Rk_head = Ri_bestn;	/* TODO, OK like this?  Maybe forget Ri_bestn, just use Rk from the beginning? */

			    /* TODO need to copy the data, not just use Ri itself! *//* Rkn = Ri; *//* we know Ri should be a neighbor of Rk *//*Todo: is there a way to skip similarity calculations on these?  keep a count, and pop them before doing the similarity check? */
			    find_segment_neighbors(&Rk_head, &Rkn_head, &Rk_count, files, functions);	/* data structure for Rk's neighbors, and pixels in Rk if we don't already have it */

			    G_debug(1, "Found Rk's pixels");
			    /*print out neighbors */
			    for (current = Rk_head; current != NULL;
				 current = current->next)
				G_debug(1, "Rk: row: %d, col: %d",
					current->row, current->col);

			    G_debug(1, "Found Rk's neighbors");
			    /*print out neighbors */
			    for (current = Rkn_head; current != NULL;
				 current = current->next)
				G_debug(1, "Rkn: row: %d, col: %d",
					current->row, current->col);

			    /*find Rk's most similar neighbor */
			    Rk_similarity = Ri_similarity;	/*Ri gets first priority - ties won't change anything, so we'll accept Ri and Rk as mutually best neighbors */
			    segment_get(&files->bands_seg, (void *)files->bands_val, Rk_head->row, Rk_head->col);	/* current segment values */

			    for (current = Rkn_head; current != NULL; current = current->next) {	/* for each of Rk's neighbors */
				tempsim = functions->calculate_similarity(Rk_head, current, files, functions);	/*TODO: need an error trap here, if something goes wrong with calculating similarity? */
				if (tempsim < Rk_similarity) {
				    Rk_similarity = tempsim;
				    break;	/* exit for Rk's neighbors loop here, we know that Ri and Rk aren't mutually best neighbors */
				}
			    }

			    if (Rk_similarity == Ri_similarity) {	/* so they agree, both are mutually most similar neighbors, none of Rk's other neighbors were more similar */
				/* TODO: put these steps in merge_segments(Ri, Rk) function?  */
				merge_values(Ri_head, Rk_head, Ri_count, Rk_count, files);	/* TODO error trap */
				endflag = 0;	/* we've made at least one merge, so need another t iteration */
				pathflag = 0;	/* go to next row,column pixel - end of Rk -> Ri chain since we found mutual best neighbors */
			    }
			    else {	/* they weren't mutually best neighbors */
				G_debug(1,
					"Ri was not Rk's best neighbor, Ri_sim: %g, Rk_sim, %g",
					Ri_similarity, Rk_similarity);

				/* did this at beginning of trail loop */
				set_candidate_flag(Ri_head, 0, files);	/* remove all Ri members from candidate pixels (set flag) */
				files->candidate_count++;	/* add one back, we had already set Ri[0] flag at the beginning. */
				G_debug(1, "line 247, \t\t\t\tcc = %d",
					files->candidate_count);
				//~ /* Use Rk as next Ri:   this is the eCognition technique.  Seems this is a bit faster, we already have segment membership pixels */
				//~ Ri_count = Rk_count;
				//~ /* Ri = &Rk; *//* TODO fast/correct way to use arrays and pointers? Ri now will just point to Rk? */
				//~ /* at beginning, when initialize Rk ` Rk[n][m] = 0 ` ?? with that just remove the Rk pointer, and leave Ri pointing to the original Rk data? */
				//~ for (n = 0; n < 100; n++) {     /*TODO shortcut code...get rid of this... */
				//~ for (m = 0; m < 2; m++) {
				//~ Ri[n][m] = Rk[n][m];
				//~ }
				//~ }

			    }
			}	/*end if Rk exists and < threshold */
			else
			    G_debug(1,
				    "3b Rk didn't didn't exist or similarity was > threshold");
		    }		/* end else - Ri did have neighbors */
		    //          }           /*end pathflag do loop */
		}		/*end if pixel is candidate pixel */
	    }			/*next column */
	}			/*next row */

	/* finished one pass for processing candidate pixels */

	G_debug(1, "Finished one pass, t was = %d", t);
	t++;
    } while (t < 90 && endflag == 0);
    /*end t loop */

    /* free memory *//*TODO: anything else? */

    /* in close_files()    link_cleanup((struct link_head *)Token); */

    return 0;
}

int find_segment_neighbors(struct pixels **R_head,
			   struct pixels **neighbors_head, int *seg_count,
			   struct files *files, struct functions *functions)
{
    //   G_debug(1, "\tin find_segment_neighbors()");
    int n, m, Ri_seg_ID = -1;
    struct pixels *newpixel, *current;

    /* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
     * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
     * But the list of points would NOT be inclusive - just the points bordering the current segment...
     */


    /* parameter: R, current segment membership, could be single pixel or list of pixels. */
    /* parameter: neighbors/Rin, neighbor pixels, could have a list already, or could be empty ?  Or just the head of a list?  */

    /* TODO local data structures... but maybe they should be allocated out in the main function, is it really slow to create/free on each pass? */

    struct pixels *to_check;	/* need to check the neighbors of these pixels */

    /* put no_check in files structure for now... */
    /* int[100][2] no_check;    *//* sorted array or btree: list of pixels (by row / column ?) that have been put into the to_check queue, been processed, or are not candidate pixels */
    /* or use flag for no_check? ... need a better name for this variable??? */

    int val_no_check = -1;	/*value of the no_check flag for the particular pixel. */

    int pixel_neighbors[8][2];	/* TODO: data type?  put in files to allocate memory once? */

    /*int current_pixel = 0; *//* TODO: for now, row index for pixel_neighbors[][].  With linked list will be the popped pixel in each loop. */

    /* Notes, these are in functions structure:
     * functions->num_pn  int, 4 or 8, for number of pixel neighbors */

    /*initialize data.... TODO: maybe remember min max row/col that was looked at each time, initialize in open_files, and reset smaller region at end of this functions */
    for (n = 0; n < files->nrows; n++) {
	for (m = 0; m < files->ncols; m++) {
	    val_no_check = 0;
	    segment_put(&files->no_check, &val_no_check, n, m);
	}
    }

    to_check = NULL;

    /* Put Ri in to be checked and no check lists (don't expand them if we find them again) */
    /* NOTE: in pseudo code also have a "current segment" list, but think we can just pass Ri and use it directly */

    for (current = *R_head; current != NULL; current = current->next) {

	newpixel = (struct pixels *)link_new(files->token);
	newpixel->next = to_check;	/*point the new pixel to the current first pixel */
	newpixel->row = current->row;
	newpixel->col = current->col;
	to_check = newpixel;	/*change the first pixel to be the new pixel. */

	val_no_check = 1;
	segment_put(&files->no_check, &val_no_check, current->row,
		    current->col);
    }

    /* empty "neighbor" list  Note: this step is in pseudo code, but think we just pass in Rin - it was already initialized, and later could have Ri data available to start from */

    /* get Ri's segment ID */
    segment_get(&files->out_seg, (void *)files->out_val, (*R_head)->row,
		(*R_head)->col);
    Ri_seg_ID = files->out_val[0];

    while (to_check != NULL) {	/* removing from to_check list as we go, NOT iterating over the list. */
	G_debug(1,
		"\tfind neighbors(): head to_check pixel: row: %d, col: %d",
		to_check->row, to_check->col);
	/* current_pixel = just use to_check - the row/col, and remove at end */

	G_debug(1,
		"\tfind_pixel_neighbors for row: %d , col %d",
		to_check->row, to_check->col);

	functions->find_pixel_neighbors(to_check->row,
					to_check->col,
					pixel_neighbors, files);

	/* Done using this to_check pixels coords, remove from list */

	current = to_check;	/* temporary store the old head */
	to_check = to_check->next;	/*head now points to the next element in the list */
	link_dispose((struct link_head *)current, (VOID_T *) files->token);

	/*print out to_check */
	G_debug(1, "remaining pixel's in to_check, after popping:");
	for (current = to_check; current != NULL; current = current->next)
	    G_debug(1, "to_check... row: %d, col: %d", current->row,
		    current->col);

	/*now check the pixel neighbors and add to the lists */

	/*debug what neighbors were found: */
	/*      for (n = 0; n < functions->num_pn; n++){
	   G_debug(1, "\tpixel_neighbors[n][0]: %d, pixel_neighbors[n][1]: %d",  pixel_neighbors[n][0], pixel_neighbors[n][1]);
	   } */

	for (n = 0; n < functions->num_pn; n++) {	/* with pixel neighbors */

	    segment_get(&files->no_check, &val_no_check,
			pixel_neighbors[n][0], pixel_neighbors[n][1]);
	    G_debug(1,
		    "\twith pixel neigh %d, row: %d col: %d, val_no_check = %d",
		    n, pixel_neighbors[n][0], pixel_neighbors[n][1],
		    val_no_check);
	    if (val_no_check == 0) {	/* want to check this neighbor */
		val_no_check = 1;
		segment_put(&files->no_check, &val_no_check, pixel_neighbors[n][0], pixel_neighbors[n][1]);	/* don't check it again */

		segment_get(&files->out_seg, (void *)files->out_val, pixel_neighbors[n][0], pixel_neighbors[n][1]);	/*TODO : do I need a second "out_val" data structure? */

		if (files->out_val[1] == 1) {	/* valid candidate pixel */

		    G_debug(1, "\tfiles->out_val[0] = %d Ri_seg_ID = %d",
			    files->out_val[0], Ri_seg_ID);
		    if (files->out_val[0] == Ri_seg_ID) {
			G_debug(1, "\tputing pixel_neighbor in Ri");
			/* put pixel_neighbor[n] in Ri */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = *R_head;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			*R_head = newpixel;	/*change the first pixel to be the new pixel. */
			*seg_count = *seg_count + 1;	/* zero index... Ri[0] had first pixel and set count =1.  increment after save data. */
			G_debug(1, "\t*seg_count now = %d", *seg_count);

			/* put pixel_neighbor[n] in to_check -- want to check this pixels neighbors */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = to_check;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			to_check = newpixel;	/*change the first pixel to be the new pixel. */

		    }
		    else {
			/* put pixel_neighbor[n] in Rin */
			G_debug(1, "Put in neighbors_head");
			/* TODO - helper function for adding pixel to a list */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = *neighbors_head;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			*neighbors_head = newpixel;	/*change the first pixel to be the new pixel. */

		    }
		}		/*end if valid candidate pixel */
		else
		    G_debug(1, "pixel was not a valid candidate pixel");

	    }			/*end if for pixel_neighbor was in "don't check" list */
	}			/* end for loop - next pixel neighbor */
	G_debug(1,
		"remaining pixel's in to_check, after processing the last pixel's neighbors:");
	for (current = to_check; current != NULL; current = current->next)
	    G_debug(1, "to_check... row: %d, col: %d", current->row,
		    current->col);



    }				/* while to_check has more elements */

    return 0;
}

int find_four_pixel_neighbors(int p_row, int p_col, int pixel_neighbors[][2],
			      struct files *files)
{
    /*   
       G_debug(1,"\t\tin find 4 pixel neighbors () ");
       G_debug(1,"\t\tpixel row: %d pixel col: %d", p_row, p_col);
       G_debug(1, "\t\tTotal rows: %d, total cols: %d", files->nrows, files->ncols); *//*check that we have files... */

    /* north */
    pixel_neighbors[0][1] = p_col;
    if (p_row > 0)
	pixel_neighbors[0][0] = p_row - 1;
    else
	pixel_neighbors[0][0] = p_row;	/*This is itself, which will be in "already checked" list.  TODO: use null or -1 as flag to skip?  What is fastest to process? */

    /* east */
    pixel_neighbors[1][0] = p_row;
    if (p_col < files->ncols - 1)
	pixel_neighbors[1][1] = p_col + 1;
    else
	pixel_neighbors[1][1] = p_col;

    /* south */
    pixel_neighbors[2][1] = p_col;
    if (p_row < files->nrows - 1)
	pixel_neighbors[2][0] = p_row + 1;
    else
	pixel_neighbors[2][0] = p_row;

    /* west */
    pixel_neighbors[3][0] = p_row;
    if (p_col > 0)
	pixel_neighbors[3][1] = p_col - 1;
    else
	pixel_neighbors[3][1] = p_col;

    /*TODO: seems there should be a more elegent way to do this... */
    return 0;
}

int find_eight_pixel_neighbors(int p_row, int p_col,
			       int pixel_neighbors[8][2], struct files *files)
{
    /* get the 4 orthogonal neighbors */
    find_four_pixel_neighbors(p_row, p_col, pixel_neighbors, files);

    /* get the 4 diagonal neighbors */

    /*TODO... continue as above */
    return 0;
}

/* similarity / distance between two points based on their input raster values */
/* assumes first point values already saved in files->bands_seg - only run segment_get once for that value... */
/* TODO: segment_get already happened for a[] values in the main function.  Could remove a[] from these parameters */
double calculate_euclidean_similarity(struct pixels *a, struct pixels *b,
				      struct files *files,
				      struct functions *functions)
{
    double val = 0;
    int n;

    /* get values for pixel b */
    segment_get(&files->bands_seg, (void *)files->second_val, b->row, b->col);

    /* euclidean distance, sum the square differences for each dimension */
    for (n = 0; n < files->nbands; n++) {
	val = val + pow(files->bands_val[n] - files->second_val[n], 2);
    }

    val = sqrt(val);

    return val;

}

int merge_values(struct pixels *Ri_head, struct pixels *Rk_head, int Ri_count,
		 int Rk_count, struct files *files)
{				/* TODO: correct assumption that this should be a weighted mean. */
    int n;
    struct pixels *current;

    /*get input values, maybe if handle earlier gets correctly this can be avoided. */
    segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row,
		Ri_head->col);
    segment_get(&files->bands_seg, (void *)files->second_val, Rk_head->row,
		Rk_head->col);

    for (n = 0; n < files->nbands; n++) {
	files->bands_val[n] =
	    (files->bands_val[n] * Ri_count +
	     files->second_val[n] * Rk_count) / (Ri_count + Rk_count);
    }

    /* update segment number and process flag ==0 */

    segment_get(&files->out_seg, (void *)files->out_val, Ri_head->row,
		Ri_head->col);
    files->out_val[1] = 0;	/*candidate pixel flag, only one merge allowed per t iteration */
    /* if separate out candidate flag, can do all changes with helper function...otherwise remember: */


    G_debug(1, "\t\tMerging, segment number: %d, including pixels:",
	    files->out_val[0]);

    /* for each member of Ri and Rk, write new average bands values and segment values */
    for (current = Ri_head; current != NULL; current = current->next) {
	segment_put(&files->bands_seg, (void *)files->bands_val, current->row,
		    current->col);
	segment_put(&files->out_seg, (void *)files->out_val, current->row,
		    current->col);
	files->candidate_count--;
	G_debug(1, "line 508, \t\t\t\tcc = %d", files->candidate_count);
	G_debug(1, "\t\tRi row: %d, col: %d", current->row, current->col);
    }
    for (current = Rk_head; current != NULL; current = current->next) {
	segment_put(&files->bands_seg, (void *)files->bands_val, current->row,
		    current->col);
	segment_put(&files->out_seg, (void *)files->out_val, current->row,
		    current->col);
	files->candidate_count--;
	G_debug(1, "line 516, \t\t\t\tcc = %d", files->candidate_count);
	G_debug(1, "\t\tRk row: %d, col: %d", current->row, current->col);

    }

    files->candidate_count++;	/* had already counted down the starting pixel Ri[0] at the beginning... */
    G_debug(1, "line 522, \t\t\t\tcc = %d", files->candidate_count);
    return 0;
}

/* TODO.. helper function, maybe make more general? */
int set_candidate_flag(struct pixels *head, int value, struct files *files)
{
    /* head is linked list of pixels, value is new value of flag */
    struct pixels *current;

    for (current = head; current != NULL; current = current->next) {
	segment_get(&files->out_seg, (void *)files->out_val, current->row, current->col);	/* this may change... */
	files->out_val[1] = value;	/*candidate pixel flag */
	segment_put(&files->out_seg, (void *)files->out_val, current->row,
		    current->col);

	/* also increment how many pixels remain to be processed */

	if (value == 0)
	    files->candidate_count--;
	else if (value == 1)
	    files->candidate_count++;
	G_debug(1, "line 544, \t\t\t\tcc = %d", files->candidate_count);

    }
    return 0;
}

/* let memory manager know space is available again and reset head to NULL */
int my_dispose(struct pixels **head, struct files *files)
{
    struct pixels *current;

    for (current = *head; current != NULL; current = current->next)
	link_dispose((struct link_head *)current, (VOID_T *) files->token);

    *head = NULL;

    return 0;
}
