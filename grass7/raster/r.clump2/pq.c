
/****************************************************************************
 *
 * MODULE:       r.clump2
 *
 * AUTHOR(S):    Markus Metz
 *
 * PURPOSE:      Recategorizes data in a raster map layer by grouping cells
 *		 that form physically discrete areas into unique categories.
 *
 * COPYRIGHT:    (C) 2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#include <stdlib.h>
#include <grass/glocale.h>
#include "local_proto.h"

#define GET_PARENT(c) (int) (((c) - 2) / 3 + 1)
#define GET_CHILD(p) (int) (((p) * 3) - 1)

static int heap_alloced = 0;
static int heap_step;
static long *heap_index;

int cmp_clump(long cid1, long cid2)
{
    if (!cid1)
	return 0;
    if (!cid2)
	return 1;
    return (cid1 < cid2);
}

int init_pq(int step)
{
    pqsize = 0;
    if (step < 100)
	step = 100;

    heap_alloced = heap_step = step;
    heap_index = (long *)G_malloc(heap_alloced * sizeof(long));

    return 0;
}

int free_pq(void)
{
    if (heap_alloced)
	G_free(heap_index);

    return 0;
}

long sift_up(long start, long child_pnt)
{
    register long parent, child;

    child = start;

    while (child > 1) {
	parent = GET_PARENT(child);

	/* child is larger */
	if (cmp_clump(clump_id[child_pnt], clump_id[heap_index[parent]])) {
	    /* push parent point down */
	    heap_index[child] = heap_index[parent];
	    child = parent;
	}
	else
	    /* no more sifting up, found new slot for child */
	    break;
    }

    /* put point in new slot */
    if (child < start) {
	heap_index[child] = child_pnt;
    }

    return child;
}

int add_pnt(long index)
{
    pqsize++;
    if (pqsize >= heap_alloced) {
	heap_alloced += heap_step;
	heap_index =
	    (long *)G_realloc((void *)heap_index,
			      heap_alloced * sizeof(long));
    }

    heap_index[pqsize] = index;
    sift_up(pqsize, index);

    return 0;
}

long drop_pnt(void)
{
    register long parent, child, childr, i;
    long next_index;

    if (pqsize == 0)
	return -1;

    next_index = heap_index[1];

    if (pqsize == 1) {
	pqsize--;

	heap_index[1] = -1;

	return next_index;
    }

    /* start with root */
    parent = 1;

    /* sift down: move hole back towards bottom of heap */

    while ((child = GET_CHILD(parent)) <= pqsize) {
	if (child < pqsize) {
	    childr = child + 1;
	    i = child + 3;
	    /* get largest child */
	    while (childr < i && childr <= pqsize) {
		if (cmp_clump(clump_id[heap_index[childr]], 
		    clump_id[heap_index[child]])) {
		    child = childr;
		}
		childr++;
	    }
	}

	/* move hole down */
	heap_index[parent] = heap_index[child];
	parent = child;
    }

    /* hole is in lowest layer, move to heap end */
    if (parent < pqsize) {
	heap_index[parent] = heap_index[pqsize];

	/* sift up last swapped point, only necessary if hole moved to heap end */
	sift_up(parent, heap_index[parent]);
    }

    /* the actual drop */
    pqsize--;

    return next_index;
}
