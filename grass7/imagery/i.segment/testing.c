/* This file includes some functions that are called as "segmentation methods" when DEBUG is defined.  They were used to test the I/O without doing any segmentation,
 * but then later were modified to test the use and speed of various data structures. */

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
