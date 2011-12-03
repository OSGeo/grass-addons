#include <stdio.h>
#include <stdlib.h>
#include <grass/glocale.h>
#include "global.h"

int trib_nums(int r, int c)
{				/* calculate number of tributuaries */
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int trib = 0;
    int i, j;

    for (i = 1; i < 9; ++i) {
	if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) || c + nextc[i] < 0
	    || c + nextc[i] > (ncols - 1))
	    continue;

	j = (i + 4) > 8 ? i - 4 : i + 4;

	if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
	    dirs[r + nextr[i]][c + nextc[i]] == j)
	    trib++;
    }

    if (trib > 1) {
	for (i = 1; i < 9; ++i) {
	    if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
		c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		continue;

	    j = (i + 4) > 8 ? i - 4 : i + 4;

	    if (streams[r + nextr[i]][c + nextc[i]] == streams[r][c] &&
		dirs[r + nextr[i]][c + nextc[i]] == j)
		trib--;
	}
    }

    if (trib > 5)
	G_fatal_error
	    ("Error finding inits. Stream and direction maps probably do not match...");
    if (trib > 3)
	G_warning("Stream network may be too dense...");

    return trib;
}				/* end trib_num */


int find_inits(void)
{
    int r, c;

    stream_num = 0;

    s_streams = (STREAM *) G_malloc((nrows + ncols) * sizeof(STREAM));
    G_message("Finding inits...");

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {

		if (trib_nums(r, c) != 1) {	/* adding inits */

		    if (stream_num > (2 * (nrows + ncols)))
			G_fatal_error
			    ("Error finding inits. Stream and direction maps probably do not match...");
		    if (stream_num > (nrows + ncols))	/* almost not possible */
			s_streams =
			    G_realloc(s_streams,
				      2 * (nrows + ncols) * sizeof(STREAM));

		    s_streams[stream_num].stream = streams[r][c];
		    s_streams[stream_num].init_r = r;
		    s_streams[stream_num++].init_c = c;
		}
	    }			/* end if streams */
	}			/* c */
    }				/* r */
    return 0;
}

int calculate(void)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int s, d;		/* s - streams index; d - direction */
    int done = 1;
    int r, c;
    int next_r, next_c;
    int cur_stream;
    int cur_cat;
    float cur_northing, cur_easting;
    float next_northing, next_easting;
    int cur_pixel;
    float cur_length = 0.;
    float cur_accum = 0.;

    G_message("Calculating...");
    G_begin_distance_calculations();

    for (s = 0; s < stream_num + 1; ++s) {	/* main loop on treams */

	if (s_streams[s].stream < 0)
	    continue;

	r = s_streams[s].init_r;
	c = s_streams[s].init_c;

	cur_stream = streams[r][c];
	cur_cat = (seq_cats) ? cur_stream : s;

	cur_length = 0.;
	cur_accum = 0.;
	cur_pixel = 0;
	done = 1;

	while (done) {

	    cur_northing = window.north - (r + .5) * window.ns_res;
	    cur_easting = window.west + (c + .5) * window.ew_res;
	    d = dirs[r][c];
	    next_r = r + nextr[d];
	    next_c = c + nextc[d];

	    if (d < 1 ||	/* end of route: sink */
		r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||	/*border */
		c + nextc[d] < 0 || c + nextc[d] > (ncols - 1) || streams[next_r][next_c] < 1) {	/* mask */

		cur_accum += (window.ns_res + window.ew_res) / 2;
		cur_pixel++;

		if (out_streams_length)
		    streams_length[r][c] = cur_accum;
		if (out_streams)
		    streams[r][c] = cur_cat * multipier + cur_pixel;
		break;
	    }

	    next_northing = window.north - (next_r + .5) * window.ns_res;
	    next_easting = window.west + (next_c + .5) * window.ew_res;
	    cur_length =
		G_distance(next_easting, next_northing, cur_easting,
			   cur_northing);
	    cur_accum += cur_length;
	    cur_pixel++;

	    if (out_streams_length)
		streams_length[r][c] = cur_accum;
	    if (out_streams)
		streams[r][c] = cur_cat * multipier + cur_pixel;

	    r = next_r;
	    c = next_c;

	    if (streams[next_r][next_c] != cur_stream)
		break;

	}			/* end while */
    }				/* end for s */
    return 0;
}
