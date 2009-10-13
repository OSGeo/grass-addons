#include <stdlib.h>
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

int do_astar(void)
{
    int r, c, r_nbr, c_nbr, ct_dir;
    struct ast_point astp;
    int count, is_in_list;
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    CELL ele_val, ele_up;
    char asp_val;
    unsigned int thisindex, nindex;

    count = 0;

    first_cum = n_points;

    G_message(_("A* Search..."));

    while (heap_size > 0) {
	G_percent(count++, n_points, 1);
	if (count > n_points)
	    G_fatal_error("broken A* Search, %d surplus points", heap_size);

	if (heap_size > n_points)
	    G_fatal_error
		("broken A* Search, too many points in heap %d, should be %d",
		 heap_size, n_points);

	astp = astar_pts[1];

	heap_drop();

	/* set flow accumulation order */
	astar_pts[first_cum] = astp;
	first_cum--;

	thisindex = astp.idx;
	r = thisindex / ncols;
	c = thisindex - r * ncols;

	ele_val = ele[thisindex];

	for (ct_dir = 0; ct_dir < sides; ct_dir++) {
	    /* get r, c (r_nbr, c_nbr) for neighbours */
	    r_nbr = r + nextdr[ct_dir];
	    c_nbr = c + nextdc[ct_dir];
	    /* check that neighbour is within region */
	    if (r_nbr >= 0 && r_nbr < nrows && c_nbr >= 0 && c_nbr < ncols) {

		is_in_list = FLAG_GET(in_list, r_nbr, c_nbr);

		if (is_in_list == 0) {
		    nindex = INDEX(r_nbr, c_nbr);
		    ele_up = ele[nindex];
		    asp_val = drain[r_nbr - r + 1][c_nbr - c + 1];
		    heap_add(r_nbr, c_nbr, ele_up, asp_val);
		    FLAG_SET(in_list, r_nbr, c_nbr);
		}
	    }
	}			/* end neighbours */
	FLAG_SET(worked, r, c);
    }				/* end A* search */

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
    struct ast_point childp;

    child = start;
    child_added = astar_added[child];
    childp = astar_pts[child];

    while (child > 1) {
	parent = get_parent(child);

	elep = ele[astar_pts[parent].idx];

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

    if (heap_size > n_points)
	G_fatal_error(_("heapsize too large"));

    astar_added[heap_size] = nxt_avail_pt;
    astar_pts[heap_size].idx = INDEX(r, c);
    astar_pts[heap_size].asp = asp;

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

	elec = ele[astar_pts[child].idx];

	if (child < heap_size) {
	    childr = child + 1;
	    i = child + 3;
	    while (childr <= heap_size && childr < i) {
		eler = ele[astar_pts[childr].idx];

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

	elec = ele[astar_pts[parent].idx];
	/* sift up last swapped point, only necessary if hole moved to heap end */
	sift_up(parent, elec);
    }

    /* the actual drop */
    heap_size--;

    return heap_size;
}
