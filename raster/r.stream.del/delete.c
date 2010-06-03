#include <grass/glocale.h>
#include "global.h"

int trib_nums(int r, int c)
{				/* calcualte number of tributuaries */
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int trib = 0;
    int i, j;

    for (i = 1; i < 9; ++i) {
	if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
	    c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
	    continue;
	j = (i + 4) > 8 ? i - 4 : i + 4;
	if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
	    dirs[r + nextr[i]][c + nextc[i]] == j)
	    trib++;
    }
    if (trib > 5)
	G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));

    return trib;
}				/* end trib_num */


int find_springs(int max_link)
{
    int r, c;
    int trib_num;
    int springs_num = 0;

    G_message(_("Finding springs..."));

    springs = (SPRING *) G_malloc(max_link * sizeof(SPRING));

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {
		trib_num = trib_nums(r, c);
		if (trib_num == 0) {	/* adding springs */

		    if (springs_num > (max_link - 1))
			G_fatal_error(_("Error finding nodes. Stream and direction maps probably do not match..."));

		    springs[springs_num].r = r;
		    springs[springs_num].c = c;
		    springs[springs_num++].val = streams[r][c];	/* collecting springs */
		}


	    }			/* end if streams */
	}			/* c */
    }				/* r */
    return springs_num;
}

int delete_join(int springs_num)
{
    int i, j, d;
    int r, c, nr, nc;
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int cell_num = 1;
    int cur_stream, tmp_stream;
    int trib_num;

    G_message(_("Deleting short streams..."));

    for (j = 0; j < springs_num; ++j) {

	r = springs[j].r;
	c = springs[j].c;
	cell_num = 1;

	while (cell_num < threshold && dirs[r][c] > 0) {
	    nr = r + nextr[dirs[r][c]];
	    nc = c + nextc[dirs[r][c]];

	    if (streams[nr][nc] == streams[r][c]) {
		cell_num++;
		r = nr;
		c = nc;
	    }
	    else {
		break;		/* if stream isn't longer due to joining in previous interation */
	    }

	}			/*end while */

	if (cell_num < threshold) {

	    r = springs[j].r;
	    c = springs[j].c;
	    cur_stream = streams[r][c];
	    streams[r][c] = 0;
	    nr = r + nextr[dirs[r][c]];
	    nc = c + nextc[dirs[r][c]];

	    while (dirs[r][c] > 0 && streams[nr][nc] == cur_stream) {	/* only when there is more than one cell in stream */
		r = nr;
		c = nc;
		streams[r][c] = 0;
		nr = r + nextr[dirs[r][c]];
		nc = c + nextc[dirs[r][c]];
	    }

	    trib_num = trib_nums(nr, nc);	/* check if there are no addational tributuaries */

	    if (trib_num != 1) {
		continue;	/* still is node (>1), or border (==0) finish and go to the next spring */
	    }
	    else {
		r = nr;
		c = nc;
		cur_stream = 0;
		for (i = 1; i < 9; ++i) {
		    if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1) ||
			c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
			continue;	/* border */
		    d = (i + 4) > 8 ? i - 4 : i + 4;
		    if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
			dirs[r + nextr[i]][c + nextc[i]] == d)
			cur_stream = streams[r + nextr[i]][c + nextc[i]];
		}
		if (cur_stream == 0)
		    G_fatal_error(_("Problem with joining streams"));

		tmp_stream = streams[r][c];
		nr = r + nextr[dirs[r][c]];
		nc = c + nextc[dirs[r][c]];
		streams[r][c] = cur_stream;

		while (dirs[r][c] > 0 && streams[nr][nc] == tmp_stream) {
		    r = nr;
		    c = nc;
		    nr = r + nextr[dirs[r][c]];
		    nc = c + nextc[dirs[r][c]];
		    streams[r][c] = cur_stream;
		}
	    }			/*end if_elese */
	}			/* end if cell_num */
    }				/*end for */
    return 0;
}				/*end function */
