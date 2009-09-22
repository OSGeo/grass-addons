#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

/*
 * compare function for search tree
 * returns 1 if a > b
 * returns -1 if a < b
 * returns 0 if a == b
 */
int draindir_compare(const void *itema, const void *itemb)
{
    struct ddir *a = (struct ddir *)itema;
    struct ddir *b = (struct ddir *)itemb;

    if (a->pos > b->pos)
	return 1;
    else if (a->pos < b->pos)
	return -1;

    return 0;
}

double mfd_pow(double base)
{
    int x;
    double result;

    result = base;
    if (c_fac == 1)
	return result;

    for (x = 2; x <= c_fac; x++) {
	result *= base;
    }
    return result;
}

int continue_stream(CELL is_swale, int r, int c, int r_max, int c_max,
		    unsigned int thisindex, int *stream_no)
{
    char aspect;
    int curr_stream;
    int r_nbr, c_nbr, ct_dir;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    int stream_node_step = 1000;
    struct ddir draindir, *founddir;

    G_debug(3, "continue stream");

    /* set drainage direction */
    aspect = drain[r - r_max + 1][c - c_max + 1];

    /* add to search tree */
    draindir.pos = thisindex;
    draindir.dir = aspect;
    rbtree_insert(draintree, &draindir);

    curr_stream = stream[INDEX(r_max, c_max)];
    if (curr_stream < 0)
	curr_stream = 0;
    /* confluence */
    if (curr_stream <= 0) {
	/* no confluence, just continue */
	G_debug(2, "no confluence, just continue stream");
	stream[INDEX(r_max, c_max)] = is_swale;
    }
    else {
	G_debug(2, "confluence");
	/* new confluence */
	if (stream_node[curr_stream].r != r_max ||
	    stream_node[curr_stream].c != c_max) {
	    G_debug(2, "new confluence");
	    /* set new stream id */
	    curr_stream = stream[INDEX(r_max, c_max)] = ++(*stream_no);
	    /* add stream node */
	    if (*stream_no >= n_alloc_nodes - 1) {
		n_alloc_nodes += stream_node_step;
		stream_node =
		    (struct snode *)G_realloc(stream_node,
					      n_alloc_nodes *
					      sizeof(struct snode));
	    }
	    stream_node[*stream_no].r = r_max;
	    stream_node[*stream_no].c = c_max;
	    stream_node[*stream_no].id = *stream_no;
	    stream_node[*stream_no].n_trib = 0;
	    stream_node[*stream_no].n_trib_total = 0;
	    stream_node[*stream_no].n_alloc = 0;
	    stream_node[*stream_no].trib = NULL;
	    stream_node[*stream_no].acc = NULL;
	    n_stream_nodes++;

	    /* debug */
	    if (n_stream_nodes != *stream_no)
		G_warning(_("stream_no %d and n_stream_nodes %d out of sync"),
			  *stream_no, n_stream_nodes);

	    /* add all tributaries */
	    G_debug(2, "add all tributaries");
	    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		/* get r_nbr, c_nbr for neighbours */
		r_nbr = r_max + nextdr[ct_dir];
		c_nbr = c_max + nextdc[ct_dir];
		/* check that neighbour is within region */
		if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 &&
		    c_nbr < ncols) {
		    draindir.pos = INDEX(r_nbr, c_nbr);
		    if ((founddir =
			 rbtree_find(draintree, &draindir)) != NULL) {
			if (r_nbr + asp_r[(int)founddir->dir] == r_max &&
			    c_nbr + asp_c[(int)founddir->dir] == c_max) {

			    /* add tributary to stream node */
			    if (stream_node[curr_stream].n_trib >=
				stream_node[curr_stream].n_alloc) {
				size_t new_size;

				stream_node[curr_stream].n_alloc += 2;
				new_size =
				    stream_node[curr_stream].n_alloc *
				    sizeof(int);
				stream_node[curr_stream].trib =
				    (int *)G_realloc(stream_node[curr_stream].
						     trib, new_size);
				new_size =
				    stream_node[curr_stream].n_alloc *
				    sizeof(double);
				stream_node[curr_stream].acc =
				    (double *)
				    G_realloc(stream_node[curr_stream].acc,
					      new_size);
			    }

			    stream_node[curr_stream].
				trib[stream_node[curr_stream].n_trib] =
				stream[draindir.pos];
			    stream_node[curr_stream].
				acc[stream_node[curr_stream].n_trib++] =
				acc[draindir.pos];
			}
		    }
		}
	    }

	    /* update stream IDs downstream */
	    G_debug(2, "update stream IDs downstream");
	    r_nbr = r_max;
	    c_nbr = c_max;
	    draindir.pos = INDEX(r_nbr, c_nbr);

	    while ((founddir = rbtree_find(draintree, &draindir)) != NULL) {
		if (asp_r[(int)founddir->dir] == 0 &&
		    asp_c[(int)founddir->dir] == 0)
		    G_fatal_error("no valid stream direction");
		r_nbr = r_nbr + asp_r[(int)founddir->dir];
		c_nbr = c_nbr + asp_c[(int)founddir->dir];
		draindir.pos = INDEX(r_nbr, c_nbr);
		if (stream[INDEX(r_nbr, c_nbr)] <= 0)
		    G_fatal_error("stream id not set");
		else
		    stream[INDEX(r_nbr, c_nbr)] = curr_stream;
	    }
	}
	else {
	    /* stream node already existing here */
	    G_debug(2, "existing confluence");
	    /* add new tributary to stream node */
	    if (stream_node[curr_stream].n_trib >=
		stream_node[curr_stream].n_alloc) {
		size_t new_size;

		stream_node[curr_stream].n_alloc += 2;
		new_size = stream_node[curr_stream].n_alloc * sizeof(int);
		stream_node[curr_stream].trib =
		    (int *)G_realloc(stream_node[curr_stream].trib, new_size);
		new_size = stream_node[curr_stream].n_alloc * sizeof(double);
		stream_node[curr_stream].acc =
		    (double *)G_realloc(stream_node[curr_stream].acc,
					new_size);
	    }

	    stream_node[curr_stream].trib[stream_node[curr_stream].n_trib++] =
		stream[thisindex];
	}
	/* end new confluence */

	G_debug(2, "%d tribs", stream_node[curr_stream].n_trib);
	if (stream_node[curr_stream].n_trib == 1)
	    G_warning("stream node %d only 1 trib: %d", curr_stream,
		      stream_node[curr_stream].trib[0]);
    }

    return 1;
}

