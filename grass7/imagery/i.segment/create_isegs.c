/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <float.h>		/* to get value of LDBL_MAX -> change this if there is a more usual grass way */
				/* #include <math.h>    *//* for sqrt() and pow() */
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

    /*TODO: implement outer loop to process polygon interior, then all remaining pixels */
    /* This loop could go in here, or in main to contain open/create/write to reduced memory reqs.  But how merge the writes? */

    G_debug(1, "Threshold: %g", functions->threshold);
    G_debug(1, "segmentation method: %d", functions->method);

    functions->threshold = functions->threshold * functions->threshold * files->nbands;	/* use modified threshold to account for scaled input and to avoid square root in similarity comparison. *//* Todo, small, could put this in main outside of polygon loop */

    if (functions->method == 0)
	successflag = io_debug(files, functions);	/* TODO: why does it want `&files` in main, but `files` here ??? */
    else if (functions->method == 1) {
	G_debug(1, "starting region_growing()");
	successflag = region_growing(files, functions);
    }
    else if (functions->method == 2)
	successflag = ll_test(files, functions);

    /* end outer loop for processing polygons */

    /* clean up? */


    return successflag;
}

/* writes row+col to the output raster.  Also using for the linkm speed test. */
int io_debug(struct files *files, struct functions *functions)
{
    int row, col;

    /* from speed.c to test speed of malloc vs. memory manager */
    register int i;
    struct link_head *head;
    struct pixels *p;

    /* **************write fake data to test I/O portion of module */

    /*    G_verbose_message("writing fake data to segmentation file"); */
    G_verbose_message("writing scaled input (layer 1) to output file");
    G_verbose_message("weighted flag = %d", files->weighted);
    for (row = 0; row < files->nrows; row++) {
	G_percent(row, files->nrows, 1);	/* TODO this didn't get displayed in the output??? Does it get erased when done? */
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    /* files->out_val[0] = col + row; */
	    segment_get(&files->bands_seg, (void *)files->bands_val, row,
			col);
	    files->out_val[0] = files->bands_val[0] * 100;	/*pushing DCELL into CELL */
	    files->out_val[1] = 1;	/*processing flag */
	    segment_put(&files->out_seg, (void *)files->out_val, row, col);
	}
    }

    /*speed test... showed a difference of 1min 9s for G_malloc and 34s for linkm. (with i < 2000000000   */

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
    struct pixels *Rkn, *current, *newpixel, *Rin_head, *Rin_second;	/*current will be used to iterate over any of the linked lists. */
    struct link_head *Rkn_token;

    G_message("testing linked lists");

    Rin_head = NULL;
    Rin_second = NULL;
    Rkn = NULL;
    Rkn_token = link_init(sizeof(struct pixels));
    if (Rkn_token == NULL)
	G_message("Rkn_token is null");

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
    /* make a second neighbor list, using same token */
    for (n = 0; n < 4; n++) {
	newpixel = (struct pixels *)link_new(files->token);
	newpixel->next = Rin_second;	/*point the new pixel to the current first pixel */
	newpixel->row = n * 100;
	newpixel->col = n * 100;
	Rin_second = newpixel;	/*change the first pixel to be the new pixel. */

	G_message("Added: Rin (second list) %d: row: %d, col: %d", n,
		  Rin_second->row, Rin_second->col);
    }

    /* make a third neighbor list, using local token */
    for (n = 0; n < 5; n++) {
	newpixel = (struct pixels *)link_new(Rkn_token);
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
	G_message("Rin: row: %d, col: %d", current->row, current->col);

    for (current = Rin_second; current != NULL; current = current->next)
	G_message("Rin (second): row: %d, col: %d", current->row,
		  current->col);

    for (current = Rkn; current != NULL; current = current->next)
	G_message("Rkn: row: %d, col: %d", current->row, current->col);

    /* remove all from Rkn list, 5 from Rin list */
    G_message("removing 5 from Rin...");
    for (n = 0; n < 5; n++) {
	current = Rin_head;	/* get first in list */
	Rin_head = Rin_head->next;	/* point head to the next one *//*pop */
	link_dispose(files->token, (VOID_T *) current);
    }

    G_message("Printing out, after 5 removed from Rin:");
    for (current = Rin_head; current != NULL; current = current->next)
	G_message("Rin: row: %d, col: %d", current->row, current->col);

    for (current = Rin_second; current != NULL; current = current->next)
	G_message("Rin (second): row: %d, col: %d", current->row,
		  current->col);

    for (current = Rkn; current != NULL; current = current->next)
	G_message("Rkn: row: %d, col: %d", current->row, current->col);


    G_message("removing all from Rkn...");
    /* for (current = Rkn; current != NULL; current = current->next) { ||||this shortcut won't work, current is gone! */
    while (Rkn != NULL) {
	G_message("In Rkn remove loop");
	current = Rkn;		/* rememer "old" head */
	Rkn = Rkn->next;	/* move head to next pixel */
	link_dispose(Rkn_token, (VOID_T *) current);	/* remove "old" head */
    }
    G_message("removed Rkn...");
    if (Rkn == NULL)
	G_message("which set Rkn to null");
    else
	G_message("hmm, still need to set Rkn to null?!");

    /* Rkn = NULL;      not needed *//* TODO: if emptying whole list - can just empty and then set head to null ? */

    G_message("Printing out, after removed Rin and Rkn:");
    for (current = Rin_head; current != NULL; current = current->next)
	G_message("Rin: row: %d, col: %d", current->row, current->col);

    for (current = Rin_second; current != NULL; current = current->next)
	G_message("Rin (second): row: %d, col: %d", current->row,
		  current->col);

    for (current = Rkn; current != NULL; current = current->next)
	G_message("Rkn: row: %d, col: %d", current->row, current->col);


    /* **************write fake data to test I/O portion of module */

    G_message("writing fake data to segmentation file");
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
	test_pass_token(&Rin_head, files);
	count += 5;
	G_message("estimate of tokens created %d", count + 15);
	/*dispose tokens */
	while (Rin_head != NULL) {
	    current = Rin_head;	/* rememer "old" head */
	    Rin_head = Rin_head->next;	/* move head to next pixel */
	    link_dispose(files->token, (VOID_T *) current);	/* remove "old" head */
	}

	G_message("are they gone?");
	for (current = Rin_head; current != NULL; current = current->next)
	    G_message("Rin: row: %d, col: %d", current->row, current->col);

	/* TODO: anyway to confirm if linkm memory manager knows they are gone???" */
    }

    link_cleanup(Rkn_token);
    G_message("after link_cleanup(Rkn_token)");

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
     * Rin = Ri's neigbors  currently as pixels, so repeat calculations are made when multiple neighbors in same segment
     * Todo: should Rin be checked for unique segments?  Or is checking for unique longer then just calculating similarity a few extra times?
     * files->token has the "link_head" for linkm: linked list memory allocation. */

    struct pixels *Ri_head, *Rk_head, *Rin_head, *Rkn_head, *current, *newpixel;	/*current will be used to iterate over any of the linked lists. */
    int Ri_count, Rk_count;	/*TODO when to calculate these, currently accumulating during find_neighbor() */
    struct pixels *Ri_bestn;	/* best neighbor pixel for Ri, not used as a linked list, just one pixel... */

    G_verbose_message("Running region growing algorithm");

    t = 0;
    files->candidate_count = 0;

    /*set next pointers to null. */
    Ri_head = NULL;
    Rk_head = NULL;
    Rin_head = NULL;
    Rkn_head = NULL;
    Ri_bestn = NULL;

    do {
	/* do while loop on t to slowly lower threshold. also check that endflag==0 (no merges were made) */

	G_debug(3, "#######   Starting outer do loop! t = %d    #######", t);

	threshold = functions->threshold;	/* TODO, consider making this a function of t. */

	endflag = 1;

	/* Set candidate flag to true/1 for all pixels TODO: for polygon/vector constraint, need to just set to true for those being processed */

	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
		segment_get(&files->out_seg, (void *)files->out_val, row, col);	/*need to get, since we only want to change the flag, and not overwrite the segment value. 
										   TODO: consider splitting this, put flag in one segmentmentation file (or RAM), and segment assignment in another. */
		/* TODO: if we are starting from seeds...and only allow merges between unassigned pixels
		 *  and seeds/existing segments, then this needs an if (and will be very inefficient)
		 * maybe consider the sorted array, btree, map... but the number of seeds could still be high for a large map */
		files->out_val[1] = 1;	/*candidate pixel flag */
		segment_put(&files->out_seg, (void *)files->out_val, row,
			    col);

		files->candidate_count++;	/*TODO this assumes full grid with no null or mask!! But need something to prevent "pathflag" infinite loop */

	    }
	}
	G_debug(4, "Starting to process %d candidate pixels",
		files->candidate_count);

	/*process candidate pixels */

	/*check each pixel, start the processing only if it is a candidate pixel */
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {

		/* G_verbose_message("Completion for pass number %d: ", t); */
		G_percent(row, files->nrows, 1);	/*this didn't get displayed in the output??? Does it get erased when done? */

		G_debug(4,
			"Next starting pixel from next row/col, not from Rk");

		segment_get(&files->out_seg, (void *)files->out_val, row, col);	/*TODO small time savings - if candidate_count reaches zero, bail out of these loops too? */
		if (files->out_val[1] == 1) {	/* out_val[1] is the candidate pixel flag, want to process the 1's */
		    G_debug(4, "going to free memory on linked lists...");
		    /*free memory for linked lists */
		    my_dispose_list(files->token, &Ri_head);
		    my_dispose_list(files->token, &Rk_head);
		    my_dispose_list(files->token, &Rin_head);
		    my_dispose_list(files->token, &Rkn_head);	/* TODO, better style for repeating this for all structures? */
		    Rk_count = 0;
		    G_debug(4, "finished free memory on linked lists...");

		    /* First pixel in Ri is current row/col pixel.  We may add more later if it is part of a segment */
		    Ri_count = 1;
		    newpixel = (struct pixels *)link_new(files->token);
		    newpixel->next = Ri_head;
		    newpixel->row = row;
		    newpixel->col = col;
		    Ri_head = newpixel;

		    pathflag = 1;

		    //      while (pathflag == 1 && files->candidate_count > 0) {   /*if don't find mutual neighbors on first try, will use Rk as next Ri. */

		    G_debug(4, "Next starting pixel: row, %d, col, %d",
			    Ri_head->row, Ri_head->col);

		    /* Setting Ri to be not a candidate allows using "itself" when at edge of raster.
		     * Otherwise need to use a list/count/something to know the number of pixel neighbors */
		    set_candidate_flag(Ri_head, 0, files);	/* TODO: error trap? */
		    G_debug(4, "line 165, \t\t\t\tcc = %d",
			    files->candidate_count);

		    /* what is passed to find segment neighors: */
		    /*    G_debug(4, "calling find_segment_neigors() with:");
		       for (current = Ri_head; current != NULL;
		       current = current->next)
		       G_debug(4, "Ri: row: %d, col: %d", current->row,
		       current->col);
		       for (current = Rin_head; current != NULL;
		       current = current->next)
		       G_debug(4, "Rin: row: %d, col: %d", current->row,
		       current->col);
		       G_debug(4, "also passing Ri_count: %d", Ri_count);
		     */
		    /* find segment neighbors */
		    if (find_segment_neighbors
			(&Ri_head, &Rin_head, &Ri_count, files,
			 functions) != 0) {
			G_fatal_error("find_segment_neighbors() failed");
		    }		/* TODO - shouldn't be just fatal error - need to still close_files().  Just put that here then fatal error? */

		    if (Rin_head == NULL) {
			G_debug(4, "2a, Segment had no valid neighbors");	/*this could happen if there is a segment surrounded by pixels that have already been processed */
			pathflag = 0;
			Ri_count = 0;
			set_candidate_flag(Ri_head, 0, files);	/* TODO: error trap? */
			files->candidate_count++;	/* already counted out Ri[0]; */
			G_debug(4, "line 176, \t\t\t\tcc = %d",
				files->candidate_count);
		    }
		    else {	/*found neighbors, go ahead until find mutually agreeing neighbors */

			G_debug(4, "2b, Found Ri's pixels");
			/*print out neighbors */

			for (current = Ri_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Ri: row: %d, col: %d", current->row,
				    current->col);

			G_debug(4, "2b, Found Ri's neighbors");
			/*print out neighbors */
			for (current = Rin_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Rin: row: %d, col: %d", current->row,
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
			    G_debug(4,
				    "simularity = %g for neighbor : row: %d, col %d.",
				    tempsim, current->row, current->col);
			    if (tempsim < Ri_similarity) {
				Ri_similarity = tempsim;
				Ri_bestn = current;	/*TODO want to point to the current pixel...confirm  when current changes need this to stay put! */
				G_debug(4,
					"Current lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
					Ri_similarity, Ri_bestn->row,
					Ri_bestn->col);
			    }
			}

			if (Ri_bestn != NULL)
			    G_debug(4,
				    "Lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
				    Ri_similarity, Ri_bestn->row,
				    Ri_bestn->col);

			if (Ri_bestn != NULL && Ri_similarity < threshold) {	/* small TODO: should this be < or <= for threshold? */
			    /* we'll have the neighbor pixel to start with. */
			    G_debug(4, "3a: Working with Rk");
			    Rk_count = 1;
			    newpixel =
				(struct pixels *)link_new(files->token);
			    newpixel->next = NULL;	/* or = Rk_head; *//*TODO, should this be Rk_head or just NULL? amounts to the same thing here? */
			    newpixel->row = Ri_bestn->row;
			    newpixel->col = Ri_bestn->col;
			    Rk_head = newpixel;
			    /* TODO - lists starting, should this be a helper function, did at start of Ri and Rk.  */

			    /*Todo: Do we want to put Ri into Rkn ?  Hmm, we don't want to actually check similarity on them when they are in Rkn, since we'll
			     * start with Ri as the initial similarity.  Maybe add a 3rd input list to find_segment_neighbors(), and put them directily into
			     * the no_check list so we avoid a small amount of processing?  But that might take longer then just checking their similarity in the first place! */

			    find_segment_neighbors(&Rk_head, &Rkn_head, &Rk_count, files, functions);	/* data structure for Rk's neighbors, and pixels in Rk if we don't already have it */

			    G_debug(4, "Found Rk's pixels");
			    /*print out neighbors */
			    for (current = Rk_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rk: row: %d, col: %d",
					current->row, current->col);

			    G_debug(4, "Found Rk's neighbors");
			    /*print out neighbors */
			    for (current = Rkn_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rkn: row: %d, col: %d",
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
				merge_values(Ri_head, Rk_head, Ri_count, Rk_count, files);	/* TODO error trap */
				endflag = 0;	/* we've made at least one merge, so need another t iteration */
				pathflag = 0;	/* go to next row,column pixel - end of Rk -> Ri chain since we found mutual best neighbors */
			    }
			    else {	/* they weren't mutually best neighbors */
				G_debug(4,
					"Ri was not Rk's best neighbor, Ri_sim: %g, Rk_sim, %g",
					Ri_similarity, Rk_similarity);

				/* did this at beginning of path loop */
				set_candidate_flag(Ri_head, 0, files);	/* remove all Ri members from candidate pixels (set flag) */
				files->candidate_count++;	/* add one back, we had already set Ri[0] flag at the beginning. */
				G_debug(4, "line 247, \t\t\t\tcc = %d",
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
			}	/*end else (from if mutually best neighbors) */
			else
			    G_debug(4,
				    "3b Rk didn't didn't exist or similarity was > threshold");
		    }		/* end else - Ri did have neighbors */
		    //          }           /*end pathflag do loop */
		}		/*end if pixel is candidate pixel */
	    }			/*next column */
	}			/*next row */

	/* finished one pass for processing candidate pixels */

	G_debug(4, "Finished one pass, t was = %d", t);
	t++;
    } while (t < 90 && endflag == 0);
    /*end t loop *//*TODO, should there be a max t that it can iterate for?  Include t in G_message? */

    /* free memory *//*TODO: anything ? */


    return 0;
}

