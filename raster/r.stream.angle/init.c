#include <grass/glocale.h>
#include "global.h"

int trib_nums(int r, int c)
{				/* calcualte number of tributuaries */
    int trib = 0;
    int i, j;
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    for (i = 1; i < 9; ++i) {
	if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) || c + nextc[i] < 0
	    || c + nextc[i] > (ncols - 1))
	    continue;
	j = (i + 4) > 8 ? i - 4 : i + 4;
	if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
	    dirs[r + nextr[i]][c + nextc[i]] == j)
	    trib++;
    }
    if (trib > 5)
	G_fatal_error
	    ("Error finding nodes. Stream and direction maps probably do not match...");
    if (trib > 3)
	G_warning("Stream network may be too dense...");

    return trib;
}				/* end trib_num */

int init_streams(void)
{
    int i;

    s_streams = (STREAM *) G_malloc((stream_num + 1) * sizeof(STREAM));
    seg_common = (SEGMENTS *) G_malloc((stream_num + 1) * sizeof(SEGMENTS));

    /*
       seg_strahler=(SEGMENTS *)G_malloc((stream_num + 1) *sizeof(SEGMENTS));
       seg_horton=(SEGMENTS *)G_malloc((stream_num + 1) *sizeof(SEGMENTS));
       seg_hack=(SEGMENTS *)G_malloc((stream_num + 1) *sizeof(SEGMENTS));
     */

    for (i = 0; i <= stream_num; ++i) {
	s_streams[i].stream = -1;
	s_streams[i].next_stream = -1;
	s_streams[i].out_stream = -1;
	s_streams[i].strahler = -1;
	s_streams[i].shreeve = -1;
	s_streams[i].hack = -1;
	s_streams[i].horton = -1;
	s_streams[i].init = -1;
	s_streams[i].trib_num = 0;
	s_streams[i].cell_num = 0;
	s_streams[i].accum = 0.;
	s_streams[i].trib[0] = 0;
	s_streams[i].trib[1] = 0;
	s_streams[i].trib[2] = 0;
	s_streams[i].trib[3] = 0;
	s_streams[i].trib[4] = 0;
	s_streams[i].init_r = -1;
	s_streams[i].init_c = -1;
	s_streams[i].out_r = -1;
	s_streams[i].out_c = -1;
	s_streams[i].stream_dir = -999;
	s_streams[i].tangent_dir = -999;

	seg_common[i].init_stream = -1;
	seg_common[i].out_stream = -1;
	seg_common[i].cell_num = -1;
	seg_common[i].seg_num = -1;
	seg_common[i].dir_angle = -1;
	seg_common[i].dir_init = -1;
	seg_common[i].dir_middle = -1;
	seg_common[i].dir_last = -1;
	seg_common[i].dir_full = -1;
	seg_common[i].angles = NULL;
	seg_common[i].lengths = NULL;
	seg_common[i].drops = NULL;
	seg_common[i].cellnums = NULL;
	seg_common[i].cats = NULL;

    }
    return 0;
}

int find_nodes(void)
{
    int d, i, j;		/* d: direction, i: iteration */
    int r, c;
    int trib_num, trib = 0;
    int next_stream = -1, cur_stream;
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };

    G_message(_("Finding nodes..."));

    springs_num = 0, outlets_num = 0;

    outlets = (int *)G_malloc((stream_num) * sizeof(int));
    springs = (int *)G_malloc((stream_num) * sizeof(int));

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {
		trib_num = trib_nums(r, c);
		trib = 0;
		d = abs(dirs[r][c]);	/* abs */
		if (r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||
		    c + nextc[d] < 0 || c + nextc[d] > (ncols - 1)) {
		    next_stream = -1;
		}
		else {
		    next_stream = streams[r + nextr[d]][c + nextc[d]];
		    if (next_stream < 1)
			next_stream = -1;
		}
		if (dirs[r][c] == 0)
		    next_stream = -1;
		cur_stream = streams[r][c];

		if (cur_stream != next_stream) {	/* building hierarchy */

		    if (outlets_num > (stream_num - 1))
			G_fatal_error
			    ("Error finding nodes. Stream and direction maps probably do not match...");

		    s_streams[cur_stream].stream = cur_stream;
		    s_streams[cur_stream].next_stream = next_stream;
		    if (next_stream < 0)
			outlets[outlets_num++] = cur_stream;	/* collecting outlets */
		}

		if (trib_num == 0) {	/* adding springs */

		    if (springs_num > (stream_num - 1))
			G_fatal_error
			    ("Error finding nodes. Stream and direction maps probably do not match...");

		    s_streams[cur_stream].trib_num = 0;
		    springs[springs_num++] = cur_stream;	/* collecting springs */
		    s_streams[cur_stream].init_r = r;
		    s_streams[cur_stream].init_c = c;
		}

		if (trib_num > 1) {	/* adding tributuaries */
		    s_streams[cur_stream].trib_num = trib_num;
		    s_streams[cur_stream].init_r = r;
		    s_streams[cur_stream].init_c = c;

		    for (i = 1; i < 9; ++i) {
			if (trib > 4)
			    G_fatal_error
				("Error finding nodes. Stream and direction maps probably do not match...");

			if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
			    c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
			    continue;

			j = (i + 4) > 8 ? i - 4 : i + 4;
			if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
			    dirs[r + nextr[i]][c + nextc[i]] == j) {
			    s_streams[cur_stream].trib[trib++] =
				streams[r + nextr[i]][c + nextc[i]];
			}
		    }		/* end for i... */

		}		/* if trib_num>1 */
	    }			/* end if streams */
	}			/* c */
    }				/* r */
    return 0;
}