/*
 * extracts streams for threshold
 */
int do_accum(double d8cut)
{
    int r, c, dr, dc;
    CELL ele_val, ele_nbr;
    DCELL value, valued;
    int count;
    struct Cell_head window;
    int mfd_cells, astar_not_set, is_null;
    double *dist_to_nbr, *weight, sum_weight, max_weight;
    double dx, dy;
    int r_nbr, c_nbr, r_max, c_max, ct_dir, np_side;
    int is_worked;
    char aspect;
    double max_acc, prop;
    int edge;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    unsigned int thisindex, nindex, workedon, killer;

    G_message(_("calculate flow accumulation..."));

    count = 0;

    /* distances to neighbours */
    dist_to_nbr = (double *)G_malloc(sides * sizeof(double));
    weight = (double *)G_malloc(sides * sizeof(double));

    G_get_set_window(&window);

    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	/* get r, c (r_nbr, c_nbr) for neighbours */
	r_nbr = nextdr[ct_dir];
	c_nbr = nextdc[ct_dir];
	/* account for rare cases when ns_res != ew_res */
	dy = abs(r_nbr) * window.ns_res;
	dx = abs(c_nbr) * window.ew_res;
	if (ct_dir < 4)
	    dist_to_nbr[ct_dir] = dx + dy;
	else
	    dist_to_nbr[ct_dir] = sqrt(dx * dx + dy * dy);
    }

    /* reset worked flag */
    flag_clear_all(worked);

    for (killer = 1; killer <= n_points; killer++) {
	G_percent(killer, n_points, 1);

	r = astar_pts[killer].r;
	c = astar_pts[killer].c;
	aspect = astar_pts[killer].asp;

	thisindex = INDEX(r, c);

	/* do not distribute flow along edges */
	if (aspect < 0) {
	    G_debug(3, "edge");
	    continue;
	}

	if (aspect) {
	    dr = r + asp_r[abs((int)aspect)];
	    dc = c + asp_c[abs((int)aspect)];
	}
	else {
	    dr = r;
	    dc = c;
	}

	r_max = dr;
	c_max = dc;

	value = acc[thisindex];

	/***************************************/
	/*  get weights for flow distribution  */

	/***************************************/

	max_weight = 0;
	sum_weight = 0;
	np_side = -1;
	mfd_cells = 0;
	astar_not_set = 1;
	ele_val = ele[thisindex];
	is_null = 0;
	edge = 0;
	/* this loop is needed to get the sum of weights */
	for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	    /* get r_nbr, c_nbr for neighbours */
	    r_nbr = r + nextdr[ct_dir];
	    c_nbr = c + nextdc[ct_dir];
	    weight[ct_dir] = -1;
	    /* check that neighbour is within region */
	    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

		nindex = INDEX(r_nbr, c_nbr);

		is_worked = FLAG_GET(worked, r_nbr, c_nbr);
		if (is_worked == 0) {
		    ele_nbr = ele[nindex];
		    is_null = G_is_c_null_value(&ele_nbr);
		    edge = is_null;
		    if (!is_null && ele_nbr <= ele_val) {
			if (ele_nbr < ele_val) {
			    weight[ct_dir] =
				mfd_pow((ele_val -
					 ele_nbr) / dist_to_nbr[ct_dir]);
			}
			if (ele_nbr == ele_val) {
			    weight[ct_dir] =
				mfd_pow(0.5 / dist_to_nbr[ct_dir]);
			}
			sum_weight += weight[ct_dir];
			mfd_cells++;

			if (weight[ct_dir] > max_weight) {
			    max_weight = weight[ct_dir];
			}

			if (dr == r_nbr && dc == c_nbr) {
			    astar_not_set = 0;
			}
		    }
		}
		if (dr == r_nbr && dc == c_nbr)
		    np_side = ct_dir;
	    }
	    else
		edge = 1;
	    if (edge)
		break;
	}

	/* do not distribute flow along edges, this causes artifacts */
	if (edge) {
	    G_debug(3, "edge");
	    continue;
	}

	/* honour A * path 
	 * mfd_cells == 0: fine, SFD along A * path
	 * mfd_cells == 1 && astar_not_set == 0: fine, SFD along A * path
	 * mfd_cells > 0 && astar_not_set == 1: A * path not included, add to mfd_cells
	 */

	/************************************/
	/*  distribute and accumulate flow  */

	/************************************/

	/* MFD, A * path not included, add to mfd_cells */
	if (mfd_cells > 0 && astar_not_set == 1) {
	    mfd_cells++;
	    sum_weight += max_weight;
	    weight[np_side] = max_weight;
	}

	/* use SFD (D8) if d8cut threshold exceeded */
	if (fabs(value) > d8cut)
	    mfd_cells = 0;

	max_acc = -1;

	if (mfd_cells > 1) {
	    prop = 0.0;
	    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		/* get r, c (r_nbr, c_nbr) for neighbours */
		r_nbr = r + nextdr[ct_dir];
		c_nbr = c + nextdc[ct_dir];

		/* check that neighbour is within region */
		if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 &&
		    c_nbr < ncols && weight[ct_dir] > -0.5) {
		    is_worked = FLAG_GET(worked, r_nbr, c_nbr);
		    if (is_worked == 0) {

			weight[ct_dir] = weight[ct_dir] / sum_weight;
			/* check everything sums up to 1.0 */
			prop += weight[ct_dir];

			nindex = INDEX(r_nbr, c_nbr);

			valued = acc[nindex];
			valued += value * weight[ct_dir];
			acc[nindex] = valued;
		    }
		    else if (ct_dir == np_side) {
			/* check for consistency with A * path */
			workedon++;
		    }
		}
	    }
	    if (fabs(prop - 1.0) > 5E-6f) {
		G_warning(_("MFD: cumulative proportion of flow distribution not 1.0 but %f"),
			  prop);
	    }
	}
	/* get out of depression in SFD mode */
	else {
	    nindex = INDEX(dr, dc);
	    valued = acc[INDEX(dr, dc)];
	    valued += value;
	    acc[INDEX(dr, dc)] = valued;
	}

	FLAG_SET(worked, r, c);
    }

    G_free(dist_to_nbr);
    G_free(weight);

    return 1;
}

