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
    if (trib > 5)
	G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));
    if (trib > 3)
	G_warning(_("Stream network may be too dense..."));

    return trib;
}				/* end trib_num */

int init_streams(int stream_num)
{
    int i;

    s_streams = (STREAM *) G_malloc((stream_num + 1) * sizeof(STREAM));
    for (i = 0; i <= stream_num; ++i) {
	s_streams[i].next_stream = -1;
	s_streams[i].stream = -1;
	s_streams[i].trib_num = -1;
	s_streams[i].strahler = -1;
	s_streams[i].shreeve = -1;
	s_streams[i].hack = -1;
	s_streams[i].horton = -1;
	s_streams[i].accum = 0.;
	s_streams[i].length = 0.;
	s_streams[i].stright = 0.;
	s_streams[i].fractal = 0.;
	s_streams[i].distance = 0.;
	s_streams[i].topo_dim = 0;
	s_streams[i].trib[0] = 0;
	s_streams[i].trib[1] = 0;
	s_streams[i].trib[2] = 0;
	s_streams[i].trib[3] = 0;
	s_streams[i].trib[4] = 0;
    }
    return 0;
}

int find_nodes(int stream_num)
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
    s_inits = (INITS *) G_malloc((stream_num) * sizeof(INITS));

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
			G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));

		    s_streams[cur_stream].stream = cur_stream;
		    s_streams[cur_stream].next_stream = next_stream;
		    if (next_stream < 0)
			outlets[outlets_num++] = cur_stream;	/* collecting outlets */
		}

		if (trib_num == 0) {	/* adding springs */

		    if (springs_num > (stream_num - 1))
			G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));

		    s_streams[cur_stream].trib_num = 0;
		    s_inits[springs_num].r = r;
		    s_inits[springs_num].c = c;
		    springs[springs_num++] = cur_stream;	/* collecting springs */

		}

		if (trib_num > 1) {	/* adding tributuaries */
		    s_streams[cur_stream].trib_num = trib_num;
		    /* G_message("HERE %d %d", cur_stream, s_streams[cur_stream].trib_num); */

		    for (i = 1; i < 9; ++i) {
			if (trib > 4)
			    G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));

			if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
			    c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
			    continue;

			j = (i + 4) > 8 ? i - 4 : i + 4;
			if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
			    dirs[r + nextr[i]][c + nextc[i]] == j) {
			    if (in_accum) {	/* only if accum map is selected */
				s_streams[streams[r + nextr[i]]
					  [c + nextc[i]]].accum =
				    fabs(accum[r + nextr[i]][c + nextc[i]]);
			    }
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
    float init_northing, init_easting;
    double cur_length = 0.;
    double cur_accum = 0.;

    G_message(_("Finding longests streams..."));
    G_begin_distance_calculations();

    for (s = 0; s < springs_num; ++s) {	/* main loop on springs */
	r = s_inits[s].r;
	c = s_inits[s].c;
	cur_stream = streams[r][c];
	cur_length = 0;
	done = 1;

	init_northing = window.north - (r + .5) * window.ns_res;
	init_easting = window.west + (c + .5) * window.ew_res;

	while (done) {

	    cur_northing = window.north - (r + .5) * window.ns_res;
	    cur_easting = window.west + (c + .5) * window.ew_res;

	    d = dirs[r][c];
	    next_r = r + nextr[d];
	    next_c = c + nextc[d];

	    if (d < 1 ||	/* end of route: sink */
		r + nextr[d] < 0 || r + nextr[d] > (nrows - 1) ||	/*border */
		c + nextc[d] < 0 || c + nextc[d] > (ncols - 1) || streams[next_r][next_c] < 1) {	/* mask */

		cur_length = (window.ns_res + window.ew_res) / 2;
		s_streams[cur_stream].accum += cur_length;
		s_streams[cur_stream].length += cur_length;
		s_streams[cur_stream].stright =
		    G_distance(cur_easting, cur_northing, init_easting,
			       init_northing);
		s_streams[cur_stream].fractal =
		    s_streams[cur_stream].length /
		    s_streams[cur_stream].stright;
		break;
	    }

	    next_northing = window.north - (next_r + .5) * window.ns_res;
	    next_easting = window.west + (next_c + .5) * window.ew_res;
	    cur_length =
		G_distance(next_easting, next_northing, cur_easting,
			   cur_northing);
	    s_streams[cur_stream].accum += cur_length;
	    s_streams[cur_stream].length += cur_length;
	    r = next_r;
	    c = next_c;

	    if (streams[next_r][next_c] != cur_stream) {
		s_streams[cur_stream].stright =
		    G_distance(next_easting, next_northing, init_easting,
			       init_northing);
		s_streams[cur_stream].fractal =
		    s_streams[cur_stream].length /
		    s_streams[cur_stream].stright;
		init_northing = cur_northing;
		init_easting = cur_easting;

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
		if (!in_accum)
		    s_streams[cur_stream].accum = cur_accum;
	    }			/* end if */
	}			/* end while */
    }				/* end for s */
    return 0;
}


