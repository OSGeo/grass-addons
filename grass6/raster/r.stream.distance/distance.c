#include <grass/glocale.h>
#include "global.h"

int calculate_upstream(void)
{
    int r, c;
    int next_r, next_c;
    float easting, northing;
    float cell_easting, cell_northing;
    int i, j, k;
    int done;
    int n_inits = 0;
    float cur_dist;
    POINT *d_inits;
    float *tmp_elevation = NULL;	/* only for elevation */
    float tmp_dist = 0;
    float target_elev = 0;
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {

	    for (i = 1; i < 9; ++i) {
		if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		    c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		    continue;	/* out of border */

		j = (i + 4) > 8 ? i - 4 : i + 4;

		if (dirs[r + nextr[i]][c + nextc[i]] == j && distance[r][c] != 0) {	/* is contributing cell */
		    distance[r][c] = -1;
		    break;
		}
	    }
	    if (distance[r][c] == 1 && dirs[r][c] > 0)
		n_inits++;
	    else if (dirs[r][c] > 0)
		distance[r][c] = -1;
	}
    }

    d_inits = (POINT *) G_malloc(n_inits * sizeof(POINT));

    if (out_elev) {
	tmp_elevation = (float *)G_malloc(nrows * ncols * sizeof(float));
	for (r = 0; r < nrows; ++r) {
	    for (c = 0; c < ncols; ++c) {
		tmp_elevation[r * ncols + c] = elevation[r][c];
	    }
	}
    }

    k = 0;
    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {

	    if (distance[r][c] == 1) {
		distance[r][c] = 0;
		if (out_elev)
		    elevation[r][c] = 0;

		next_r = r + nextr[dirs[r][c]];
		next_c = c + nextc[dirs[r][c]];

		if (dirs[next_r][next_c] < 0)
		    continue;
		if (distance[next_r][next_c] == 0)
		    continue;

		d_inits[k].r = r;
		d_inits[k].c = c;
		d_inits[k].cur_dist = 0;

		if (out_elev)
		    d_inits[k].target_elev = tmp_elevation[r * ncols + c];

		k++;
	    }
	}
    }
    n_inits = k;

    while (n_inits > 0) {
	k = 0;

	for (i = 0; i < n_inits; ++i) {
	    r = d_inits[i].r;
	    c = d_inits[i].c;
	    next_r = r + nextr[dirs[r][c]];
	    next_c = c + nextc[dirs[r][c]];
	    tmp_dist = d_inits[i].cur_dist;

	    if (out_elev)
		target_elev = d_inits[i].target_elev;

	    easting = window.west + (c + 0.5) * window.ew_res;
	    northing = window.north - (r + 0.5) * window.ns_res;
	    cell_easting = window.west + (next_c + 0.5) * window.ew_res;
	    cell_northing = window.north - (next_r + 0.5) * window.ns_res;

	    cur_dist =
		tmp_dist + G_distance(easting, northing, cell_easting,
				      cell_northing);

	    if (near)
		done = (distance[next_r][next_c] > cur_dist ||
			distance[next_r][next_c] == -1) ? 1 : 0;
	    else
		done = (distance[next_r][next_c] < cur_dist ||
			distance[next_r][next_c] == -1) ? 1 : 0;

	    if (done) {
		distance[next_r][next_c] = cur_dist;
		if (out_elev)
		    elevation[next_r][next_c] =
			target_elev - tmp_elevation[next_r * ncols + next_c];

		if (dirs[r + nextr[dirs[r][c]]][c + nextc[dirs[r][c]]] < 1)
		    continue;

		d_inits[k].r = next_r;
		d_inits[k].c = next_c;
		d_inits[k].cur_dist = cur_dist;

		if (out_elev)
		    d_inits[k].target_elev = target_elev;

		k++;
	    }			/* end of if done */
	}
	n_inits = k;
    }
    return 0;
}


/*
   algorithm uses fifo queue for determining basins area. 
   it can works in stream mode (calculate distance to and elevation above streams)
   and outlet mode (calculate distance to and elevation above outlets)
 */
int fill_maps(OUTLET outlet)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int r, c,  i, j;
    POINT n_cell;
    float cur_dist = 0;
    float tmp_dist = 0;
    float target_elev;		/* eleavation at stream or outlet */
    float easting, northing;
    float cell_easting, cell_northing;

    tail = 0;
    head = -1;
    r = outlet.r;
    c = outlet.c;

    if (out_elev) {
	target_elev = elevation[r][c];
	elevation[r][c] = 0.;
    }

    while (tail != head) {
	easting = window.west + (c + .5) * window.ew_res;
	northing = window.north - (r + .5) * window.ns_res;

	for (i = 1; i < 9; ++i) {

	    if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		continue;	/* border */
	    j = (i + 4) > 8 ? i - 4 : i + 4;
	    if (dirs[r + nextr[i]][c + nextc[i]] == j) {	/* countributing cell */
		/* restet distance and elevation on streams and outlets: */
		if (outs) {	/* outlet mode */
		    if (distance[r + nextr[i]][c + nextc[i]] == 0) {
			continue;	/* continue for loop, point simply is not added to the queue! */
		    }
		    else {
			cell_northing =
			    window.north - (r + nextr[i] +
					    .5) * window.ns_res;
			cell_easting =
			    window.west + (c + nextc[i] + .5) * window.ew_res;
			cur_dist =
			    tmp_dist + G_distance(easting, northing,
						  cell_easting,
						  cell_northing);
			distance[r + nextr[i]][c + nextc[i]] = cur_dist;
		    }
		}
		else {		/* stream mode */
		    if (distance[r + nextr[i]][c + nextc[i]] == 0) {
			cur_dist = 0;
			if (out_elev)
			    target_elev =
				elevation[r + nextr[i]][c + nextc[i]];
		    }
		    else {
			cell_northing =
			    window.north - (r + nextr[i] +
					    .5) * window.ns_res;
			cell_easting =
			    window.west + (c + nextc[i] + .5) * window.ew_res;
			cur_dist =
			    tmp_dist + G_distance(easting, northing,
						  cell_easting,
						  cell_northing);
			distance[r + nextr[i]][c + nextc[i]] = cur_dist;
		    }
		}		/* end stream mode */

		if (out_elev) {
		    elevation[r + nextr[i]][c + nextc[i]] =
			elevation[r + nextr[i]][c + nextc[i]] - target_elev;
		    n_cell.target_elev = target_elev;
		}

		n_cell.r = (r + nextr[i]);
		n_cell.c = (c + nextc[i]);
		n_cell.cur_dist = cur_dist;
		fifo_insert(n_cell);
	    }
	}			/* end for i... */

	n_cell = fifo_return_del();
	r = n_cell.r;
	c = n_cell.c;
	tmp_dist = n_cell.cur_dist;
	target_elev = n_cell.target_elev;

    }				/* end while */
    return 0;
}

/* fifo functions */
int fifo_insert(POINT point)
{
    fifo_outlet[tail++] = point;
    if (tail > fifo_max)
	tail = 0;
    return 0;
}

POINT fifo_return_del(void)
{
    if (head >= fifo_max)
	head = -1;
    return fifo_outlet[++head];
}
