#include <grass/glocale.h>
#include "global.h"


int find_outlets(void)
{
    int d;		/* d: direction */
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

int fill_catchments(OUTLET outlet)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int r, c, i, j;
    float stop, val;
    POINT n_cell;

    tail = 0;
    head = -1;
    r = outlet.r;
    c = outlet.c;
    val = 1;
    stop = 0;

    distance[r][c] = stop;

    while (tail != head) {
	for (i = 1; i < 9; ++i) {
	    if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		continue;	/* out of border */
	    j = (i + 4) > 8 ? i - 4 : i + 4;
	    if (dirs[r + nextr[i]][c + nextc[i]] == j) {	/* countributing cell */

		/* if (distance[r + nextr[i]][c + nextc[i]] == 0) */
		/* continue; */ /* other outlet */

		distance[r + nextr[i]][c + nextc[i]] =
		    (distance[r + nextr[i]][c + nextc[i]] == stop) ?
		    stop : val;

		/* distance[r + nextr[i]][c + nextc[i]] = val; */
		n_cell.r = (r + nextr[i]);
		n_cell.c = (c + nextc[i]);
		fifo_insert(n_cell);
	    }
	}			/* end for i... */

	n_cell = fifo_return_del();
	r = n_cell.r;
	c = n_cell.c;
    }

    return 0;
}