/* 
   All algorithms used in analysis ar not recursive. For Strahler order and Shreve magnitude starts from initial channel and  proceed downstream. Algortitms try to assgin order for branch and if it is imposible start from next initial channel, till all branches are ordered.
   For Hortor and Hack ordering it proceed upstream and uses stack data structure to determine unordered branch. 
   Strahler stream order algorithm according idea of Victor Olaya' (SAGA GIS), but without recusion.
   Algorithm of Hack main stram according idea of Markus Metz .
 */


int strahler(void)
{
    int i, j, done = 1;
    int cur_stream, next_stream;
    int max_strahler = 0, max_strahler_num;

    G_message(_("Calculating Strahler's stream order ..."));

    for (j = 0; j < springs_num; ++j) {	/* main loop on springs */

	cur_stream = s_streams[springs[j]].stream;
	do {			/* we must go at least once, if stream is of first order and is outlet */
	    max_strahler_num = 1;
	    max_strahler = 0;
	    next_stream = s_streams[cur_stream].next_stream;

	    if (s_streams[cur_stream].trib_num == 0) {	/* assign 1 for spring stream */
		s_streams[cur_stream].strahler = 1;
		cur_stream = next_stream;
		done = 1;
	    }
	    else {
		done = 1;

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* loop for determining strahler */
		    if (s_streams[s_streams[cur_stream].trib[i]].strahler < 0) {
			done = 0;
			break;	/* strahler is not determined, break for loop */
		    }
		    else if (s_streams[s_streams[cur_stream].trib[i]].strahler
			     > max_strahler) {
			max_strahler =
			    s_streams[s_streams[cur_stream].trib[i]].strahler;
			max_strahler_num = 1;
		    }
		    else if (s_streams[s_streams[cur_stream].trib[i]].strahler
			     == max_strahler) {
			++max_strahler_num;
		    }
		}		/* end determining strahler */

		if (done == 1) {
		    s_streams[cur_stream].strahler =
			(max_strahler_num >
			 1) ? ++max_strahler : max_strahler;
		    cur_stream = next_stream;	/* if next_stream<0 we in outlet stream */
		}

	    }
	} while (done && next_stream > 0);
    }				/* end for of main loop */
    return 0;
}				/* end strahler */

int shreeve(void)
{
    int i, j, done = 1;
    int cur_stream, next_stream;
    int max_shreeve = 0;

    G_message(_("Calculating Shreeve's stream magnitude ..."));

    for (j = 0; j < springs_num; ++j) {	/* main loop on springs */

	cur_stream = s_streams[springs[j]].stream;
	do {			/* we must go at least once, if stream is of first order and is outlet */

	    max_shreeve = 0;
	    next_stream = s_streams[cur_stream].next_stream;

	    if (s_streams[cur_stream].trib_num == 0) {	/* assign 1 for spring stream */

		s_streams[cur_stream].shreeve = 1;
		cur_stream = next_stream;
		done = 1;

	    }
	    else {
		done = 1;

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* loop for determining strahler */
		    if (s_streams[s_streams[cur_stream].trib[i]].shreeve < 0) {
			done = 0;
			break;	/* shreeve is not determined, break for loop */
		    }
		    else {
			max_shreeve +=
			    s_streams[s_streams[cur_stream].trib[i]].shreeve;
		    }
		}		/* end determining strahler */

		if (done == 1) {
		    s_streams[cur_stream].shreeve = max_shreeve;
		    cur_stream = next_stream;	/* if next_stream<0 we in outlet stream */
		}
	    }

	} while (done && next_stream > 0);
    }				/* end main loop */
    return 0;
}				/* end shreeve */