int find_segment_neighbors(struct pixels **R_head,
			   struct pixels **neighbors_head, int *seg_count,
			   struct files *files, struct functions *functions)
{
    int n, m, Ri_seg_ID = -1;
    struct pixels *newpixel, *current, *to_check;	/* need to check the pixel neighbors of to_check */
    int val_no_check = -1;	/*value of the no_check flag for the particular pixel. */
    int pixel_neighbors[8][2];	/* TODO: data type?  put in files to allocate memory once? */


    /* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
     * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
     * But the list of points would NOT be inclusive - just the points bordering the current segment...
     */

    /* parameter: R, current segment membership, could be single pixel or list of pixels.
     * parameter: neighbors/Rin/Rik, neighbor pixels, could have a list already, or could be empty ?
     * files->out_seg is currently an array [0] for seg ID and [1] for "candidate pixel"
     * files->no_check is a segmentation data structure, if the pixel should no longer be checked on this current find_neighbors() run
     * functions->num_pn  int, 4 or 8, for number of pixel neighbors 
     * */

    /* show what was sent to function *//*
       G_debug(5, "in find_segment_neigors() with:");
       for (current = *R_head; current != NULL; current = current->next)
       G_debug(5, "R: row: %d, col: %d", current->row, current->col);
       for (current = *neighbors_head; current != NULL; current = current->next)
       G_debug(5, "neig: row: %d, col: %d", current->row, current->col);
       G_debug(5, "also passing Ri_count: %d", *seg_count); */

