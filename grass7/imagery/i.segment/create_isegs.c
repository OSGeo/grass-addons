/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include <grass/linkm.h>	/* memory manager for linked lists */
#include <grass/rbtree.h>	/* Red Black Tree library functions */
#include "iseg.h"

#ifdef DEBUG
	#include <time.h>
#endif

#define LINKM
/* #define REVERSE */

int create_isegs(struct files *files, struct functions *functions)
{
    int lower_bound, upper_bound;
    int successflag = 1;
    struct Range range;

    /* TODO consider if there are _method specific_ parameter set up and memory allocation, should that happen here? */

    G_debug(1, "Threshold: %g", functions->threshold);
    G_debug(1, "segmentation method: %d", functions->method);

    functions->threshold = functions->threshold * functions->threshold * files->nbands;	/* use modified threshold to account for scaled input and to avoid square root in similarity comparison. *//* Todo, small, could put this in main outside of polygon loop */

    /* set parameters for outer processing loop for polygon constraints */
    if (files->bounds_map == NULL) {	/*normal processing */
	lower_bound = upper_bound = 0;
    }				/* just one time through loop */
    else {
	if (Rast_read_range(files->bounds_map, files->bounds_mapset, &range) != 1) {	/* returns -1 on error, 2 on empty range, quiting either way. */
	    G_fatal_error(_("No min/max found in raster map <%s>"),
			  files->bounds_map);
	}
	Rast_get_range_min_max(&range, &lower_bound, &upper_bound);	/* todo, faster way to do this?  maybe do it manually when open and write to the segment file? But it is just once.... */
    }

    for (files->current_bound = lower_bound; files->current_bound <= upper_bound; files->current_bound++) {	/* outer processing loop for polygon constraints */
	G_debug(1, "current_bound = %d", files->current_bound);
	if (functions->method == 0)
	    successflag = io_debug(files, functions);	/* TODO: why does it want `&files` in main, but `files` here ??? */
	else if (functions->method == 1) {
	    G_debug(1, "starting region_growing()");
	    successflag = region_growing(files, functions);
	}
	else if (functions->method == 2)
	    successflag = ll_test(files, functions);
	    
	else if (functions->method == 3)
	    successflag = seg_speed_test(files, functions);

    }				/* end outer loop for processing polygons */

    /* clean up? */


    return successflag;
}

#ifdef DEBUG
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
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    /* files->out_val[0] = col + row; */
	    segment_get(&files->bands_seg, (void *)files->bands_val, row,
			col);
	    files->iseg[row][col] = files->bands_val[0] * 100;	/*pushing DCELL into CELL */
	}
	G_percent(row, files->nrows, 1);
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
    return TRUE;
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
	for (col = 0; col < files->ncols; col++) {
	    /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
	    files->iseg[row][col] = col + row;
	}
	G_percent(row, files->nrows, 1);
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
    return TRUE;
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
    return TRUE;

}

