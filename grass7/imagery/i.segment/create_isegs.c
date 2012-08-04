/* PURPOSE:      Develop the image segments */

/* Currently only region growing is implemented */

#include <stdlib.h>
#include <float.h>		/* for DBL_MAX */
#include <math.h>		/* for fabs() */
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include <grass/segment.h>	/* segmentation library */
#include <grass/linkm.h>	/* memory manager for linked lists */
#include <grass/rbtree.h>	/* Red Black Tree library functions */
#include "iseg.h"

#include <time.h>		//todo polish...remove at end

#ifdef DEBUG
#include <limits.h>
#endif

#define LINKM
#define ROWMAJOR		//gave nesting error with INDENT program since this changes the for loops

int create_isegs(struct files *files, struct functions *functions)
{
    int lower_bound, upper_bound, row, col;
    int successflag = 1;
    struct Range range;

    /* todo double check this for different distance measurements and numbers of bands. */
    if (functions->calculate_similarity == calculate_euclidean_similarity)
	functions->threshold = functions->threshold * functions->threshold * files->nbands;	/* use modified threshold to account multiple input bands and to avoid square root in similarity comparison. */
    else
	functions->threshold = functions->threshold * files->nbands;	/* use modified threshold to account for multiple input bands. */


    /* set parameters for outer processing loop for polygon constraints */
    if (files->bounds_map == NULL) {	/*normal processing */
	lower_bound = upper_bound = 0;	/* so run the segmentation algorithm just one time */
    }
    else {
	if (Rast_read_range(files->bounds_map, files->bounds_mapset, &range) != 1) {	/* returns -1 on error, 2 on empty range, quiting either way. */
	    G_fatal_error(_("No min/max found in raster map <%s>"),
			  files->bounds_map);
	}
	Rast_get_range_min_max(&range, &lower_bound, &upper_bound);
	/* TODO polish, should we instead/also get unique values?
	 * As is, we will iterate at least one time over the entire raster for each integer between the upper and lower bound. */
    }

    /* processing loop for polygon/boundary constraints */
    if (files->bounds_map != NULL)
	G_message(_("Running region growing algorithm, the percent completed is based the range of values in the boundary constraints map"));
    for (files->current_bound = lower_bound;
	 files->current_bound <= upper_bound; files->current_bound++) {

	if (files->bounds_map != NULL)
	    G_percent(files->current_bound - lower_bound,
		      upper_bound - lower_bound, 1);

	/* *** check the processing window *** */

	/* set boundaries at "opposite" end, change until reach lowest/highest */
	files->minrow = files->nrows;
	files->mincol = files->ncols;
	files->maxrow = files->maxcol = 0;

	if (files->bounds_map == NULL) {
	    /* check the NULL flag to see where the first/last row/col of real data are, and reduce the processing window.
	     * This could help (a little?) if a MASK is used that removes a large border portion of the map. */
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {

		    if (!(FLAG_GET(files->null_flag, row, col))) {

			if (files->minrow > row)
			    files->minrow = row;
			if (files->maxrow < row)
			    files->maxrow = row;
			if (files->mincol > col)
			    files->mincol = col;
			if (files->maxcol < col)
			    files->maxcol = col;
		    }
		}
	    }
	}
	else {
	    for (row = 0; row < files->nrows; row++) {
		for (col = 0; col < files->ncols; col++) {

		    segment_get(&files->bounds_seg, &files->bounds_val, row,
				col);
		    if (files->bounds_val == files->current_bound &&
			!(FLAG_GET(files->orig_null_flag, row, col))) {
			FLAG_UNSET(files->null_flag, row, col);

			if (files->minrow > row)
			    files->minrow = row;
			if (files->maxrow < row)
			    files->maxrow = row;
			if (files->mincol > col)
			    files->mincol = col;
			if (files->maxcol < col)
			    files->maxcol = col;

		    }
		    else	/* pixel is outside the current boundary or was null in the input bands */
			FLAG_SET(files->null_flag, row, col);
		}
	    }

	    /* clear candidate flag, so only need to reset the processing area on each iteration. todo polish, can be removed after all loops only cover the processing area */
	    flag_clear_all(files->candidate_flag);

	}			/* end of else, set up for bounded segmentation */

	/* consider maxrow/maxcol as nrow, ncol, loops will have: row < maxrow
	 * so need to increment by one */
	files->maxrow++;
	files->maxcol++;
	G_debug(1,
		"minrow: %d, maxrow: %d, nrows: %d, mincol: %d, maxcol: %d, ncols: %d",
		files->minrow, files->maxrow, files->nrows, files->mincol,
		files->maxcol, files->ncols);

	/* run the segmentation algorithm */

	if (functions->method == 1) {
	    successflag = region_growing(files, functions);
	}
#ifdef DEBUG
	else if (functions->method == 0)
	    successflag = io_debug(files, functions);
	else if (functions->method == 2)
	    successflag = ll_test(files, functions);
	else if (functions->method == 3)
	    successflag = seg_speed_test(files, functions);
#endif
    }				/* end outer loop for processing polygons */

    /* reset null flag to the original if we have boundary constraints */
    if (files->bounds_map != NULL) {
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
		if (FLAG_GET(files->orig_null_flag, row, col))
		    FLAG_SET(files->null_flag, row, col);
		else
		    FLAG_UNSET(files->null_flag, row, col);
	    }
	}
    }


    return successflag;		/* todo, successflag was assuming one pass... don't have anything to pick up a failure if there is a bounds constraint */
}