    /*initialize data.... TODO: maybe remember min max row/col that was looked at each time, initialize in open_files, and reset smaller region at end of this functions */
    for (n = 0; n < files->nrows; n++) {
	for (m = 0; m < files->ncols; m++) {
	    val_no_check = 0;
	    segment_put(&files->no_check, &val_no_check, n, m);
	}
    }

    to_check = NULL;

    /* Copy R in to_check and no_check data structures (don't expand them if we find them again) */
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
	G_debug(5,
		"\tfind_pixel_neighbors for row: %d , col %d",
		to_check->row, to_check->col);

	functions->find_pixel_neighbors(to_check->row,
					to_check->col,
					pixel_neighbors, files);

	/* Done using this to_check pixels coords, remove from list */

	current = to_check;	/* temporary store the old head */
	to_check = to_check->next;	/*head now points to the next element in the list */
	link_dispose(files->token, (VOID_T *) current);

	/*print out to_check */
	G_debug(5, "remaining pixel's in to_check, after popping:");
	for (current = to_check; current != NULL; current = current->next)
	    G_debug(5, "to_check... row: %d, col: %d", current->row,
		    current->col);
	for (current = *neighbors_head; current != NULL;
	     current = current->next)
	    G_debug(5, "Rn... row: %d, col: %d", current->row, current->col);

