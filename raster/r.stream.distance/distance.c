#include <grass/glocale.h>
#include "global.h"

int find_outlets(void)
{
    int d, i, j;		/* d: direction, i: iteration */
    int r, c;
    int next_stream = -1, cur_stream;
    int out_max = ncols + nrows;

    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    G_message(_("Finding nodes..."));
    outlets = (OUTLET *) G_malloc((out_max) * sizeof(OUTLET));

    outlets_num = 0;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {
		if (outlets_num > (out_max - 1)) {
		    out_max *= 2;
		    outlets =
			(OUTLET *) G_realloc(outlets,
					     out_max * sizeof(OUTLET));
		}

		d = abs(dirs[r][c]);	/* abs */
		if (r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||
		    c + nextc[d] < 0 || c + nextc[d] > (ncols - 1)) {
		    next_stream = -1;	/* border */
		}
		else {
		    next_stream = streams[r + nextr[d]][c + nextc[d]];
		    if (next_stream < 1)
			next_stream = -1;
		}
		if (d == 0)
		    next_stream = -1;
		cur_stream = streams[r][c];

		if (subs && outs) {	/* in stream mode subs is ignored */
		    if (cur_stream != next_stream) {	/* is outlet or node! */
			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].northing =
			    window.north - (r + .5) * window.ns_res;
			outlets[outlets_num].easting =
			    window.west + (c + .5) * window.ew_res;
			outlets_num++;
		    }
		}
		else {
		    if (cur_stream != next_stream && next_stream < 0) {	/* is outlet! */
			outlets[outlets_num].r = r;
			outlets[outlets_num].c = c;
			outlets[outlets_num].northing =
			    window.north - (r + .5) * window.ns_res;
			outlets[outlets_num].easting =
			    window.west + (c + .5) * window.ew_res;
			outlets_num++;
		    }
		}		/* end lasts */
	    }			/* end if streams */
	}			/* end for */
    }				/* end for */

    return 0;
}

int reset_distance(void)
{
    int r, c, i;

    distance = (FCELL **) G_malloc(sizeof(FCELL *) * nrows);
    if (!outs) {		/* stream mode */
	for (r = 0; r < nrows; ++r) {
	    distance[r] = (FCELL *) G_malloc(sizeof(FCELL) * ncols);
	    for (c = 0; c < ncols; ++c) {
		distance[r][c] = (streams[r][c]) ? 0 : -1;
	    }			/* r */
	}			/* r */
    }
    else {			/* outlets mode */
	for (r = 0; r < nrows; ++r) {
	    distance[r] = (FCELL *) G_malloc(sizeof(FCELL) * ncols);
	    for (c = 0; c < ncols; ++c) {
		distance[r][c] = -1;
	    }
	}
	for (i = 0; i < outlets_num; ++i) {

	    distance[outlets[i].r][outlets[i].c] = 0;
	}
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

    int r, c, val, i, j;
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
    if (head > fifo_max)
	head = -1;
    return fifo_outlet[++head];
}