#ifdef DEBUG
/* writes row+col to the output raster.  Also using for the linkm speed test. */
int io_debug(struct files *files, struct functions *functions)
{
    int row, col;

    /* from speed.c to test speed of malloc vs. memory manager */
    unsigned long int z, end_z;	// depending on shape of the rectangle...will need a larger max i.  long long is avail in C99 spec...
    register int i, j;
    int s;
    struct link_head *head;
    struct pixels *p;

    /* **************write fake data to test I/O portion of module */

    /*    G_verbose_message("writing fake data to segmentation file"); */
    G_verbose_message("writing scaled input (layer 1) to output file");
    G_verbose_message("weighted flag = %d", files->weighted);
    //~ for (row = 0; row < files->nrows; row++) {
    //~ for (col = 0; col < files->ncols; col++) {
    //~ /*files->out_val[0] = files->out_val[0]; *//*segment number *//* just copying the map for testing. */
    //~ /* files->out_val[0] = col + row; */
    //~ segment_get(&files->bands_seg, (void *)files->bands_val, row,
    //~ col);
    //~ files->iseg[row][col] = files->bands_val[0] * 100;      /*pushing DCELL into CELL */
    //~ }
    //~ G_percent(row, files->nrows, 1);
    //~ }

    /* Trying out peano ordering */
    /* idea is for large maps, if the width of SEG tiles in RAM is less than the width of the map, this should avoid a lot of I/O */
    /* this is probably closer to a z-order curve then peano order. */

    s = -1;
    /*blank slate */
    for (row = 0; row < files->nrows; row++) {
	for (col = 0; col < files->ncols; col++) {
	    //files->iseg[row][col] = -1;
	    segment_put(&files->iseg_seg, &s, row, col);
	}
    }
    s = 0;

    //~ for(i=1; i<9; i++)
    //~ {
    //~ G_message("i: %d", i);
    //~ for(j=4; j>=0; j--){
    //~ G_message("\tj=%d, 1 & (i >> j) = %d", j, 1 & (i >> j));
    //~ }
    //~ }

    /* need to get a "square" power of 2 around our processing area */

    /*largest dimension: */
    if (files->nrows > files->ncols)
	end_z = files->nrows;
    else
	end_z = files->ncols;

    /* largest power of 2: */
    end_z--;			/* in case we are already a power of two. */
    end_z = (end_z >> 1) | end_z;
    end_z = (end_z >> 2) | end_z;
    end_z = (end_z >> 4) | end_z;
    end_z = (end_z >> 8) | end_z;
    end_z = (end_z >> 16) | end_z;
    end_z = (end_z >> 32) | end_z;	/* only for 64-bit architecture TODO, would this mess things up on 32? */
    /*todo does this need to repeat more since it is long unsigned??? */
    end_z++;

    /*squared: */
    end_z *= end_z;

    for (z = 0; z < end_z; z++) {	// if square and power of 2: files->nrows*files->ncols
	row = col = 0;
	/*bit wise construct row and col from i */
	for (j = 8 * sizeof(long int) - 1; j > 1; j--) {
	    row = row | (1 & (z >> j));
	    row = row << 1;
	    j--;
	    col = col | (1 & (z >> j));
	    col = col << 1;
	}
	row = row | (1 & (z >> j));
	j--;
	col = col | (1 & (z >> j));
	G_message("Done: z: %li, row: %d, col: %d", z, row, col);
	if (row >= files->nrows || col >= files->ncols)
	    continue;

	segment_put(&files->iseg_seg, &s, row, col);
	s++;
    }


    //~ for(i=0; i<8; i++){ //files->nrows*files->ncols
    //              G_message("i: %d", i);
    //~ row=col=0;
    //~ 
    //~ /*bit wise construct row and col from i*/
    //~ for(j=4; j>0; j=j-2){  //8*sizeof(int)
    //                      G_message("j: %d", j);
    //~ row = row | ( i & (1 << (2 * j))); /* row | a[rmax-r]; */
    //~ row = row << 1;
    //~ col = col | ( i & (1 << (2 * j + 1)));
    //~ col = col << 1;
    //~ G_message("j: %d, row: %d, col: %d", j, row, col);
    //~ }
    //~ row = row | ( i & (1 << (2 * j))); /* row | a[rmax-r]; */
    //~ col = col | ( i & (1 << ((2 * j) + 1)));
    //~ G_message("(1 << ((2 * j) + 1)) = %d", (1 << ((2 * j) + 1)));
    //~ G_message("Done: i: %d, row: %d, col: %d", i, row, col);
    //~ files->iseg[row][col] = s;
    //~ s++;
    //~ }



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
	    //~ files->iseg[row][col] = col + row;
	    //todo need variable if this speed test will be used again..
	    //segment_put(&files->iseg_seg, (void *)s, row, col);
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
	    current = Rin_head;	/* remember "old" head */
	    Rin_head = Rin_head->next;	/* move head to next pixel */
	    link_dispose(files->token, (VOID_T *) current);	/* remove "old" head */
	}

	G_message("are they gone?");
	for (current = Rin_head; current != NULL; current = current->next)
	    G_message("Rin: row: %d, col: %d", current->row, current->col);

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
    int (*get) (struct files *, int, int);	/* files, row, col */
    struct RB_TREE *no_check_tree, *known_iseg_tree;
    struct RB_TRAV trav;
    struct pixels *to_check, *newpixel, *current, *tree_pix;
    FLAG *check_flag;

    G_message("checking speed of RAM vs SEG vs get function performance");

    G_message("Access in the same region, so shouldn't have any disk I/O");

    max = 100000000;
    G_message("repeating everything %d times.", max);

    {				/* Array vs. SEG ... when working in local area */
	start = clock();
	for (i = 0; i < max; i++) {
	    segment_get(&files->bands_seg, (void *)files->bands_val, 12, 12);
	    temp = files->bands_val[0];
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("Using SEG: %g", cpu_time_used);

	start = clock();
	for (i = 0; i < max; i++) {
	    //~ temp = files->iseg[12][12];
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("Using array in RAM: %g", cpu_time_used);

	get = &get_segID_SEG;

	start = clock();
	for (i = 0; i < max; i++) {
	    temp = get(files, 12, 12);
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("Using SEG w/ get(): %g", cpu_time_used);

	get = &get_segID_RAM;

	start = clock();
	for (i = 0; i < max; i++) {
	    temp = get(files, 12, 12);
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
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
    {				/* compare rbtree with linked list and array */

	n = 100;
	start = clock();
	for (i = 0; i < max; i++) {
	    no_check_tree = rbtree_create(compare_ids, sizeof(struct pixels));

	    /*build */
	    for (j = 0; j < n; j++) {
		tree_pix = (struct pixels *)link_new(files->token);
		tree_pix->row = tree_pix->col = j;
		rbtree_insert(no_check_tree, &tree_pix);
	    }
	    /*access */
	    for (j = 0; j < n; j++) {
		if (rbtree_find(no_check_tree, &tree_pix))
		    continue;	/* always looking for the same pixel...is this an easy or hard one to find? */
	    }
	    /*free memory */
	    rbtree_destroy(no_check_tree);
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message
	    ("Using rbtree of pixels ( build/find/destroy), %d elements, time: %g",
	     n, cpu_time_used);

	start = clock();
	for (i = 0; i < max; i++) {
	    known_iseg_tree = rbtree_create(compare_ids, sizeof(int));

	    /*build */
	    for (j = 0; j < n; j++) {
		rbtree_insert(known_iseg_tree, &j);
	    }

	    /*access */
	    for (j = 0; j < n; j++) {
		if (rbtree_find(known_iseg_tree, &j))
		    continue;
	    }

	    /*free memory */
	    rbtree_destroy(known_iseg_tree);
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message
	    ("Using rbtree ints ( build/find/destroy), %d elements, time: %g",
	     n, cpu_time_used);


	to_check = NULL;

	start = clock();
	for (i = 0; i < max; i++) {
	    /*build */
	    for (j = 0; j < n; j++) {
		newpixel = (struct pixels *)link_new(files->token);
		newpixel->next = to_check;	/*point the new pixel to the current first pixel */
		newpixel->row = j;
		newpixel->col = i;
		to_check = newpixel;	/*change the first pixel to be the new pixel. */
	    }
	    /*access */
	    for (current = to_check; current != NULL; current = current->next) {	/* for each of Ri's neighbors */
		temp = current->row;
	    }
	    /*free memory */
	    my_dispose_list(files->token, &to_check);

	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message
	    ("Using linked list and linkm (build/access/free), %d elements, time: %g",
	     n, cpu_time_used);


	n = 1000;
	/* repeat for both with larger membership */

	start = clock();
	for (i = 0; i < max; i++) {
	    known_iseg_tree = rbtree_create(compare_ids, sizeof(int));

	    /*build */
	    for (j = 0; j < n; j++) {
		rbtree_insert(known_iseg_tree, &j);
	    }

	    /*access */
	    for (j = 0; j < n; j++) {
		if (rbtree_find(known_iseg_tree, &j))
		    continue;
	    }

	    /*free memory */
	    rbtree_destroy(known_iseg_tree);
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("Using rbtree ints, %d elements, time: %g", n,
		  cpu_time_used);

	to_check = NULL;

	start = clock();
	for (i = 0; i < max; i++) {
	    /*build */
	    for (j = 0; j < n; j++) {
		newpixel = (struct pixels *)link_new(files->token);
		newpixel->next = to_check;	/*point the new pixel to the current first pixel */
		newpixel->row = j;
		newpixel->col = i;
		to_check = newpixel;	/*change the first pixel to be the new pixel. */
	    }
	    /*access */
	    for (current = to_check; current != NULL; current = current->next) {	/* for each of Ri's neighbors */
		temp = current->row;
	    }
	    /*free memory */
	    my_dispose_list(files->token, &to_check);

	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("Using linked list and linkm, %d elements, time: %g", n,
		  cpu_time_used);

	k = 100;
	n = 50;
	check_flag = flag_create(k, k);
	start = clock();
	for (i = 0; i < max; i++) {
	    /*set to zero */
	    flag_clear_all(check_flag);
	    /*write and access */
	    for (j = 0; j < n; j++) {
		FLAG_SET(check_flag, j, j);
		temp = FLAG_GET(check_flag, j, j);
	    }
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message
	    ("Using %d pixel flag array (all cleared), %d elements set and get, time: %g",
	     k * k, n, cpu_time_used);


	k = 10000;
	check_flag = flag_create(k, k);
	start = clock();
	for (i = 0; i < max; i++) {
	    /*set to zero */
	    flag_clear_all(check_flag);
	    /*write and access */
	    for (j = 0; j < n; j++) {
		FLAG_SET(check_flag, j, j);
		temp = FLAG_GET(check_flag, j, j);
	    }
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message
	    ("Using %d pixel flag array (all cleared), %d elements set and get, time: %g",
	     k * k, n, cpu_time_used);

    }

    /* iff bounding constraints have been given, need to confirm neighbors are in the same area.
     * Faster to check if the bounds map is null, or if no bounds just set all the bounds flags to 1 and directly check the bounds flag? */
    {
	max = INT_MAX;
	j = 0;
	G_message("compare if statement to FLAG_GET, repeating %d times",
		  max);
	G_message("Flag = %d", FLAG_GET(files->candidate_flag, 1, 1));

	start = clock();
	for (i = 0; i < max; i++) {
	    if ((FLAG_GET(files->candidate_flag, 1, 1)) != 0) {
		j++;
	    }
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("FLAG_GET: %g, temp: %d", cpu_time_used, j);
	j = 0;
	start = clock();
	for (i = 0; i < max; i++) {
	    if (files->bounds_map != NULL) {
		j++;
	    }
	}
	end = clock();
	cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
	G_message("check for NULL: %g, temp: %d", cpu_time_used, j);	/* was faster by about 20% */
    }

    /* is accessing a variable different then a value? */
    max = INT_MAX;
    j = k = 0;
    G_message("compare variable to number, repeating %d times", max);

    start = clock();
    for (i = 0; i < max; i++) {
	if (i > 0) {
	    j++;
	}
    }
    end = clock();
    cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
    G_message("compare to zero: %g, temp: %d", cpu_time_used, j);
    j = 0;
    start = clock();
    for (i = 0; i < max; i++) {
	if (i > k) {
	    j++;
	}
    }
    end = clock();
    cpu_time_used = ((double)(end - start)) / CLOCKS_PER_SEC;
    G_message("compare to k: %g, temp: %d", cpu_time_used, j);	/* was faster by about 20% */


    return TRUE;
}

int get_segID_SEG(struct files *files, int row, int col)
{
    segment_get(&files->bands_seg, (void *)files->bands_val, row, col);
    return files->bands_val[0];	/* for accurate comparison, is converting double to int a time penalty? */
}

int get_segID_RAM(struct files *files, int row, int col)
{
    return 0;			//files->iseg[row][col];
}
#endif

int region_growing(struct files *files, struct functions *functions)
{
    int row, col, t;
    double threshold, Ri_similarity, Rk_similarity, tempsim;
    int endflag;		/* =TRUE if there were no merges on that processing iteration */
    int pathflag;		/* =TRUE if we didn't find mutual neighbors, and should continue with Rk */
    struct pixels *Ri_head, *Rk_head, *Rin_head, *Rkn_head, *Rclose_head,
	*Rc_head, *Rc_tail, *Rcn_head, *current, *newpixel, *Ri_bestn;
    int Ri_count, Rk_count, Rc_count;	/* number of pixels/cells in Ri and Rk */
    unsigned long int z, end_z;	// depending on shape of the rectangle...will need a larger max i.  long long is avail in C99 spec...  (only needed for z-order)
    int j;

#ifdef PROFILE
    //todo polish, remove or comment when done?
    clock_t start, end;
    clock_t merge_start, merge_end;
    double merge_accum, merge_lap;
    clock_t fn_start, fn_end;
    double fn_accum, fn_lap;
    clock_t pass_start, pass_end;

    merge_accum = fn_accum = 0;
    start = clock();
#endif
    /* files->token has the "link_head" for linkm: linked list memory allocation.
     * 
     * 4 linked lists of pixels:
     * Ri = current focus segment
     * Rk = Ri's most similar neighbor
     * Rkn = Rk's neighbors
     * Rin = Ri's neigbors
     * */
    if (files->bounds_map == NULL)
	G_message(_("Running region growing algorithm, the percent completed is based on %d max iterations, but the process will end earlier if no further merges can be made."),
		  functions->end_t);

    t = 1;

    /*set linked list head pointers to null. */
    Ri_head = NULL;
    Rk_head = NULL;
    Rin_head = NULL;
    Rkn_head = NULL;
    Ri_bestn = NULL;
    Rclose_head = NULL;
    Rc_head = NULL;
    Rcn_head = NULL;

    /* do while loop until no merges are made, or until t reaches maximum number of iterations */
    do {
#ifdef PROFILE
	pass_start = clock();
#endif
	fprintf(stdout, "pass %d\n", t);
	G_debug(3, "#######   Starting outer do loop! t = %d    #######", t);
	G_percent(t, functions->end_t, 1);

	threshold = functions->threshold;	/* TODO, consider making this a function of t. */

	endflag = TRUE;

	/* Set candidate flag to true/1 for all pixels */
	set_all_candidate_flags(files);

	/*process candidate pixels for this iteration */

	/*check each pixel, start the processing only if it is a candidate pixel */
#ifdef ROWMAJOR
	for (row = 0; row < files->nrows; row++) {
	    for (col = 0; col < files->ncols; col++) {
#else
	{
	    /* z-order traversal: */
	    /* need to get a "square" power of 2 around our processing area */

	    /*largest dimension: */
	    if (files->nrows > files->ncols)
		end_z = files->nrows;
	    else
		end_z = files->ncols;

	    /* largest power of 2: */
	    end_z--;		/* in case we are already a power of two. */
	    end_z = (end_z >> 1) | end_z;
	    end_z = (end_z >> 2) | end_z;
	    end_z = (end_z >> 4) | end_z;
	    end_z = (end_z >> 8) | end_z;
	    end_z = (end_z >> 16) | end_z;
	    end_z = (end_z >> 32) | end_z;	/* only for 64-bit architecture TODO, would this mess things up on 32? */
	    /*todo does this need to repeat more since it is long unsigned??? */
	    end_z++;

	    /*squared: */
	    end_z *= end_z;

	    for (z = 0; z < end_z; z++) {
		row = col = 0;
		/*bit wise construct row and col from i */
		for (j = 8 * sizeof(long int) - 1; j > 1; j--) {
		    row = row | (1 & (z >> j));
		    row = row << 1;
		    j--;
		    col = col | (1 & (z >> j));
		    col = col << 1;
		}
		row = row | (1 & (z >> j));
		j--;
		col = col | (1 & (z >> j));
		if (row >= files->nrows || col >= files->ncols)
		    continue;	/* todo polish, if z-order is helpful, could skip to the next z that is in the processing area. */
	    }
#endif
	    G_debug(4, "Starting pixel from next row/col, not from Rk");

	    if (FLAG_GET(files->candidate_flag, row, col) &&
		FLAG_GET(files->seeds_flag, row, col)) {
		/*free memory for linked lists */
		my_dispose_list(files->token, &Ri_head);
		my_dispose_list(files->token, &Rk_head);
		my_dispose_list(files->token, &Rin_head);
		my_dispose_list(files->token, &Rkn_head);
		my_dispose_list(files->token, &Rclose_head);
		Rk_count = 0;

		/* First pixel in Ri is current row/col pixel.  We may add more later if it is part of a segment */
		Ri_count = 1;
		newpixel = (struct pixels *)link_new(files->token);
		newpixel->next = NULL;
		newpixel->row = row;
		newpixel->col = col;
		Ri_head = newpixel;

		pathflag = TRUE;

		while (pathflag == TRUE) {	/*if don't find mutual neighbors on first try, will use Rk as next Ri. */
		    G_debug(4, "Next starting pixel: row, %d, col, %d",
			    Ri_head->row, Ri_head->col);

		    pathflag = FALSE;

		    /* find segment neighbors, if we don't already have them */
		    if (Rin_head == NULL) {
#ifdef PROFILE
			fn_start = clock();
#endif
			if (find_segment_neighbors
			    (&Ri_head, &Rin_head, &Ri_count, files,
			     functions) != TRUE) {
			    G_fatal_error("find_segment_neighbors() failed");
			}
#ifdef PROFILE
			fn_end = clock();
			fn_lap =
			    ((double)(fn_end - fn_start)) / CLOCKS_PER_SEC;
			fn_accum += fn_lap;
			fprintf(stdout, "fsn(Ri): %g\t", fn_lap);
#endif
		    }

		    if (Rin_head != NULL) {	/*found neighbors, find best neighbor then see if is mutually best neighbor */

#ifdef DEBUG
			/*print out segment membership */
			G_debug(4, "2b, Found Ri's pixels");
			for (current = Ri_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Ri: row: %d, col: %d",
				    current->row, current->col);
			/*print out neighbors */
			G_debug(4, "2b, Found Ri's neighbors");
			for (current = Rin_head; current != NULL;
			     current = current->next)
			    G_debug(4, "Rin: row: %d, col: %d",
				    current->row, current->col);
#endif

			/* ********  find Ri's most similar neighbor  ******** */
			Ri_bestn = NULL;
			Ri_similarity = threshold + 1;	/* set current similarity to max value */
			segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row, Ri_head->col);	/* current segment values */

			/* for each of Ri's neighbors */
			for (current = Rin_head; current != NULL;
			     current = current->next) {
			    tempsim = (*functions->calculate_similarity)
				(Ri_head, current, files, functions);
			    G_debug(4,
				    "simularity = %g for neighbor : row: %d, col %d.",
				    tempsim, current->row, current->col);

			    /* if very close, will merge, but continue checking other neighbors */
			    //~ if (tempsim < functions->very_close * threshold){
			    //~ /* add to Rclose list */
			    //~ newpixel = (struct pixels *)link_new(files->token);
			    //~ newpixel->next = Rclose_head;
			    //~ newpixel->row = current->row;
			    //~ newpixel->col = current->col;
			    //~ Rclose_head = newpixel;
			    //~ }
			    /* If "sort of" close, merge only if it is the mutually most similar */
			    //~ else 
			    if (tempsim < Ri_similarity) {
				Ri_similarity = tempsim;
				Ri_bestn = current;
				G_debug(4,
					"Current lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
					Ri_similarity, Ri_bestn->row,
					Ri_bestn->col);
			    }
			}	/* finished similiarity check for all neighbors */

			/* *** merge all the "very close" pixels/segments *** */
			/* doing this after checking all Rin, so we don't change the bands_val between similarity comparisons
			 * TODO... but that leaves the possibility that we have the wrong best Neighbor after doing these merges... 
			 * but it seems we can't put this merge after the Rk/Rkn portion of the loop, because we are changing the available neighbors
			 * ...maybe this extra "very close" idea has to be done completely differently or dropped???  */
			for (current = Rclose_head; current != NULL;
			     current = current->next) {
			    my_dispose_list(files->token, &Rc_head);
			    my_dispose_list(files->token, &Rcn_head);

			    /* get membership of neighbor segment */
			    Rc_count = 1;
			    newpixel =
				(struct pixels *)link_new(files->token);
			    newpixel->next = NULL;
			    newpixel->row = current->row;
			    newpixel->col = current->col;
			    Rc_head = Rc_tail = newpixel;
			    find_segment_neighbors(&Rc_head, &Rcn_head, &Rc_count, files, functions);	/* just to get members, not looking at neighbors now */
			    merge_values(Ri_head, Rc_head, Ri_count,
					 Rc_count, files);

			    /* Add Rc pixels to Ri */
			    Rc_tail->next = Ri_head;
			    Ri_head = Rc_head;

			    //todo, recurse?  Check all Rcn neighbors if they are very close?
			    // not needed if the combining works...   my_dispose_list(files->token, &Rc_head);
			    Rc_head = NULL;
			    my_dispose_list(files->token, &Rcn_head);
			}
			my_dispose_list(files->token, &Rclose_head);

			/* check if we have a bestn that is valid to use to look at Rk */
			if (Ri_bestn != NULL) {
			    G_debug(4,
				    "Lowest Ri_similarity = %g, for neighbor pixel row: %d col: %d",
				    Ri_similarity, Ri_bestn->row,
				    Ri_bestn->col);

			    //todo this "limited" flag will probably be removed?  Then this entire if section could be removed if we always allow multiple merges per pass?
			    if ((functions->limited == TRUE) && !
				(FLAG_GET
				 (files->candidate_flag,
				  Ri_bestn->row, Ri_bestn->col))) {
				/* this check is important:
				 * best neighbor is not a valid candidate, was already merged earlier in this time step */
				Ri_bestn = NULL;
			    }
			}
			if (Ri_bestn != NULL && Ri_similarity < threshold) {	/* small TODO: should this be < or <= for threshold? */
			    /* Rk starts from Ri's best neighbor */
			    if (Rk_head) {
				G_warning("Rk_head is not NULL!");
				my_dispose_list(files->token, &Rk_head);
			    }
			    if (Rkn_head) {
				G_warning("Rkn_head is not NULL!");
				my_dispose_list(files->token, &Rkn_head);
			    }
			    Rk_count = 1;
			    newpixel =
				(struct pixels *)link_new(files->token);
			    newpixel->next = NULL;
			    newpixel->row = Ri_bestn->row;
			    newpixel->col = Ri_bestn->col;
			    Rk_head = newpixel;

			    find_segment_neighbors(&Rk_head, &Rkn_head,
						   &Rk_count, files,
						   functions);

#ifdef DEBUG
			    /*print out neighbors */
			    G_debug(4, "Found Rk's pixels");
			    for (current = Rk_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rk: row: %d, col: %d",
					current->row, current->col);
			    /*print out neighbors */
			    G_debug(4, "Found Rk's neighbors");
			    for (current = Rkn_head; current != NULL;
				 current = current->next)
				G_debug(4, "Rkn: row: %d, col: %d",
					current->row, current->col);
#endif

			    /* ********  find Rk's most similar neighbor  ******** */
			    Rk_similarity = Ri_similarity;	/*Ri gets first priority - ties won't change anything, so we'll accept Ri and Rk as mutually best neighbors */
			    segment_get(&files->bands_seg, (void *)files->bands_val, Rk_head->row, Rk_head->col);	/* current segment values */

			    /* check similarity for each of Rk's neighbors */
			    for (current = Rkn_head; current != NULL;
				 current = current->next) {
				tempsim =
				    functions->calculate_similarity
				    (Rk_head, current, files, functions);

				if (tempsim < Rk_similarity) {
				    Rk_similarity = tempsim;
				    break;	/* exit for Rk's neighbors loop here, we know that Ri and Rk aren't mutually best neighbors */
				}
			    }	/* have checked all of Rk's neighbors */

			    if (Rk_similarity == Ri_similarity) {	/* mutually most similar neighbors */

#ifdef PROFILE
				merge_start = clock();
#endif
				merge_values(Ri_head, Rk_head, Ri_count,
					     Rk_count, files);
#ifdef PROFILE
				merge_end = clock();
				merge_lap =
				    ((double)(merge_end - merge_start)) /
				    CLOCKS_PER_SEC;
				merge_accum += merge_lap;
				fprintf(stdout, "merge time: %g\n",
					merge_lap);
#endif
				endflag = FALSE;	/* we've made at least one merge, so want another t iteration */
			    }
			    else {	/* they weren't mutually best neighbors */
				G_debug(4,
					"Ri was not Rk's best neighbor, Ri_sim: %g, Rk_sim, %g",
					Ri_similarity, Rk_similarity);

				/* checked Ri once, didn't find a mutually best neighbor, so remove all members of Ri from candidate pixels for this iteration */
				set_candidate_flag(Ri_head, FALSE, files);

				if (FLAG_GET
				    (files->candidate_flag, Rk_head->row,
				     Rk_head->col) &&
				    FLAG_GET(files->seeds_flag, Rk_head->row,
					     Rk_head->col))
				    pathflag = TRUE;
			    }
			}	/* end if (Ri_bestn != NULL && Ri_similarity < threshold) */
			else {
			    /* no valid best neighbor for this Ri
			     * exclude this Ri from further comparisons 
			     * because we checked already Ri for a mutually best neighbor with all valid candidates
			     * thus Ri can not be the mutually best neighbor later on during this pass
			     * unfortunately this does happen sometimes */
			    set_candidate_flag(Ri_head, FALSE, files);
			    G_debug(4,
				    "3b Ri's best neighbor was not valid candidate, or their similarity was > threshold");
			}

		    }		/* end if(Rin_head != NULL) */
		    else {	/* Ri didn't have a neighbor */
			G_debug(4, "Segment had no neighbors");
			set_candidate_flag(Ri_head, FALSE, files);
		    }

		    if (pathflag) {	/*initialize Ri, Rin, Rk, Rin using Rk as Ri. */
			/* So for the next iteration, lets start with Rk as the focus segment */
			/* Seems this should be a bit faster, since we already have segment membership pixels */
			/* TODO: this shortened each iteration time by about 10% but increased the number of iterations by 20% ?!?!?!? */
			if (functions->path == TRUE) {
			    Ri_count = Rk_count;
			    Rk_count = 0;
			    my_dispose_list(files->token, &Ri_head);
			    Ri_head = Rk_head;
			    Rk_head = NULL;
			    if (Rkn_head != NULL) {
				my_dispose_list(files->token, &Rin_head);
				Rin_head = Rkn_head;
				Rkn_head = NULL;
			    }
			    else
				my_dispose_list(files->token, &Rin_head);
			}
			else
			    pathflag = FALSE;

		    }

		}		/*end pathflag do loop */
	    }			/*end if pixel is candidate and seed pixel */
	}			/*next column (or next z) */
#ifdef ROWMAJOR
    }				/*next row */
#endif
#ifdef PROFILE
    pass_end = clock();
    fprintf(stdout, "pass %d took: %g\n", t,
	    ((double)(pass_end - pass_start)) / CLOCKS_PER_SEC);
#endif


    /* finished one iteration over entire raster */
    G_debug(4, "Finished one pass, t was = %d", t);
    t++;
    }
    while (t <= functions->end_t && endflag == FALSE) ;	/*end t loop, either reached max iterations or didn't merge any segments */

    if (t == 2 && files->bounds_map == NULL)
	G_warning(_("No segments were created. Verify threshold and region settings."));
    /* included the bound_map check, since we check all values between min/max, intermediate values might not be present.  TODO polish, add back in if we check for unique bounds values. */

    if (endflag == FALSE)
	G_message(_("Merging processes stopped due to reaching max iteration limit, more merges may be possible"));


    /* ****************************************************************************************** */
    /* final pass, ignore threshold and force a merge for small segments with their best neighbor */
    /* ****************************************************************************************** */


    if (functions->min_segment_size > 1 && t > 2) {	/* NOTE: added t > 2, it doesn't make sense to force merges if no merges were made on the original pass.  Something should be adjusted first */
	G_message
	    (_("Final iteration, forcing merges for small segments, percent complete based on rows."));

	/* for the final forced merge, the candidate flag is just to keep track if we have confirmed if:
	 *              a. the segment size is >= to the minimum allowed size  or
	 *              b. we have merged it with its best neighbor
	 */

	set_all_candidate_flags(files);

	for (row = 0; row < files->nrows; row++) {
	    G_percent(row, files->nrows - 1, 5);
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

		    /* find segment neighbors */
		    if (find_segment_neighbors
			(&Ri_head, &Rin_head, &Ri_count, files,
			 functions) != TRUE) {
			G_fatal_error("find_segment_neighbors() failed");
		    }

		    if (Rin_head != NULL) {	/*found neighbors */
			if (Ri_count >= functions->min_segment_size)	/* don't force a merge */
			    set_candidate_flag(Ri_head, FALSE, files);

			else {	/* Merge with most similar neighbor */

			    /* find Ri's most similar neighbor */
			    Ri_bestn = NULL;
			    Ri_similarity = DBL_MAX;	/* set current similarity to max value */
			    segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row, Ri_head->col);	/* current segment values */

			    /* for each of Ri's neighbors */
			    for (current = Rin_head; current != NULL;
				 current = current->next) {
				tempsim = (*functions->calculate_similarity)
				    (Ri_head, current, files, functions);
				G_debug(4,
					"simularity = %g for neighbor : row: %d, col %d.",
					tempsim, current->row, current->col);

				if (tempsim < Ri_similarity) {
				    Ri_similarity = tempsim;
				    Ri_bestn = current;
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

				/* we'll have the neighbor pixel to start with. */
				Rk_count = 1;
				newpixel =
				    (struct pixels *)link_new(files->token);
				newpixel->next = NULL;
				newpixel->row = Ri_bestn->row;
				newpixel->col = Ri_bestn->col;
				Rk_head = newpixel;

				/* get the full pixel/cell membership list for Rk *//* todo polish: worth having a seperate function for this, since we don't need the neighbors? */
				find_segment_neighbors(&Rk_head, &Rkn_head,
						       &Rk_count, files,
						       functions);

				merge_values(Ri_head, Rk_head, Ri_count,
					     Rk_count, files);

				/* merge_values sets Ri and Rk candidate flag to FALSE.  Put Rk back to TRUE if the size is too small. */
				if (Ri_count + Rk_count <
				    functions->min_segment_size)
				    set_candidate_flag(Rk_head, TRUE, files);
			    }	/* end if best neighbor != null */
			    else
				G_warning
				    ("No best neighbor found in final merge for small segment, this shouldn't happen!");


			}	/* end else - pixel count was below minimum allowed */
		    }		/* end if neighbors found */
		    else {	/* no neighbors were found */
			G_warning
			    ("no neighbors found, this means only one segment was created.");
			set_candidate_flag(Ri_head, FALSE, files);
		    }
		}		/* end if pixel is candidate pixel */
	    }			/* next column */
	}			/* next row */
	t++;			/* to count one more "iteration" */
    }				/* end if for force merge */
    else
     if (t > 2)
	G_verbose_message("temporary(?) message, number of passes: %d",
			  t - 1);
#ifdef PROFILE
    end = clock();
    fprintf(stdout, "time spent merging: %g\n", merge_accum);
    fprintf(stdout, "time spent finding neighbors: %g\n", fn_accum);
    fprintf(stdout, "total time: %g\n",
	    ((double)(end - start) / CLOCKS_PER_SEC));
#endif
    return TRUE;
    }

    int find_segment_neighbors(struct pixels **R_head,
			       struct pixels **neighbors_head, int *seg_count,
			       struct files *files,
			       struct functions *functions)
    {
	int n, current_seg_ID, R_iseg = -1;
	struct pixels *newpixel, *current, *to_check, tree_pix;	/* need to check the pixel neighbors of to_check */
	int pixel_neighbors[8][2];
	struct RB_TREE *no_check_tree;	/* pixels that should no longer be checked on this current find_neighbors() run */
	struct RB_TREE *known_iseg;

#ifdef DEBUG
	struct RB_TRAV trav;
#endif

	/* TODO, any time savings to move any variables to files (mem allocation in open_files) */

	/* neighbor list will be a listing of pixels that are neighbors?  Include segment numbers?  Only include unique segments?
	 * MM: counting unique neighbor segments could have the advantage of dealing with special
	 * segments that have only one neighbor, i.e. segments within segments
	 * 

	 * Maybe the most complete return would be a structure array, structure to include the segment ID and a list of points in it?  
	 * But the list of points would NOT be inclusive - just the points bordering the current segment...
	 */

	/* parameter: R, current segment membership, could be single pixel (incomplete list) or list of pixels.
	 * parameter: neighbors/Rin/Rik, neighbor pixels, could have a list already, or could be empty ?
	 * functions->num_pn  int, 4 or 8, for number of pixel neighbors 
	 * */


	/* *** initialize data *** */

	segment_get(&files->iseg_seg, &R_iseg, (*R_head)->row,
		    (*R_head)->col);

	if (R_iseg == 0) {	/* if seeds were provided, this is just a single non-seed pixel, only return neighbors that are segments or seeds */

	    functions->find_pixel_neighbors((*R_head)->row, (*R_head)->col,
					    pixel_neighbors, files);
	    for (n = 0; n < functions->num_pn; n++) {

		/* skip pixel if out of computational area or null */
		if (pixel_neighbors[n][0] < files->minrow ||
		    pixel_neighbors[n][0] >= files->maxrow ||
		    pixel_neighbors[n][1] < files->mincol ||
		    pixel_neighbors[n][1] >= files->maxcol ||
		    FLAG_GET(files->null_flag, pixel_neighbors[n][0],
			     pixel_neighbors[n][1])
		    )
		    continue;

		segment_get(&files->iseg_seg, &current_seg_ID,
			    pixel_neighbors[n][0], pixel_neighbors[n][1]);

		if (current_seg_ID > 0) {
		    newpixel = (struct pixels *)link_new(files->token);
		    newpixel->next = *neighbors_head;	/*point the new pixel to the current first pixel */
		    newpixel->row = pixel_neighbors[n][0];
		    newpixel->col = pixel_neighbors[n][1];
		    *neighbors_head = newpixel;	/*change the first pixel to be the new pixel. */
		    /* todo polish... could use a tree and only return pixels from unique segments. */
		}
	    }

	}
	else {			/*normal processing, look for all adjacent pixels or segments */
	    no_check_tree =
		rbtree_create(compare_pixels, sizeof(struct pixels));
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
		if (rbtree_insert(no_check_tree, &tree_pix) == 0)	/* don't check it again */
		    G_warning("could not insert data!?");
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
		for (current = to_check; current != NULL;
		     current = current->next)
		    G_debug(5, "to_check... row: %d, col: %d", current->row,
			    current->col);
		for (current = *neighbors_head; current != NULL;
		     current = current->next)
		    G_debug(5, "Rn... row: %d, col: %d", current->row,
			    current->col);
#endif

		/*now check the pixel neighbors and add to the lists */

		/*print what pixel neighbors were found: */
		/*      for (n = 0; n < functions->num_pn; n++){
		   G_debug(5, "\tpixel_neighbors[n][0]: %d, pixel_neighbors[n][1]: %d",  pixel_neighbors[n][0], pixel_neighbors[n][1]);
		   } */

		/* for each pixel neighbors, check if they should be processed, check segment ID, and add to appropriate lists */
		for (n = 0; n < functions->num_pn; n++) {

		    /* skip pixel if out of computational area or null */
		    if (pixel_neighbors[n][0] < files->minrow ||
			pixel_neighbors[n][0] >= files->maxrow ||
			pixel_neighbors[n][1] < files->mincol ||
			pixel_neighbors[n][1] >= files->maxcol ||
			FLAG_GET(files->null_flag, pixel_neighbors[n][0],
				 pixel_neighbors[n][1])
			)
			continue;

		    tree_pix.row = pixel_neighbors[n][0];
		    tree_pix.col = pixel_neighbors[n][1];
		    G_debug(5,
			    "********* rbtree_find(no_check_tree, &tree_pix) = %p",
			    rbtree_find(no_check_tree, &tree_pix));

		    if (rbtree_find(no_check_tree, &tree_pix) == FALSE) {	/* want to check this neighbor */
			segment_get(&files->iseg_seg, &current_seg_ID,
				    pixel_neighbors[n][0],
				    pixel_neighbors[n][1]);

			rbtree_insert(no_check_tree, &tree_pix);	/* don't check it again */

			//~ G_debug(5, "\tfiles->iseg[][] = %d Ri_seg_ID = %d",
			//~ files->iseg[pixel_neighbors[n][0]]
			//~ [pixel_neighbors[n]
			//~ [1]], Ri_seg_ID);

			if (current_seg_ID == R_iseg) {	/* pixel is member of current segment, add to R */
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
			    if (!rbtree_find(known_iseg, &current_seg_ID)) {	/* we don't have any neighbors yet from this segment */
				if (current_seg_ID != 0)
				    /* with seeds, non seed pixels are defaulted to zero.  Should we use null instead?? then could skip this check?  Or we couldn't insert it??? */
				    /* add to known neighbors list */
				    rbtree_insert(known_iseg, &current_seg_ID);	/* todo: could I just try to insert it, if it fails I know it is already there?
										 * I guess it would depend on how much faster the find() is, and what fraction of the 
										 * neighbors are in a duplicate segment... */

				/* put pixel_neighbor[n] in Rin */
				G_debug(5, "Put in neighbors_head");
				newpixel =
				    (struct pixels *)link_new(files->token);
				newpixel->next = *neighbors_head;	/*point the new pixel to the current first pixel */
				newpixel->row = pixel_neighbors[n][0];
				newpixel->col = pixel_neighbors[n][1];
				*neighbors_head = newpixel;	/*change the first pixel to be the new pixel. */
			    }
			}


		    }		/*end if for pixel_neighbor was in "don't check" list */
		}		/* end for loop - next pixel neighbor */

#ifdef DEBUG
		G_debug(5,
			"remaining pixel's in to_check, after processing the last pixel's neighbors:");
		for (current = to_check; current != NULL;
		     current = current->next)
		    G_debug(5, "to_check... row: %d, col: %d", current->row,
			    current->col);

		G_debug(5, "\t### end of pixel neighors");
#endif
	    }			/* end while to_check has more elements */

	    /* clean up */
	    rbtree_destroy(no_check_tree);
	    rbtree_destroy(known_iseg);
	}
	return TRUE;
    }

    int find_four_pixel_neighbors(int p_row, int p_col,
				  int pixel_neighbors[8][2],
				  struct files *files)
    {
	/* Note: this will return neighbors outside of the raster boundary.
	 * Check in the calling routine if the pixel should be processed.
	 */

	/* north */
	pixel_neighbors[0][1] = p_col;
	pixel_neighbors[0][0] = p_row - 1;

	/* east */
	pixel_neighbors[1][0] = p_row;
	pixel_neighbors[1][1] = p_col + 1;

	/* south */
	pixel_neighbors[2][1] = p_col;
	pixel_neighbors[2][0] = p_row + 1;

	/* west */
	pixel_neighbors[3][0] = p_row;
	pixel_neighbors[3][1] = p_col - 1;

	return TRUE;
    }

    int find_eight_pixel_neighbors(int p_row, int p_col,
				   int pixel_neighbors[8][2],
				   struct files *files)
    {
	/* get the 4 orthogonal neighbors: */
	find_four_pixel_neighbors(p_row, p_col, pixel_neighbors, files);

	/* and then the diagonals: */

	/* north west */
	pixel_neighbors[4][0] = p_row - 1;
	pixel_neighbors[4][1] = p_col - 1;

	/* north east */
	pixel_neighbors[5][0] = p_row - 1;
	pixel_neighbors[5][1] = p_col + 1;

	/* south east */
	pixel_neighbors[6][0] = p_row + 1;
	pixel_neighbors[6][1] = p_col + 1;

	/* south west */
	pixel_neighbors[7][0] = p_row + 1;
	pixel_neighbors[7][1] = p_col - 1;

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

	/* val = sqrt(val); *//* use squared distance, save the calculation time. */

	return val;

    }

    /* similarity / distance between two points based on their input raster values */
    /* assumes first point values already saved in files->bands_seg - only run segment_get once for that value... */
    /* TODO: segment_get already happened for a[] values in the main function.  Could remove a[] from these parameters */
    double calculate_manhattan_similarity(struct pixels *a, struct pixels *b,
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
	    val += fabs(files->bands_val[n] - files->second_val[n]);	/* todo check if fabs is the "fast" way for absolute value */
	}

	/* val = sqrt(val); *//* use squared distance, save the calculation time. */

	return val;

    }

    /*
       In the eCognition literature, we find that the key factor in the
       multi-scale segmentation algorithm used by Definiens is the scale
       factor f:

       f = W.Hcolor + (1 - W).Hshape
       Hcolor = sum(b = 1:nbands)(Wb.SigmaB)
       Hshape = Ws.Hcompact + (1 - Ws).Hsmooth
       Hcompact = PL/sqrt(Npx)
       Hsmooth = PL/Pbbox

       Where W is a user-defined weight of importance of object radiometry vs
       shape (usually .9 vs .1), Wb is the weigh given to band B, SigmaB is
       the std dev of the object for band b, Ws is a user-defined weight
       giving the importance of compactedness vs smoothness, PL is the
       perimeter lenght of the object, Npx the number of pixels within the
       object, and Pbbox the perimeter of the bounding box of the object.
     */

    int merge_values(struct pixels *Ri_head, struct pixels *Rk_head,
		     int Ri_count, int Rk_count, struct files *files)
    {
	int n, Ri_iseg, Rk_iseg;
	struct pixels *current;

	/*get input values *//*TODO polish, confirm if we can assume we already have bands_val for Ri, so don't need to segment_get() again?  note...current very_close implementation requires getting this value again... */
	segment_get(&files->bands_seg, (void *)files->bands_val, Ri_head->row,
		    Ri_head->col);
	segment_get(&files->bands_seg, (void *)files->second_val,
		    Rk_head->row, Rk_head->col);

	segment_get(&files->iseg_seg, &Rk_iseg, Rk_head->row, Rk_head->col);
	segment_get(&files->iseg_seg, &Ri_iseg, Ri_head->row, Ri_head->col);
	/* todo polish, maybe we have some of these values already?  Or they should be stored in files structure? */

	for (n = 0; n < files->nbands; n++) {
	    files->bands_val[n] =
		(files->bands_val[n] * Ri_count +
		 files->second_val[n] * Rk_count) / (Ri_count + Rk_count);
	}

	/* update segment number and candidate flag ==0 */

	//~ G_debug(4, "\t\tMerging, segment number: %d, including pixels:",
	//~ files->iseg[Ri_head->row][Ri_head->col]);

	fprintf(stdout,
		"merging Ri (pixel count): %d (%d) with Rk (count): %d (%d).\n",
		Ri_iseg, Ri_count, Rk_iseg, Rk_count);

	/* for each member of Ri and Rk, write new average bands values and segment values */
	for (current = Ri_head; current != NULL; current = current->next) {
	    segment_put(&files->bands_seg, (void *)files->bands_val,
			current->row, current->col);
	    FLAG_UNSET(files->candidate_flag, current->row, current->col);	/*candidate pixel flag, only one merge allowed per t iteration */
	    G_debug(4, "\t\tRi row: %d, col: %d", current->row, current->col);
	}
	for (current = Rk_head; current != NULL; current = current->next) {
	    segment_put(&files->bands_seg, (void *)files->bands_val,
			current->row, current->col);
	    segment_put(&files->iseg_seg, &Ri_iseg, current->row,
			current->col);
	    FLAG_UNSET(files->candidate_flag, current->row, current->col);
	    G_debug(4, "\t\tRk row: %d, col: %d", current->row, current->col);

	}

	/* merged two segments, decrement count if Rk was an actual segment (not a non-seed pixel) */
	if (Rk_iseg > 0)
	    files->nsegs--;

	return TRUE;
    }

    /* calculates and stores the mean value for all pixels in a list, assuming they are all in the same segment */
    int merge_pixels(struct pixels *R_head, struct files *files)
    {
	int n, count = 0;
	struct pixels *current;

	/* Note: using files->bands_val for current pixel values, and files->second_val for the accumulated value */

	/* initialize second_val */
	for (n = 0; n < files->nbands; n++) {
	    files->second_val[n] = 0;
	}

	if (R_head->next != NULL) {
	    /* total up bands values for all pixels */
	    for (current = R_head; current != NULL; current = current->next) {
		segment_get(&files->bands_seg, (void *)files->bands_val,
			    current->row, current->col);
		for (n = 0; n < files->nbands; n++) {
		    files->second_val[n] += files->bands_val[n];
		}
		count++;
	    }

	    /* calculate the mean */
	    for (n = 0; n < files->nbands; n++) {
		files->second_val[n] = files->second_val[n] / count;
	    }

	    /* save the results */
	    for (current = R_head; current != NULL; current = current->next) {
		segment_put(&files->bands_seg, (void *)files->second_val,
			    current->row, current->col);
	    }

	}

	return TRUE;
    }

    /* besides setting flag, also increments how many pixels remain to be processed */
    int set_candidate_flag(struct pixels *head, int value,
			   struct files *files)
    {
	/* head is linked list of pixels, value is new value of flag */
	struct pixels *current;

	for (current = head; current != NULL; current = current->next) {


	    if (value == FALSE) {
		FLAG_UNSET(files->candidate_flag, current->row, current->col);
	    }
	    else if (value == TRUE) {
		FLAG_SET(files->candidate_flag, current->row, current->col);
	    }
	    else
		G_fatal_error
		    ("programming bug, helper function called with invalid argument");
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

    /* functions used by binary tree to compare items */

    /* TODO "static" was used in break_polygons.c  extern was suggested in docs.  */

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
	struct pixels *a = (struct pixels *)first, *b =
	    (struct pixels *)second;

	if (a->row < b->row)
	    return -1;
	else if (a->row > b->row)
	    return 1;
	else {
	    /* same row */
	    if (a->col < b->col)
		return -1;
	    else if (a->col > b->col)
		return 1;
	}
	/* same row and col */
	return 0;
    }

    /* Set candidate flag to true/1 or false/0 for all pixels in current processing area
     * checks for NULL flag and if it is in current "polygon" if a bounds map is given 
     * checks if seeds were given */
    int set_all_candidate_flags(struct files *files)
    {
	int row, col;

	for (row = files->minrow; row < files->maxrow; row++) {
	    for (col = files->mincol; col < files->maxcol; col++) {
		if (!(FLAG_GET(files->null_flag, row, col))) {
		    FLAG_SET(files->candidate_flag, row, col);
		}
		else
		    FLAG_UNSET(files->candidate_flag, row, col);
	    }
	}
	return TRUE;
    }


    /* TODO polish: helper functions:
     * 
     * starting a list
     * 
     * */

#ifdef NODEF
    G_message("2b, Found Ri's pixels");
    /*print out neighbors */
    for (current = Ri_head; current != NULL; current = current->next)
	G_message("Ri: row: %d, col: %d", current->row, current->col);
    G_message("2b, Found Ri's neighbors");
    /*print out neighbors */
    for (current = Rin_head; current != NULL; current = current->next)
	G_message("Rin: row: %d, col: %d", current->row, current->col);
    G_message("Found Rk's pixels");
    /*print out neighbors */
    for (current = Rk_head; current != NULL; current = current->next)
	G_message("Rk: row: %d, col: %d", current->row, current->col);
    G_message("Found Rk's neighbors");
    /*print out neighbors */
    for (current = Rkn_head; current != NULL; current = current->next)
	G_message("Rkn: row: %d, col: %d", current->row, current->col);
#endif