	/*now check the pixel neighbors and add to the lists */

	/*debug what neighbors were found: */
	/*      for (n = 0; n < functions->num_pn; n++){
	   G_debug(5, "\tpixel_neighbors[n][0]: %d, pixel_neighbors[n][1]: %d",  pixel_neighbors[n][0], pixel_neighbors[n][1]);
	   } */

	for (n = 0; n < functions->num_pn; n++) {	/* with pixel neighbors */

	    segment_get(&files->no_check, &val_no_check,
			pixel_neighbors[n][0], pixel_neighbors[n][1]);
	    G_debug(5,
		    "\twith pixel neigh %d, row: %d col: %d, val_no_check = %d",
		    n, pixel_neighbors[n][0], pixel_neighbors[n][1],
		    val_no_check);
	    if (val_no_check == 0) {	/* want to check this neighbor */
		val_no_check = 1;
		segment_put(&files->no_check, &val_no_check, pixel_neighbors[n][0], pixel_neighbors[n][1]);	/* don't check it again */

		segment_get(&files->out_seg, (void *)files->out_val, pixel_neighbors[n][0], pixel_neighbors[n][1]);	/*TODO : do I need a second "out_val" data structure? */

		if (files->out_val[1] == 1) {	/* valid candidate pixel */

		    G_debug(5, "\tfiles->out_val[0] = %d Ri_seg_ID = %d",
			    files->out_val[0], Ri_seg_ID);
		    if (files->out_val[0] == Ri_seg_ID) {
			G_debug(5, "\tputing pixel_neighbor in Ri");
			/* put pixel_neighbor[n] in Ri */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = *R_head;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			*R_head = newpixel;	/*change the first pixel to be the new pixel. */
			*seg_count = *seg_count + 1;	/* zero index... Ri[0] had first pixel and set count =1.  increment after save data. */
			G_debug(5, "\t*seg_count now = %d", *seg_count);

			/* put pixel_neighbor[n] in to_check -- want to check this pixels neighbors */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = to_check;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			to_check = newpixel;	/*change the first pixel to be the new pixel. */

		    }
		    else {	/* segment id's were different */
			/* put pixel_neighbor[n] in Rin */
			G_debug(5, "Put in neighbors_head");
			/* TODO - helper function for adding pixel to a list */
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = *neighbors_head;	/*point the new pixel to the current first pixel */
			newpixel->row = pixel_neighbors[n][0];
			newpixel->col = pixel_neighbors[n][1];
			*neighbors_head = newpixel;	/*change the first pixel to be the new pixel. */

		    }
		}		/*end if valid candidate pixel */
		else
		    G_debug(5,
			    "pixel row: %d col: %d was not a valid candidate pixel",
			    pixel_neighbors[n][0], pixel_neighbors[n][1]);

	    }			/*end if for pixel_neighbor was in "don't check" list */
	}			/* end for loop - next pixel neighbor */
	G_debug(5,
		"remaining pixel's in to_check, after processing the last pixel's neighbors:");
	for (current = to_check; current != NULL; current = current->next)
	    G_debug(5, "to_check... row: %d, col: %d", current->row,
		    current->col);
	G_debug(5, "\t### end of pixel neighors");
    }				/* while to_check has more elements */

    return 0;
}