/*
 * extracts streams for threshold, accumulation is provided
 */
int extract_streams(double threshold, double mont_exp, int use_weight)
{
    int r, c, dr, dc;
    CELL is_swale, ele_val, ele_nbr;
    DCELL value, valued;
    struct Cell_head window;
    int mfd_cells, stream_cells, swale_cells, astar_not_set, is_null;
    double *dist_to_nbr;
    double dx, dy;
    int r_nbr, c_nbr, r_max, c_max, ct_dir, np_side, max_side;
    int is_worked;
    char aspect;
    double max_acc;
    int edge, flat;
    int asp_r[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int asp_c[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    /* sides */
    /*
     *  | 7 | 1 | 4 |
     *  | 2 |   | 3 |
     *  | 5 | 0 | 6 |
     */
    unsigned int thisindex, nindex, workedon, killer;
    int stream_no = 0, stream_node_step = 1000;
    double slope, diag;

    G_message(_("extract streams..."));

    /* init BST for drainage direction */
    draintree = rbtree_create(draindir_compare, sizeof(struct ddir));

    /* init stream nodes */
    n_alloc_nodes = stream_node_step;
    stream_node =
	(struct snode *)G_malloc(n_alloc_nodes * sizeof(struct snode));
    n_stream_nodes = 0;

    /* init outlet nodes */
    n_alloc_outlets = stream_node_step;
    outlets =
	(struct point *)G_malloc(n_alloc_outlets * sizeof(struct point));
    n_outlets = 0;

    /* distances to neighbours */
    dist_to_nbr = (double *)G_malloc(sides * sizeof(double));

    G_get_set_window(&window);

    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	/* get r, c (r_nbr, c_nbr) for neighbours */
	r_nbr = nextdr[ct_dir];
	c_nbr = nextdc[ct_dir];
	/* account for rare cases when ns_res != ew_res */
	dy = abs(r_nbr) * window.ns_res;
	dx = abs(c_nbr) * window.ew_res;
	if (ct_dir < 4)
	    dist_to_nbr[ct_dir] = dx + dy;
	else
	    dist_to_nbr[ct_dir] = sqrt(dx * dx + dy * dy);
    }

    diag = sqrt(2);

    /* reset worked flag */
    flag_clear_all(worked);

    workedon = 0;

    for (killer = 1; killer <= n_points; killer++) {
	G_percent(killer, n_points, 1);

	r = astar_pts[killer].r;
	c = astar_pts[killer].c;
	aspect = astar_pts[killer].asp;

	thisindex = INDEX(r, c);

	/* do not distribute flow along edges */
	if (aspect < 0) {
	    G_debug(3, "edge");
	    is_swale = stream[thisindex];
	    if (is_swale) {
		G_debug(2, "edge outlet");
		/* add outlet point */
		if (n_outlets >= n_alloc_outlets) {
		    n_alloc_outlets += stream_node_step;
		    outlets =
			(struct point *)G_realloc(outlets,
						  n_alloc_outlets *
						  sizeof(struct point));
		}
		outlets[n_outlets].r = r;
		outlets[n_outlets].c = c;
		n_outlets++;
	    }
	    continue;
	}

	if (aspect) {
	    dr = r + asp_r[abs((int)aspect)];
	    dc = c + asp_c[abs((int)aspect)];
	}
	else {
	    dr = r;
	    dc = c;
	}

	r_max = dr;
	c_max = dc;

	value = acc[thisindex];

	/************************************/
	/*  find main drainage direction  */

	/************************************/

	max_acc = -1;
	max_side = np_side = -1;
	mfd_cells = 0;
	stream_cells = 0;
	swale_cells = 0;
	astar_not_set = 1;
	ele_val = ele[thisindex];
	is_null = 0;
	edge = 0;
	flat = 1;
	/* this loop is needed to get the sum of weights */
	for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	    /* get r_nbr, c_nbr for neighbours */
	    r_nbr = r + nextdr[ct_dir];
	    c_nbr = c + nextdc[ct_dir];
	    /* check that neighbour is within region */
	    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

		if (dr == r_nbr && dc == c_nbr)
		    np_side = ct_dir;

		nindex = INDEX(r_nbr, c_nbr);

		/* check for swale cells */
		is_swale = stream[nindex];
		if (is_swale > 0)
		    swale_cells++;
		/* check for stream cells */
		valued = fabs(acc[nindex]);
		if (valued >= threshold)
		    stream_cells++;

		is_worked = FLAG_GET(worked, r_nbr, c_nbr);
		if (is_worked == 0) {
		    ele_nbr = ele[nindex];
		    if (ele_nbr != ele_val)
			flat = 0;
		    edge = G_is_c_null_value(&ele_nbr);
		    if (!edge && ele_nbr <= ele_val) {

			mfd_cells++;

			/* set main drainage direction */
			if (valued >= max_acc) {
			    max_acc = valued;
			    r_max = r_nbr;
			    c_max = c_nbr;
			    max_side = ct_dir;
			}

			if (dr == r_nbr && dc == c_nbr) {
			    astar_not_set = 0;
			}
		    }
		}
		else if (ct_dir == np_side) {
		    /* check for consistency with A * path */
		    workedon++;
		}
	    }
	    else
		edge = 1;
	    if (edge)
		break;
	}

	is_swale = stream[thisindex];

	/* do not distribute flow along edges, this causes artifacts */
	if (edge) {
	    G_debug(3, "edge");
	    if (is_swale) {
		G_debug(2, "edge outlet");
		/* add outlet point */
		if (n_outlets >= n_alloc_outlets) {
		    n_alloc_outlets += stream_node_step;
		    outlets =
			(struct point *)G_realloc(outlets,
						  n_alloc_outlets *
						  sizeof(struct point));
		}
		outlets[n_outlets].r = r;
		outlets[n_outlets].c = c;
		n_outlets++;
	    }
	    continue;
	}

	/* honour A * path 
	 * mfd_cells == 0: fine, SFD along A * path
	 * mfd_cells == 1 && astar_not_set == 0: fine, SFD along A * path
	 * mfd_cells > 0 && astar_not_set == 1: A * path not included, add to mfd_cells
	 */

	/* MFD, A * path not included, add to mfd_cells */
	if (mfd_cells > 0 && astar_not_set == 1) {
	    mfd_cells++;
	    /* get main drainage direction */
	    nindex = INDEX(dr, dc);
	    if (fabs(acc[nindex]) >= max_acc) {
		max_acc = fabs(acc[nindex]);
		r_max = dr;
		c_max = dc;
		max_side = np_side;
	    }
	}
	else if (mfd_cells == 0) {
	    flat = 0;
	    max_side = np_side;
	}

	is_swale = stream[thisindex];

	/**********************/
	/*  start new stream  */

	/**********************/

	/* weight map has precedence over Montgomery */
	if (use_weight) {
	    value *= accweight[thisindex];
	}
	/* Montgomery's stream initiation acc * (tan(slope))^mont_exp */
	/* uses whatever unit is accumulation */
	if (mont_exp > 0) {
	    if (r_max == r && c_max == c)
		G_warning
		    ("Can't use Montgomery's method, no stream direction found");
	    else {

		ele_nbr = ele[INDEX(r_max, c_max)];

		slope = (double)(ele_val - ele_nbr) / ele_scale;

		if (max_side > 3)
		    slope /= diag;

		value *= pow(fabs(slope), mont_exp);

	    }
	}

	if (is_swale < 1 && flat == 0 && fabs(value) >= threshold &&
	    stream_cells < 4 && swale_cells < 1) {
	    G_debug(2, "start new stream");
	    is_swale = stream[thisindex] = ++stream_no;
	    /* add stream node */
	    if (stream_no >= n_alloc_nodes - 1) {
		n_alloc_nodes += stream_node_step;
		stream_node =
		    (struct snode *)G_realloc(stream_node,
					      n_alloc_nodes *
					      sizeof(struct snode));
	    }
	    stream_node[stream_no].r = r;
	    stream_node[stream_no].c = c;
	    stream_node[stream_no].id = stream_no;
	    stream_node[stream_no].n_trib = 0;
	    stream_node[stream_no].n_trib_total = 0;
	    stream_node[stream_no].n_alloc = 0;
	    stream_node[stream_no].trib = NULL;
	    stream_node[stream_no].acc = NULL;
	    n_stream_nodes++;

	    /* debug */
	    if (n_stream_nodes != stream_no)
		G_warning(_("stream_no %d and n_stream_nodes %d out of sync"),
			  stream_no, n_stream_nodes);
	}

	/*********************/
	/*  continue stream  */

	/*********************/

	/* can't continue stream, add outlet point */
	if (is_swale > 0 && r_max == r && c_max == c) {
	    G_debug(2, "can't continue stream at %d %d", r, c);

	    if (n_outlets >= n_alloc_outlets) {
		n_alloc_outlets += stream_node_step;
		outlets =
		    (struct point *)G_malloc(n_alloc_outlets *
					     sizeof(struct point));
	    }
	    outlets[n_outlets].r = r;
	    outlets[n_outlets].c = c;
	    n_outlets++;
	}
	else if (is_swale > 0) {
	    continue_stream(is_swale, r, c, r_max, c_max, thisindex,
			    &stream_no);
	}

	FLAG_SET(worked, r, c);
    }
    if (workedon)
	G_warning(_("MFD: A * path already processed when distributing flow: %d of %d cells"),
		  workedon, n_points);

    flag_destroy(worked);

    G_free(dist_to_nbr);

    G_debug(1, "%d outlets", n_outlets);
    G_debug(1, "%d nodes", n_stream_nodes);
    G_debug(1, "%d streams", stream_no);

    return 1;
}