int seg_speed_test(struct files *files, struct functions *functions)
{
	int i, j, k, n, max;
	clock_t start, end;
    double temp, cpu_time_used;
    int (*get) (struct files *, int, int); /* files, row, col */
	struct RB_TREE *no_check_tree, *known_iseg_tree; 
	struct RB_TRAV trav;
	struct pixels *to_check, *newpixel, *current, *tree_pix;
	FLAG *check_flag;
	G_message("checking speed of RAM vs SEG vs get function performance");
	
	G_message("Access in the same region, so shouldn't have any disk I/O");
	
	max = 100000000;
	G_message("repeating everything %d times.", max);
	
	{ /* Array vs. SEG ... when working in local area */
	start = clock();
	for (i=0; i<max; i++){
		segment_get(&files->bands_seg, (void *)files->bands_val, 12, 12);
		temp = files->bands_val[0];
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using SEG: %g", cpu_time_used);
	
	start = clock();
	for (i=0; i<max; i++){
		temp = files->iseg[12][12];
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using array in RAM: %g", cpu_time_used);

	get = &get_segID_SEG;

	start = clock();
	for (i=0; i<max; i++){
		temp = get(files, 12, 12);
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using SEG w/ get(): %g", cpu_time_used);

	get = &get_segID_RAM;

	start = clock();
	for (i=0; i<max; i++){
		temp = get(files, 12, 12);
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using RAM w/ get(): %g", cpu_time_used);
	}
	
	G_message("to check storage requirements... system dependent... :");
	G_message("unsigned char: %lu", sizeof(unsigned char));
	G_message("unsigned char pointer: %lu", sizeof(unsigned char *));
	G_message("int: %lu", sizeof(int));
	G_message("unsigned int: %lu", sizeof(unsigned int));
	G_message("double: %lu", sizeof(double));
	
	
	max = 100000;
	G_message("repeating everything %d times.", max);

	{ /* compare rbtree with linked list and array */

	n = 100;
	start = clock();
	for (i=0; i<max; i++){
		no_check_tree = rbtree_create(compare_ids, sizeof(struct pixels));
		/*build*/
		for(j=0; j<n; j++){
			tree_pix->row = tree_pix->col = j;
			rbtree_insert(no_check_tree, &tree_pix);
		}
		//~ /*access*/
		rbtree_init_trav(&trav, no_check_tree);
		//~ while ((data = rbtree_traverse(&trav)) != NULL) {
			//~ if (my_compare_fn(data, threshold_data) == 0) break;
				//~ G_message("%d", data);
		//~ }
		/*free memory*/
		rbtree_destroy(no_check_tree);
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using rbtree of pixels (just build/destroy), %d elements, time: %g", n, cpu_time_used);

	start = clock();
	for (i=0; i<max; i++){
		known_iseg_tree = rbtree_create(compare_ids, sizeof(int));
		/*build*/
		for(j=0; j<n; j++){
			rbtree_insert(known_iseg_tree, &j);
		}
		//~ /*access*/
		rbtree_init_trav(&trav, known_iseg_tree);
		//~ while ((data = rbtree_traverse(&trav)) != NULL) {
			//~ if (my_compare_fn(data, threshold_data) == 0) break;
				//~ G_message("%d", data);
		//~ }
		/*free memory*/
		rbtree_destroy(known_iseg_tree);
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using rbtree ints (just build/destroy), %d elements, time: %g", n, cpu_time_used);


	to_check = NULL;
	
	start = clock();
	for (i=0; i<max; i++){
		/*build*/
		for(j=0; j<n; j++){
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = to_check;	/*point the new pixel to the current first pixel */
			newpixel->row = j;
			newpixel->col = i;
			to_check = newpixel;	/*change the first pixel to be the new pixel. */
		}
		/*access*/
		for (current = to_check; current != NULL; current = current->next) {	/* for each of Ri's neighbors */
			temp = current->row;
		}
		/*free memory*/
		my_dispose_list(files->token, &to_check);

	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using linked list and linkm (build/access/free), %d elements, time: %g", n, cpu_time_used);

	
	n=1000;
	//repeat for both with larger membership
	
		start = clock();
	for (i=0; i<max; i++){
		known_iseg_tree = rbtree_create(compare_ids, sizeof(int));
		rbtree_init_trav(&trav, known_iseg_tree);

		/*build*/
		for(j=0; j<n; j++){
			rbtree_insert(known_iseg_tree, &j);
		}
		//~ /*access*/
		//~ while ((data = rbtree_traverse(&trav)) != NULL) {
			//~ if (my_compare_fn(data, threshold_data) == 0) break;
				//~ G_message("%d", data);
		//~ }
		/*free memory*/
		rbtree_destroy(known_iseg_tree);
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using rbtree ints, %d elements, time: %g", n, cpu_time_used);

	to_check = NULL;
	
	start = clock();
	for (i=0; i<max; i++){
		/*build*/
		for(j=0; j<n; j++){
			newpixel = (struct pixels *)link_new(files->token);
			newpixel->next = to_check;	/*point the new pixel to the current first pixel */
			newpixel->row = j;
			newpixel->col = i;
			to_check = newpixel;	/*change the first pixel to be the new pixel. */
		}
		/*access*/
		for (current = to_check; current != NULL; current = current->next) {	/* for each of Ri's neighbors */
			temp = current->row;
		}
		/*free memory*/
		my_dispose_list(files->token, &to_check);

	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using linked list and linkm, %d elements, time: %g", n, cpu_time_used);
	
	k=100;
	n=50;
    check_flag = flag_create(k, k);
	start = clock();
	for (i=0; i<max; i++){
		/*set to zero*/
		flag_clear_all(check_flag);
		/*write and access*/
		for(j=0; j<n; j++){
			flag_set(check_flag, j, j);
			temp = flag_get(check_flag, j, j);
		}
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using %d pixel flag array (all cleared), %d elements set and get, time: %g", k*k, n, cpu_time_used);
	

	k=10000;
    check_flag = flag_create(k, k);
	start = clock();
	for (i=0; i<max; i++){
		/*set to zero*/
		flag_clear_all(check_flag);
		/*write and access*/
		for(j=0; j<n; j++){
			flag_set(check_flag, j, j);
			temp = flag_get(check_flag, j, j);
		}
	}
	end = clock();
	cpu_time_used = ((double) (end - start)) / CLOCKS_PER_SEC;
	G_message("Using %d pixel flag array (all cleared), %d elements set and get, time: %g", k*k, n, cpu_time_used);

}
	
	return TRUE;
}

int get_segID_SEG(struct files *files, int row, int col)
{
	segment_get(&files->bands_seg, (void *)files->bands_val, row, col);
	return files->bands_val[0]; /*todo for accurate comparison, is converting double to int a time penalty? */
}

int get_segID_RAM(struct files *files, int row, int col)
{
	return files->iseg[row][col];
}
#endif

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
     * files->token has the "link_head" for linkm: linked list memory allocation.
     * just moved iseg to RAM, bands is in SEG, so probably faster to check for unique. */

    struct pixels *Ri_head, *Rk_head, *Rin_head, *Rkn_head, *current, *newpixel;	/*current will be used to iterate over any of the linked lists. */
    int Ri_count, Rk_count;	/*TODO when to calculate these, currently accumulating during find_neighbor() */
    struct pixels *Ri_bestn;	/* best neighbor pixel for Ri, not used as a linked list, just one pixel... */

    G_verbose_message("Running region growing algorithm");

    t = 1;
    files->candidate_count = 0;

    /*set next pointers to null. */
    Ri_head = NULL;
    Rk_head = NULL;
    Rin_head = NULL;
    Rkn_head = NULL;
    Ri_bestn = NULL;

    /* TODO, want to get a min/max row/col to narrow the processing window ??? */

    do {
	/* do while loop on t to slowly lower threshold. also check that endflag==0 (no merges were made) */

	G_debug(3, "#######   Starting outer do loop! t = %d    #######", t);

	threshold = functions->threshold;	/* TODO, consider making this a function of t. */

	endflag = TRUE;

	/* Set candidate flag to true/1 for all pixels TODO: for polygon/vector constraint, need to just set to true for those being processed */
	if (files->bounds_map == NULL) {	/*normal processing */
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {
		    /* TODO: if we are starting from seeds...and only allow merges between unassigned pixels
		     *  and seeds/existing segments, then this needs an if (and will be very inefficient)
		     * maybe consider the sorted array, btree, map... but the number of seeds could still be high for a large map */
		    if (!(FLAG_GET(files->null_flag, row, col))) {
			FLAG_SET(files->candidate_flag, row, col);	/*candidate pixel flag */

			files->candidate_count++;
		    }		/* Need something to prevent "pathflag" infinite loop */
		}
	    }
	}
	else {			/* polygon constraints/boundaries were supplied, include that criteria.  TODO: this repeats a lot of code, is there a way to combine this check without having too many extra if/etc statements ??? */
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {
		    if (!(FLAG_GET(files->null_flag, row, col))) {

			segment_get(&files->bounds_seg, &files->bounds_val,
				    row, col);

			if (files->bounds_val == files->current_bound) {
			    /*TODO could move this if statement one line up, and only set "1" flags if we can assume all flags are already zero.  (i.e. only get/put the ones we want to set to 1.) */
			    FLAG_SET(files->candidate_flag, row, col);	/*candidate pixel flag */
			    files->candidate_count++;	/*TODO this assumes full grid with no null or mask!! But need something to prevent "pathflag" infinite loop */
			}
			//~ else   !!!TODO is it safe to assume that all flag's are zero at this point?
			//~ FLAG_UNSET(files->candidate_flag, row, col);

		    }
		}
	    }
	}

	G_debug(4, "Starting to process %d candidate pixels",
		files->candidate_count);

	/*process candidate pixels */
	G_verbose_message("Pass %d: ", t);
	/*check each pixel, start the processing only if it is a candidate pixel */
	/* for validation, select one of the two... could make this IFDEF or input parameter */
	/* reverse order 
	 */
#ifdef REVERSE
	for (row = files->nrows - 1; row >= 0; row--) {
		G_percent(files->nrows - row, files->nrows, 1);
	    for (col = files->ncols - 1; col >= 0; col--) {
#else
	for (row = 0; row < files->nrows; row++) {
		G_percent(row, files->nrows, 1);	/* TODO, can a message be included with G_percent? */
	    for (col = 0; col < files->ncols; col++) {
#endif

		G_debug(4,
			"Next starting pixel from next row/col, not from Rk");

		if (FLAG_GET(files->candidate_flag, row, col)) {
		    /*free memory for linked lists */
		    my_dispose_list(files->token, &Ri_head);
		    my_dispose_list(files->token, &Rk_head);
		    my_dispose_list(files->token, &Rin_head);
		    my_dispose_list(files->token, &Rkn_head);	/* TODO, better style for repeating this for all structures? */
		    Rk_count = 0;

		    /* First pixel in Ri is current row/col pixel.  We may add more later if it is part of a segment */
		    Ri_count = 1;
		    newpixel = (struct pixels *)link_new(files->token);
		    newpixel->next = NULL;
		    newpixel->row = row;
		    newpixel->col = col;
		    Ri_head = newpixel;

		    pathflag = TRUE;

		    //      while (pathflag == TRUE && files->candidate_count > 0) {   /*if don't find mutual neighbors on first try, will use Rk as next Ri. */

		    G_debug(4, "Next starting pixel: row, %d, col, %d",
			    Ri_head->row, Ri_head->col);

		    /* Setting Ri to be not a candidate allows using "itself" when at edge of raster. TODO THIS NEEDS TO BE CHANGED!!!!
		     * Otherwise need to use a list/count/something to know the number of pixel neighbors */
		    set_candidate_flag(Ri_head, FALSE, files);	/* TODO: error trap? */
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
			 functions) != TRUE) {
			G_fatal_error("find_segment_neighbors() failed");
		    }

		    if (Rin_head == NULL) {
			G_debug(4, "2a, Segment had no valid neighbors");	/*this could happen if there is a segment surrounded by pixels that have already been processed */
			pathflag = FALSE;
			Ri_count = 0;
			set_candidate_flag(Ri_head, FALSE, files);	/* TODO: error trap? */
			files->candidate_count++;	/* already counted out Ri[0]; */
			G_debug(4, "line 176, \t\t\t\tcc = %d",
				files->candidate_count);
		    }
		    else {	/*found neighbors, go ahead until find mutually agreeing neighbors */

			G_debug(4, "2b, Found Ri's pixels");
			#ifdef DEBUG
			/*print out neighbors */
			for (current = Ri_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Ri: row: %d, col: %d", current->row,
				    current->col);
			#endif
			G_debug(4, "2b, Found Ri's neighbors");
			#ifdef DEBUG
			/*print out neighbors */
			for (current = Rin_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Rin: row: %d, col: %d", current->row,
				    current->col);
			#endif

			/* find Ri's most similar neighbor */
			Ri_bestn = NULL;
			Ri_similarity = threshold + 1;	/* set current similarity to max value */
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

			if (Ri_bestn != NULL) {
			    G_debug(4,
				    "Lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
				    Ri_similarity, Ri_bestn->row,
				    Ri_bestn->col);

			    //~ segment_get(&files->out_seg,
			    //~ (void *)files->out_val, Ri_bestn->row,
			    //~ Ri_bestn->col);
			    if (!
				(FLAG_GET
				 (files->candidate_flag, Ri_bestn->row,
				  Ri_bestn->col)))
				/* this check is important:
				 * best neighbor is not a valid candidate, was already merged earlier in this time step */
				Ri_bestn = NULL;
			}

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
			    #ifdef DEBUG
			    /*print out neighbors */
			    for (current = Rk_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rk: row: %d, col: %d",
					current->row, current->col);
				#endif
			    G_debug(4, "Found Rk's neighbors");
			    #ifdef DEBUG
			    /*print out neighbors */
			    for (current = Rkn_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rkn: row: %d, col: %d",
					current->row, current->col);
				#endif
				
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
				endflag = FALSE;	/* we've made at least one merge, so need another t iteration */
				pathflag = FALSE;	/* go to next row,column pixel - end of Rk -> Ri chain since we found mutual best neighbors */
			    }
			    else {	/* they weren't mutually best neighbors */
				G_debug(4,
					"Ri was not Rk's best neighbor, Ri_sim: %g, Rk_sim, %g",
					Ri_similarity, Rk_similarity);

				/* did this at beginning of path loop */
				set_candidate_flag(Ri_head, FALSE, files);	/* remove all Ri members from candidate pixels (set flag) */
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
			else {
			    /* no valid best neighbor for this Ri
			     * exclude this Ri from further comparisons 
			     * because we checked already Ri for a mutually best neighbor with all valid candidates
			     * thus Ri can not be the mutually best neighbor later on during this pass
			     * unfortunately this does happen sometimes */
			    set_candidate_flag(Ri_head, FALSE, files);	/* TODO: error trap? */
			    files->candidate_count++;	/*first pixel was already set */
			    G_debug(4,
				    "3b Rk didn't didn't exist, was not valid candidate, or similarity was > threshold");
			}	/*end else - Ri's best neighbor was not a candidate */
		    }		/* end else - Ri did have neighbors */
		    //          }           /*end pathflag do loop */
		}		/*end if pixel is candidate pixel */
	    }			/*next column */
#ifdef REVERSE
	    G_percent(files->nrows - row, files->nrows, 1);
#else
	    G_percent(row, files->nrows-1, 1);	/* TODO, can a message be included with G_percent? */
#endif
	    /* TODO, the REVERSE version gets printed on a new line, and isnt' covered.  The else version is. ? */
	    /* TODO, shows up in CLI, not in GUI */

#ifdef NODEF
	}
    }
    /* to balance brackets in first ifdef statement */
#endif

    }				/*next row */
    /* finished one pass for processing candidate pixels */

    G_debug(4, "Finished one pass, t was = %d", t);
    t++;
    } while (t <= functions->end_t && endflag == FALSE);
    /*end t loop *//*TODO, should there be a max t that it can iterate for?  Include t in G_message? */
    
	if(endflag == FALSE) G_message(_("Merging processes stopped due to reaching max iteration limit, more merges may be possible"));


	/* ****************************************************************************************** */
	/* final pass, ignore threshold and force a merge for small segments with their best neighbor */
	/* ****************************************************************************************** */
	
	
	if (functions->min_segment_size > 1) {
		G_verbose_message("Final iteration, force merges for small segments.");
		
		/* TODO: It would be possible to use some sort of "forced merge" flag and if statements in the above code.
 * This might be easier to maintain... but I wasn't sure which would be easier to read
 * and it would add some extra if statements to each iteration...
 * 
 * for the final forced merge, the candidate flag is just to keep track if we have confirmed if:
 * 		a. the segment size is >= to the minimum allowed size  or
 * 		b. we have merged it with its best neighbor
 */
	/* TODO: repeating this twice, move to helper function? */
	
	/* Set candidate flag to true/1 for all pixels TODO: for polygon/vector constraint, need to just set to true for those being processed */
	if (files->bounds_map == NULL) {	/*normal processing */
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {
		    /* TODO: if we are starting from seeds...and only allow merges between unassigned pixels
		     *  and seeds/existing segments, then this needs an if (and will be very inefficient)
		     * maybe consider the sorted array, btree, map... but the number of seeds could still be high for a large map */
		    if (!(FLAG_GET(files->null_flag, row, col))) {
			FLAG_SET(files->candidate_flag, row, col);	/*candidate pixel flag */

			files->candidate_count++;
		    }		/* Need something to prevent "pathflag" infinite loop */
		}
	    }
	}
	else {			/* polygon constraints/boundaries were supplied, include that criteria.  TODO: this repeats a lot of code, is there a way to combine this check without having too many extra if/etc statements ??? */
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {
		    if (!(FLAG_GET(files->null_flag, row, col))) {

			segment_get(&files->bounds_seg, &files->bounds_val,
				    row, col);

			if (files->bounds_val == files->current_bound) {
			    /*TODO could move this if statement one line up, and only set "1" flags if we can assume all flags are already zero.  (i.e. only get/put the ones we want to set to 1.) */
			    FLAG_SET(files->candidate_flag, row, col);	/*candidate pixel flag */
			    files->candidate_count++;	/*TODO this assumes full grid with no null or mask!! But need something to prevent "pathflag" infinite loop */
			}
			//~ else   !!!TODO is it safe to assume that all flag's are zero at this point?
			//~ FLAG_UNSET(files->candidate_flag, row, col);

		    }
		}
	    }
	}


	for (row = 0; row < files->nrows; row++) {
	for (col = 0; col < files->ncols; col++) {

		if (FLAG_GET(files->candidate_flag, row, col)) {
		    /*free memory for linked lists */
		    my_dispose_list(files->token, &Ri_head);
		    my_dispose_list(files->token, &Rk_head);
		    my_dispose_list(files->token, &Rin_head);
		    my_dispose_list(files->token, &Rkn_head);
		    Rk_count = 0;

		    /* First pixel in Ri is current row/col pixel.  We may add more later if it is part of a segment */
		    Ri_count = 1;
		    newpixel = (struct pixels *)link_new(files->token);
		    newpixel->next = Ri_head;
		    newpixel->row = row;
		    newpixel->col = col;
		    Ri_head = newpixel;

		    G_debug(4, "Next starting pixel: row, %d, col, %d",
			    Ri_head->row, Ri_head->col);

		    set_candidate_flag(Ri_head, FALSE, files);	/* TODO: error trap? */
		    G_debug(4, "line 165, \t\t\t\tcc = %d",
			    files->candidate_count);

		    /* find segment neighbors */
		    if (find_segment_neighbors
			(&Ri_head, &Rin_head, &Ri_count, files,
			 functions) != TRUE) {
			G_fatal_error("find_segment_neighbors() failed");
		    }

		    if (Rin_head != NULL)  /*found neighbors */
		    {
				if (Ri_count >= functions->min_segment_size) /* don't force a merge */
					set_candidate_flag(Ri_head, FALSE, files);
					
				else /* Merge with most similar neighbor */
				{
					//~ TODO DELETE?
					//~ G_debug(4, "2b, Found Ri's pixels");
					//~ 
					//~ /*print out neighbors */
					//~ for (current = Ri_head; current != NULL;
						 //~ current = current->next)
						//~ G_debug(4, "Ri: row: %d, col: %d", current->row,
							//~ current->col);
//~ 
					//~ G_debug(4, "2b, Found Ri's neighbors");
					//~ /*print out neighbors */
					//~ for (current = Rin_head; current != NULL;
						 //~ current = current->next)
						//~ G_debug(4, "Rin: row: %d, col: %d", current->row,
							//~ current->col);

					/* find Ri's most similar neighbor */
					Ri_bestn = NULL;
					Ri_similarity = threshold + 1;	/* set current similarity to max value */
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
				
					if (Ri_bestn != NULL)
					{
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

						/* using this just to get the full pixel/cell membership list for Rk */
						find_segment_neighbors(&Rk_head, &Rkn_head, &Rk_count, files, functions);	/* data structure for Rk's neighbors, and pixels in Rk if we don't already have it */

//~ TODO DELETE?
						//~ G_debug(4, "Found Rk's pixels");
						//~ /*print out neighbors */
						//~ for (current = Rk_head; current != NULL;
						 //~ current = current->next)
						//~ G_debug(4, "Rk: row: %d, col: %d",
							//~ current->row, current->col);
//~ 
						//~ G_debug(4, "Found Rk's neighbors");
						//~ /*print out neighbors */
						//~ for (current = Rkn_head; current != NULL;
						 //~ current = current->next)
						//~ G_debug(4, "Rkn: row: %d, col: %d",
							//~ current->row, current->col);

						merge_values(Ri_head, Rk_head, Ri_count, Rk_count, files);	/* TODO error trap */

						/* merge_values sets Ri and Rk candidate flag to FALSE.  Put Rk back to TRUE if the size is too small. */
						if(Ri_count + Rk_count < functions->min_segment_size)
							set_candidate_flag(Rk_head, TRUE, files);
					} /* end if best neighbor != null */
					else
					G_warning("No best neighbor found in final merge, this shouldn't happen?");
					
					
				}		/* end else - pixel count was below minimum allowed */
		    } /* end if neighbors found */
		    else{ /* no neighbors were found */
				G_warning("no neighbors found, this means only one segment was created.");
				set_candidate_flag(Ri_head, FALSE, files);
		    }
		}		/*end if pixel is candidate pixel */
	}			/*next column */
	G_percent(row, files->nrows-1, 1);
    }			/*next row */
	} /* end if for force merge */
	else
		G_message(_("Input for minimum pixels in a segment was 1, skipping final iteration for joining small segments."));

    /* free memory *//*TODO: anything ? */


    return TRUE;
    }

    int find_segment_neighbors(struct pixels **R_head,
			       struct pixels **neighbors_head, int *seg_count,
			       struct files *files,
			       struct functions *functions)
    {
	int n, current_seg_ID, Ri_seg_ID = -1;
	struct pixels *newpixel, *current, *to_check, tree_pix;	/* need to check the pixel neighbors of to_check */
	int pixel_neighbors[8][2];	/* TODO: data type? use list instead?  put in files to allocate memory once? */
	
//TODO remove...	/* files->no_check is a FLAG structure, only used here but allocating memory in open_files */
	struct RB_TREE *no_check_tree; /* pixels that should no longer be checked on this current find_neighbors() run */
	struct RB_TREE *known_iseg;
#ifdef DEBUG
	struct RB_TRAV trav;
#endif
	
	/* TODO, any time savings to move any variables to files (mem allocation in open_files) */

	/* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
	 * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
	 * But the list of points would NOT be inclusive - just the points bordering the current segment...
	 */

	/* parameter: R, current segment membership, could be single pixel or list of pixels.
	 * parameter: neighbors/Rin/Rik, neighbor pixels, could have a list already, or could be empty ?
	 * functions->num_pn  int, 4 or 8, for number of pixel neighbors 
	 * */

	/* show what was sent to function *//*
	   G_debug(5, "in find_segment_neigors() with:");
	   for (current = *R_head; current != NULL; current = current->next)
	   G_debug(5, "R: row: %d, col: %d", current->row, current->col);
	   for (current = *neighbors_head; current != NULL; current = current->next)
	   G_debug(5, "neig: row: %d, col: %d", current->row, current->col);
	   G_debug(5, "also passing Ri_count: %d", *seg_count); */

	/* *** initialize data *** */
	
	/* get Ri's segment ID */
	Ri_seg_ID = files->iseg[(*R_head)->row][(*R_head)->col];
	
//	flag_clear_all(files->no_check);
	no_check_tree = rbtree_create(compare_pixels, sizeof(struct pixels));
	known_iseg = rbtree_create(compare_ids, sizeof(int));
	to_check = NULL;

	/* Copy R in to_check and no_check data structures (don't expand them if we find them again) */

	for (current = *R_head; current != NULL; current = current->next) {
		/* put in to_check linked list */
	    newpixel = (struct pixels *)link_new(files->token);
	    newpixel->next = to_check;	/*point the new pixel to the current first pixel */
	    newpixel->row = current->row;
	    newpixel->col = current->col;
	    to_check = newpixel;	/*change the first pixel to be the new pixel. */
	
		/* put in no_check tree */
		tree_pix.row = current->row;
		tree_pix.col = current->col;
		if(rbtree_insert(no_check_tree, &tree_pix)==0)	/* don't check it again */
			G_warning("could not insert data!?");

		//todo delete	    flag_set(files->no_check, current->row, current->col);
	
	}	
	
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
	    #ifdef DEBUG
	    G_debug(5, "remaining pixel's in to_check, after popping:");
	    for (current = to_check; current != NULL; current = current->next)
		G_debug(5, "to_check... row: %d, col: %d", current->row,
			current->col);
	    for (current = *neighbors_head; current != NULL;
		 current = current->next)
		G_debug(5, "Rn... row: %d, col: %d", current->row,
			current->col);
		#endif
		
	    /*now check the pixel neighbors and add to the lists */

	    /*debug what pixel neighbors were found: */
	    /*      for (n = 0; n < functions->num_pn; n++){
	       G_debug(5, "\tpixel_neighbors[n][0]: %d, pixel_neighbors[n][1]: %d",  pixel_neighbors[n][0], pixel_neighbors[n][1]);
	       } */

	    for (n = 0; n < functions->num_pn; n++) {	/* with pixel neighbors */

		// TODO delete   if (flag_get(files->no_check, pixel_neighbors[n][0], pixel_neighbors[n][1]) == FALSE) 
		tree_pix.row = pixel_neighbors[n][0];
		tree_pix.col = pixel_neighbors[n][1];
		G_debug(5, "\tcurrent_seg_ID = %d", current_seg_ID);
		G_debug(5, "********* rbtree_find(no_check_tree, &tree_pix) = %p", rbtree_find(no_check_tree, &tree_pix)); 
		G_debug(5, "if evaluation: %d", rbtree_find(no_check_tree, &tree_pix) == FALSE);

		if(rbtree_find(no_check_tree, &tree_pix) == FALSE) {	/* want to check this neighbor */
			current_seg_ID = files->iseg[pixel_neighbors[n][0]][pixel_neighbors[n][1]];		

		    rbtree_insert(no_check_tree, &tree_pix);	/* don't check it again */

		    if (!(FLAG_GET(files->null_flag, pixel_neighbors[n][0], pixel_neighbors[n][1]))) {	/* all pixels, not just valid pixels */

				G_debug(5, "\tfiles->iseg[][] = %d Ri_seg_ID = %d",
					files->
					iseg[pixel_neighbors[n][0]][pixel_neighbors[n]
									[1]], Ri_seg_ID);
									
				if(current_seg_ID == Ri_seg_ID) { /* pixel is member of current segment, add to R */
					G_debug(5, "\tputing pixel_neighbor in Ri");
					/* put pixel_neighbor[n] in Ri */
					newpixel =
					(struct pixels *)link_new(files->token);
					newpixel->next = *R_head;	/*point the new pixel to the current first pixel */
					newpixel->row = pixel_neighbors[n][0];
					newpixel->col = pixel_neighbors[n][1];
					*R_head = newpixel;	/*change the first pixel to be the new pixel. */
					*seg_count = *seg_count + 1;	/* zero index... Ri[0] had first pixel and set count =1.  increment after save data. */
					G_debug(5, "\t*seg_count now = %d", *seg_count);

					/* put pixel_neighbor[n] in to_check -- want to check this pixels neighbors */
					newpixel =
					(struct pixels *)link_new(files->token);
					newpixel->next = to_check;	/*point the new pixel to the current first pixel */
					newpixel->row = pixel_neighbors[n][0];
					newpixel->col = pixel_neighbors[n][1];
					to_check = newpixel;	/*change the first pixel to be the new pixel. */

				}
				else {	/* segment id's were different */
					//if current ID not found in known neighbors list
						//add to known neighbors list
						/* put pixel_neighbor[n] in Rin */
						G_debug(5, "Put in neighbors_head");
						/* TODO - helper function for adding pixel to a list */
						newpixel =
						(struct pixels *)link_new(files->token);
						newpixel->next = *neighbors_head;	/*point the new pixel to the current first pixel */
						newpixel->row = pixel_neighbors[n][0];
						newpixel->col = pixel_neighbors[n][1];
						*neighbors_head = newpixel;	/*change the first pixel to be the new pixel. */
					//}

				}
		    }		/*end if not a null pixel */
		    else
			G_debug(5,
				"pixel row: %d col: %d was a null pixel",
				pixel_neighbors[n][0], pixel_neighbors[n][1]);

		}		/*end if for pixel_neighbor was in "don't check" list */
	    }			/* end for loop - next pixel neighbor */
	    #ifdef DEBUG
	    G_debug(5,
		    "remaining pixel's in to_check, after processing the last pixel's neighbors:");
	    for (current = to_check; current != NULL; current = current->next)
			G_debug(5, "to_check... row: %d, col: %d", current->row,
				current->col);
	
	    G_debug(5, "\t### end of pixel neighors");
	    #endif
	}			/* while to_check has more elements */

	/* TODO - anything to free??? */
	/* clean up */
	rbtree_destroy(no_check_tree);

	return TRUE;
    }

    int find_four_pixel_neighbors(int p_row, int p_col,
				  int pixel_neighbors[8][2],
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
	return TRUE;
    }

    int find_eight_pixel_neighbors(int p_row, int p_col,
				   int pixel_neighbors[8][2],
				   struct files *files)
    {
	/* get the 4 orthogonal neighbors */
	find_four_pixel_neighbors(p_row, p_col, pixel_neighbors, files);

	/* get the 4 diagonal neighbors */
	G_warning("Diagonal neighbors Not Implemented");
	/*TODO... continue as above? or "nicer" way to do it? */
	return TRUE;
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
	segment_get(&files->bands_seg, (void *)files->second_val, b->row,
		    b->col);

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

    int merge_values(struct pixels *Ri_head, struct pixels *Rk_head,
		     int Ri_count, int Rk_count, struct files *files)
    {				/* TODO: correct assumption that this should be a weighted mean? */
	int n;
	struct pixels *current;

	/*get input values, maybe if handle earlier gets correctly this can be avoided. */
	segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row,
		    Ri_head->col);
	segment_get(&files->bands_seg, (void *)files->second_val,
		    Rk_head->row, Rk_head->col);

	for (n = 0; n < files->nbands; n++) {
	    files->bands_val[n] =
		(files->bands_val[n] * Ri_count +
		 files->second_val[n] * Rk_count) / (Ri_count + Rk_count);
	}

	/* update segment number and candidate flag ==0 */

	G_debug(4, "\t\tMerging, segment number: %d, including pixels:",
		files->iseg[Ri_head->row][Ri_head->col]);

	/* for each member of Ri and Rk, write new average bands values and segment values */
	for (current = Ri_head; current != NULL; current = current->next) {
	    segment_put(&files->bands_seg, (void *)files->bands_val,
			current->row, current->col);
	    FLAG_UNSET(files->candidate_flag, current->row, current->col);	/*candidate pixel flag, only one merge allowed per t iteration */
	    files->candidate_count--;
	    G_debug(4, "line 508, \t\t\t\tcc = %d", files->candidate_count);
	    G_debug(4, "\t\tRi row: %d, col: %d", current->row, current->col);
	}
	for (current = Rk_head; current != NULL; current = current->next) {
	    segment_put(&files->bands_seg, (void *)files->bands_val,
			current->row, current->col);
	    files->iseg[current->row][current->col] =
		files->iseg[Ri_head->row][Ri_head->col];
	    FLAG_UNSET(files->candidate_flag, current->row, current->col);
	    files->candidate_count--;
	    G_debug(4, "line 516, \t\t\t\tcc = %d", files->candidate_count);
	    G_debug(4, "\t\tRk row: %d, col: %d", current->row, current->col);

	}

	files->candidate_count++;	/* had already counted down the starting pixel Ri[0] at the beginning... */
	G_debug(4, "line 522, \t\t\t\tcc = %d", files->candidate_count);
	return TRUE;
    }

    /* TODO.. helper function, maybe make more general? */
    /* todo, not using this in all cases, plus this used to be more complicated but now is two lines.  maybe get rid of this function. */
    /* besides setting flag, also increments how many pixels remain to be processed */
    int set_candidate_flag(struct pixels *head, int value,
			   struct files *files)
    {
	/* head is linked list of pixels, value is new value of flag */
	struct pixels *current;

	for (current = head; current != NULL; current = current->next) {


	    if (value == FALSE) {
		FLAG_UNSET(files->candidate_flag, current->row, current->col);
		files->candidate_count--;
	    }
	    else if (value == TRUE) {
		FLAG_SET(files->candidate_flag, current->row, current->col);
		files->candidate_count++;
	    }
	    else
		G_fatal_error
		    ("programming bug, helper function called with invalid argument");

	    G_debug(4, "line 544, \t\t\t\tcc = %d", files->candidate_count);
	}
	return TRUE;
    }

    /* let memory manager know space is available again and reset head to NULL */
    int my_dispose_list(struct link_head *token, struct pixels **head)
    {
	struct pixels *current;

	while ((*head) != NULL) {
	    current = *head;	/* remember "old" head */
	    *head = (*head)->next;	/* move head to next pixel */
	    link_dispose(token, (VOID_T *) current);	/* remove "old" head */
	}

	return TRUE;
    }

/* function used by binary tree to compare items */

/* TODO
 * "static" was used in break_polygons.c  extern was suggested in docs.  */

int compare_ids(const void *first, const void *second)
{
	int *a = (int *)first, *b = (int *)second;

	if (*a < *b)
		return -1;
	else if (*a > *b)
		return 1;
	else if (*a == *b)
		return 0;
	
	
	G_warning(_("find neighbors: Bug in binary tree!"));
	return 1;
	
}

int compare_pixels(const void *first, const void *second)
{
	struct pixels *a = (struct pixels *)first, *b = (struct pixels *)second;

	if (a->row < b->row)
		return -1;
	else if (a->row > b->row)
		return 1;
	//else if (*a->row == *b->row) todo - a little faster to use else.  But what if (can) a null pixel be passed?
	else {
            /* same row */
	    if (a->col < b->col)
		    return -1;
	    else if (a->col > b->col)
		    return 1;
        }
	/* same row and col todo, same as above, need an == check to be sure?*/
	return 0;
}