int find_four_pixel_neighbors(int p_row, int p_col, int pixel_neighbors[8][2],
			      struct files *files)
{
    /*   
       G_debug(5,"\t\tin find 4 pixel neighbors () ");
       G_debug(5,"\t\tpixel row: %d pixel col: %d", p_row, p_col);
       G_debug(5, "\t\tTotal rows: %d, total cols: %d", files->nrows, files->ncols); *//*check that we have files... */

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
    G_warning("Diagonal neighbors Not Implemented");
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
	val =
	    val + (files->bands_val[n] -
		   files->second_val[n]) * (files->bands_val[n] -
					    files->second_val[n]);
    }

    /* val = sqrt(val); *//* use squared distance, save the calculation time */

    return val;

}

int merge_values(struct pixels *Ri_head, struct pixels *Rk_head, int Ri_count,
		 int Rk_count, struct files *files)
{				/* TODO: correct assumption that this should be a weighted mean? */
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


    G_debug(4, "\t\tMerging, segment number: %d, including pixels:",
	    files->out_val[0]);

    /* for each member of Ri and Rk, write new average bands values and segment values */
    for (current = Ri_head; current != NULL; current = current->next) {
	segment_put(&files->bands_seg, (void *)files->bands_val, current->row,
		    current->col);
	segment_put(&files->out_seg, (void *)files->out_val, current->row,
		    current->col);
	files->candidate_count--;
	G_debug(4, "line 508, \t\t\t\tcc = %d", files->candidate_count);
	G_debug(4, "\t\tRi row: %d, col: %d", current->row, current->col);
    }
    for (current = Rk_head; current != NULL; current = current->next) {
	segment_put(&files->bands_seg, (void *)files->bands_val, current->row,
		    current->col);
	segment_put(&files->out_seg, (void *)files->out_val, current->row,
		    current->col);
	files->candidate_count--;
	G_debug(4, "line 516, \t\t\t\tcc = %d", files->candidate_count);
	G_debug(4, "\t\tRk row: %d, col: %d", current->row, current->col);

    }

    files->candidate_count++;	/* had already counted down the starting pixel Ri[0] at the beginning... */
    G_debug(4, "line 522, \t\t\t\tcc = %d", files->candidate_count);
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
	G_debug(4, "line 544, \t\t\t\tcc = %d", files->candidate_count);

    }
    return 0;
}

/* let memory manager know space is available again and reset head to NULL */
int my_dispose_list(struct link_head *token, struct pixels **head)
{
    struct pixels *current;

    while ((*head) != NULL) {
	current = *head;	/* rememer "old" head */
	*head = (*head)->next;	/* move head to next pixel */
	link_dispose(token, (VOID_T *) current);	/* remove "old" head */
    }

    return 0;
}
