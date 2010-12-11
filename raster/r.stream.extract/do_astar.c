#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

unsigned int get_parent(unsigned int c)
{
    return (unsigned int)((c) - 2) / 3 + 1;
}

unsigned int get_child(unsigned int p)
{
    return (unsigned int)(p) * 3 - 1;
}

unsigned int heap_drop(void);

double get_slope2(CELL, CELL, double);

int do_astar(void)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    unsigned int astp;
    int count, is_in_list, is_worked;
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    CELL ele_val, ele_up, ele_nbr[8];
    unsigned int thisindex, nindex;
    /* sides
     * |7|1|4|
     * |2| |3|
     * |5|0|6|
     */
    int nbr_ew[8] = { 0, 1, 2, 3, 1, 0, 0, 1 };
    int nbr_ns[8] = { 0, 1, 2, 3, 3, 2, 3, 2 };
    double dx, dy, dist_to_nbr[8], ew_res, ns_res;
    double slope[8];
    struct Cell_head window;
    int skip_me;

    count = 0;

    first_cum = n_points;

    G_message(_("A* Search..."));

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
    ew_res = window.ew_res;
    ns_res = window.ns_res;

    while (heap_size > 0) {
	G_percent(count++, n_points, 1);
	if (count > n_points)
	    G_fatal_error(_("BUG in A* Search: %d surplus points"), heap_size);

	if (heap_size > n_points)
	    G_fatal_error
		(_("BUG in A* Search: too many points in heap %d, should be %d"),
		 heap_size, n_points);

	astp = astar_pts[1];

	heap_drop();

	/* set flow accumulation order */
	astar_pts[first_cum] = astp;
	first_cum--;

	thisindex = astp;
	r = thisindex / ncols;
	c = thisindex - r * ncols;

	ele_val = ele[thisindex];

	for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	    /* get r, c (r_nbr, c_nbr) for neighbours */
	    r_nbr = r + nextdr[ct_dir];
	    c_nbr = c + nextdc[ct_dir];
	    slope[ct_dir] = ele_nbr[ct_dir] = 0;
	    skip_me = 0;
	    /* check that neighbour is within region */
	    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

		is_in_list = FLAG_GET(in_list, r_nbr, c_nbr);
		is_worked = FLAG_GET(worked, r_nbr, c_nbr);
		nindex = INDEX(r_nbr, c_nbr);
		if (!is_worked) {
		    ele_nbr[ct_dir] = ele[nindex];
		    slope[ct_dir] =
			get_slope2(ele_val, ele_nbr[ct_dir],
				   dist_to_nbr[ct_dir]);
		}
		/* avoid diagonal flow direction bias */
		if (!is_in_list) {
		    if (ct_dir > 3 && slope[ct_dir] > 0) {
			if (slope[nbr_ew[ct_dir]] > 0) {
			    /* slope to ew nbr > slope to center */
			    if (slope[ct_dir] <
				get_slope2(ele_nbr[nbr_ew[ct_dir]],
					   ele_nbr[ct_dir], ew_res))
				skip_me = 1;
			}
			if (!skip_me && slope[nbr_ns[ct_dir]] > 0) {
			    /* slope to ns nbr > slope to center */
			    if (slope[ct_dir] <
				get_slope2(ele_nbr[nbr_ns[ct_dir]],
					   ele_nbr[ct_dir], ns_res))
				skip_me = 1;
			}
		    }
		}

		if (is_in_list == 0 && skip_me == 0) {
		    ele_up = ele[nindex];
		    asp[nindex] = drain[r_nbr - r + 1][c_nbr - c + 1];
		    heap_add(r_nbr, c_nbr, ele_up, asp[nindex]);
		}
		else if (is_in_list && is_worked == 0) {
		    /* neighbour is edge in list, not yet worked */
		    if (asp[nindex] < 0) {
			asp[nindex] = drain[r_nbr - r + 1][c_nbr - c + 1];
		    }
		    /* neighbour is inside real depression, not yet worked */
		    if (asp[nindex] == 0 && ele_val <= ele[nindex]) {
			asp[nindex] = drain[r_nbr - r + 1][c_nbr - c + 1];
		    }
		}
	    }
	}    /* end neighbours */
	FLAG_SET(worked, r, c);
    }    /* end A* search */

    G_percent(n_points, n_points, 1);	/* finish it */

    flag_destroy(in_list);
    G_free(astar_added);

    return 1;
}

/*
 * compare function for heap
 * returns 1 if point1 < point2 else 0
 */
int heap_cmp(CELL ele1, unsigned int index1, CELL ele2, unsigned int index2)
{
    if (ele1 < ele2)
	return 1;
    else if (ele1 == ele2) {
	if (index1 < index2)
	    return 1;
    }

    return 0;
}

int sift_up(unsigned int start, CELL elec)
{
    unsigned int child, child_added, parent;
    CELL elep;
    unsigned int childp;

    child = start;
    child_added = astar_added[child];
    childp = astar_pts[child];

    while (child > 1) {
	parent = get_parent(child);

	elep = ele[astar_pts[parent]];

	/* child < parent */
	if (heap_cmp(elec, child_added, elep, astar_added[parent]) == 1) {
	    /* push parent point down */
	    astar_added[child] = astar_added[parent];
	    astar_pts[child] = astar_pts[parent];
	    child = parent;
	}
	else
	    /* no more sifting up, found new slot for child */
	    break;
    }

    /* set heap_index for child */
    if (child < start) {
	astar_added[child] = child_added;
	astar_pts[child] = childp;
	return 1;
    }

    return 0;
}

/*
 * add item to heap
 * returns heap_size
 */
unsigned int heap_add(int r, int c, CELL ele, char asp)
{
    FLAG_SET(in_list, r, c);

    /* add point to next free position */

    heap_size++;

    astar_added[heap_size] = nxt_avail_pt;
    astar_pts[heap_size] = INDEX(r, c);

    nxt_avail_pt++;

    /* sift up: move new point towards top of heap */
    sift_up(heap_size, ele);

    return heap_size;
}

/*
 * drop item from heap
 * returns heap size
 */
unsigned int heap_drop(void)
{
    unsigned int child, childr, parent;
    int i;
    CELL elec, eler;

    if (heap_size == 1) {
	astar_added[1] = -1;
	heap_size = 0;
	return heap_size;
    }

    parent = 1;
    while ((child = get_child(parent)) <= heap_size) {

	elec = ele[astar_pts[child]];

	if (child < heap_size) {
	    childr = child + 1;
	    i = child + 3;
	    while (childr <= heap_size && childr < i) {
		eler = ele[astar_pts[childr]];

		if (heap_cmp
		    (eler, astar_added[childr], elec,
		     astar_added[child]) == 1) {
		    child = childr;
		    elec = eler;
		}
		childr++;
	    }
	}

	/* move hole down */
	astar_added[parent] = astar_added[child];
	astar_pts[parent] = astar_pts[child];
	parent = child;
    }

    /* hole is in lowest layer, move to heap end */
    if (parent < heap_size) {
	astar_added[parent] = astar_added[heap_size];
	astar_pts[parent] = astar_pts[heap_size];

	elec = ele[astar_pts[parent]];
	/* sift up last swapped point, only necessary if hole moved to heap end */
	sift_up(parent, elec);
    }

    /* the actual drop */
    heap_size--;

    return heap_size;
}

double get_slope2(CELL ele, CELL up_ele, double dist)
{
    if (ele >= up_ele)
	return 0.0;
    else
	return (double)(up_ele - ele) / dist;
}