int do_cum_length(void)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int i, s, d;		/* s - streams index; d - direction */
    int done = 1;
    int r, c;
    int next_r, next_c;
    int cur_stream;
    float cur_northing, cur_easting;
    float next_northing, next_easting;
    double cur_length = 0.;
    double cur_accum = 0.;

    G_message("Finding longests streams...");

    for (s = 0; s < springs_num; ++s) {	/* main loop on springs */
	r = s_streams[springs[s]].init_r;
	c = s_streams[springs[s]].init_c;
	cur_stream = s_streams[springs[s]].stream;
	cur_length = 0;
	done = 1;

	while (done) {

	    cur_northing = window.north - (r + .5) * window.ns_res;
	    cur_easting = window.west + (c + .5) * window.ew_res;
	    d = dirs[r][c];
	    next_r = r + nextr[d];
	    next_c = c + nextc[d];
	    next_northing = window.north - (next_r + .5) * window.ns_res;
	    next_easting = window.west + (next_c + .5) * window.ew_res;

	    if (d < 1 ||	/* end of route: sink */
		r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||	/*border */
		c + nextc[d] < 0 || c + nextc[d] > (ncols - 1) || streams[next_r][next_c] < 1) {	/* mask */

		cur_length = (window.ns_res + window.ew_res) / 2;
		s_streams[cur_stream].accum += cur_length;
		cur_length =
		    G_distance(next_easting, next_northing, cur_easting,
			       cur_northing);
		s_streams[cur_stream].accum += cur_length;
		s_streams[cur_stream].cell_num++;
		s_streams[cur_stream].out_r = r;
		s_streams[cur_stream].out_c = c;
		break;
	    }

	    cur_length =
		G_distance(next_easting, next_northing, cur_easting,
			   cur_northing);
	    s_streams[cur_stream].accum += cur_length;
	    s_streams[cur_stream].cell_num++;

	    if (streams[next_r][next_c] != cur_stream) {
		s_streams[cur_stream].out_r = r;
		s_streams[cur_stream].out_c = c;
		cur_stream = streams[next_r][next_c];
		cur_accum = 0;

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {
		    if (s_streams[s_streams[cur_stream].trib[i]].accum == 0) {
			done = 0;
			cur_accum = 0;
			break;	/* do not pass accum */
		    }
		    if (s_streams[s_streams[cur_stream].trib[i]].accum >
			cur_accum)
			cur_accum =
			    s_streams[s_streams[cur_stream].trib[i]].accum;
		}		/* end for i */
		s_streams[cur_stream].accum = cur_accum;
	    }			/* end if */

	    r = next_r;
	    c = next_c;

	}			/* end while */
    }				/* end for s */
    return 0;
}

int cur_orders(int cur_stream, int ordering)
{
    switch (ordering) {
    case NONE:
	return s_streams[cur_stream].stream;
	break;
    case HACK:
	return s_streams[cur_stream].hack;
	break;
    case STRAHLER:
	return s_streams[cur_stream].strahler;
	break;
    case HORTON:
	return s_streams[cur_stream].horton;
	break;
    }
    return 0;
}

/*
 * rp: previous row (most upstream row)
 * cp: previous col (most upstream col)
 * nr: next row (most downstream row)
 * nc: next col (most downstream col)
 */

float calc_dir(int rp, int cp, int rn, int cn)
{
    return
	(cp - cn) == 0 ?
	(rp - rn) > 0 ? 0 : PI :
	(cp - cn) < 0 ?
	PI / 2 + atan((rp - rn) / (float)(cp - cn)) :
	3 * PI / 2 + atan((rp - rn) / (float)(cp - cn));
}

float calc_drop(int rp, int cp, int rn, int cn)
{
    if ((elevation[rp][cp] - elevation[rn][cn]) < 0.)
	return 0.;
    else
	return elevation[rp][cp] - elevation[rn][cn];
}

float calc_length(int rp, int cp, int rn, int cn)
{

    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int d;			/* s - streams index; d - direction */
    int done = 1;
    int r, c;
    int next_r, next_c;
    float cur_northing, cur_easting;
    float next_northing, next_easting;
    float length;

    r = rp;
    c = cp;
    length = 0.;
    done = 1;

    while (done) {

	cur_northing = window.north - (r + .5) * window.ns_res;
	cur_easting = window.west + (c + .5) * window.ew_res;
	d = dirs[r][c];
	next_r = r + nextr[d];
	next_c = c + nextc[d];

	if (d < 1 ||		/* end of route: sink */
	    r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||	/*border */
	    c + nextc[d] < 0 || c + nextc[d] > (ncols - 1)) {
	    length += (window.ns_res + window.ew_res) / 2;
	    return length;
	}


	if (r == rn && c == cn) {
	    length +=
		(dirs[r][c] % 2) ? 1.41 * (window.ns_res +
					   window.ew_res) /
		2 : (window.ns_res + window.ew_res) / 2;
	    return length;
	}
	next_northing = window.north - (next_r + .5) * window.ns_res;
	next_easting = window.west + (next_c + .5) * window.ew_res;
	length +=
	    G_distance(next_easting, next_northing, cur_easting,
		       cur_northing);

	r = next_r;
	c = next_c;


    }				/* end while */
    return length;
}