int horton(void)
{
    int *stack;
    int top, i, j;
    int cur_stream, cur_horton;
    int max_strahler;
    double max_accum;
    int up_stream = 0;

    G_message(_("Calculating Hortons's stream order ..."));
    stack = (int *)G_malloc(stack_max * sizeof(int));

    for (j = 0; j < outlets_num; ++j) {
	cur_stream = s_streams[outlets[j]].stream;	/* outlet: init */
	cur_horton = s_streams[cur_stream].strahler;
	stack[0] = 0;
	stack[1] = cur_stream;
	top = 1;

	do {			/* on every stream */
	    max_strahler = 0;
	    max_accum = 0;

	    if (s_streams[cur_stream].trib_num == 0) {	/* spring: go back on stack */

		s_streams[cur_stream].horton = cur_horton;
		cur_stream = stack[--top];

	    }
	    else if (s_streams[cur_stream].trib_num > 1) {	/* node */

		up_stream = 0;	/* calculating up_stream */
		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {
		    if (s_streams[s_streams[cur_stream].trib[i]].horton < 0) {

			if (s_streams[s_streams[cur_stream].trib[i]].strahler
			    > max_strahler) {
			    max_strahler =
				s_streams[s_streams[cur_stream].
					  trib[i]].strahler;
			    max_accum =
				s_streams[s_streams[cur_stream].
					  trib[i]].accum;
			    up_stream = s_streams[cur_stream].trib[i];

			}
			else if (s_streams
				 [s_streams[cur_stream].trib[i]].strahler ==
				 max_strahler) {

			    if (s_streams[s_streams[cur_stream].trib[i]].accum
				> max_accum) {
				max_accum =
				    s_streams[s_streams[cur_stream].
					      trib[i]].accum;
				up_stream = s_streams[cur_stream].trib[i];
			    }
			}
		    }
		}		/* end determining up_stream */

		if (up_stream) {	/* at least one branch is not assigned */
		    if (s_streams[cur_stream].horton < 0) {
			s_streams[cur_stream].horton = cur_horton;
		    }
		    else {
			cur_horton = s_streams[up_stream].strahler;
		    }
		    cur_stream = up_stream;
		    stack[++top] = cur_stream;

		}
		else {		/* all asigned, go downstream */
		    cur_stream = stack[--top];

		}		/* end up_stream */
	    }			/* end spring/node */
	} while (cur_stream);
    }				/* end for outlets */
    G_free(stack);
    return 0;
}

int hack(void)
{				/* also calculate topological dimension */
    int *stack;
    int top, i, j;
    int cur_stream, cur_hack;
    double max_accum;
    int up_stream = 0;
    double cur_distance = 0;

    G_message(_("Calculating Hack's main streams and topological dimension..."));
    stack = (int *)G_malloc(stack_max * sizeof(int));

    for (j = 0; j < outlets_num; ++j) {

	cur_stream = s_streams[outlets[j]].stream;	/* outlet: init */
	cur_hack = 1;
	stack[0] = 0;
	stack[1] = cur_stream;
	top = 1;

	s_streams[cur_stream].topo_dim = top;
	cur_distance = s_streams[cur_stream].distance =
	    s_streams[cur_stream].length;
	do {
	    max_accum = 0;

	    if (s_streams[cur_stream].trib_num == 0) {	/* spring: go back on stack */

		s_streams[cur_stream].hack = cur_hack;
		cur_stream = stack[--top];

	    }
	    else if (s_streams[cur_stream].trib_num > 1) {	/* node */
		up_stream = 0;	/* calculating up_stream */

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* determining upstream */
		    if (s_streams[s_streams[cur_stream].trib[i]].hack < 0) {
			if (s_streams[s_streams[cur_stream].trib[i]].accum >
			    max_accum) {
			    max_accum =
				s_streams[s_streams[cur_stream].
					  trib[i]].accum;
			    up_stream = s_streams[cur_stream].trib[i];
			}
		    }
		}		/* end determining up_stream */

		if (up_stream) {	/* at least one branch is not assigned */

		    if (s_streams[cur_stream].hack < 0) {
			s_streams[cur_stream].hack = cur_hack;
		    }
		    else {
			cur_hack = s_streams[cur_stream].hack;
			++cur_hack;

		    }

		    cur_distance = s_streams[cur_stream].distance;

		    cur_stream = up_stream;
		    stack[++top] = cur_stream;

		    s_streams[cur_stream].distance =
			cur_distance + s_streams[cur_stream].length;
		    s_streams[cur_stream].topo_dim = top;


		}
		else {		/* all asigned, go downstream */
		    cur_stream = stack[--top];

		}		/* end up_stream */
	    }			/* end spring/node */
	} while (cur_stream);
    }				/* end for outlets */
    G_free(stack);
    return 0;
}
