#include "local_proto.h"

typedef struct
{
    int x, y;
} Position;

Coords *writeFrag(DCELL * flagbuf, Coords * actpos, int row, int col,
		  int nrows, int ncols, int nbr_cnt);
int getNeighbors(Position * res, DCELL * flagbuf, int x, int y, int nx,
		 int ny, int nbr_cnt);

int getNeighbors(Position * res, DCELL * flagbuf, int x, int y, int nx,
		 int ny, int nbr_cnt)
{
    int left, right, top, bottom;
    int i, j;
    int cnt = 0;

    switch (nbr_cnt) {
    case 4:			/* von Neumann neighborhood */
	if (x > 0 && !G_is_d_null_value(&flagbuf[y * nx + x - 1])) {
	    res[cnt].x = x - 1;
	    res[cnt].y = y;
	    cnt++;
	}
	if (y > 0 && !G_is_d_null_value(&flagbuf[(y - 1) * nx + x])) {
	    res[cnt].x = x;
	    res[cnt].y = y - 1;
	    cnt++;
	}
	if (x < nx - 1 && !G_is_d_null_value(&flagbuf[y * nx + x + 1])) {
	    res[cnt].x = x + 1;
	    res[cnt].y = y;
	    cnt++;
	}
	if (y < ny - 1 && !G_is_d_null_value(&flagbuf[(y + 1) * nx + x])) {
	    res[cnt].x = x;
	    res[cnt].y = y + 1;
	    cnt++;
	}
	break;
    case 8:			/* Moore neighborhood */
	left = x > 0 ? x - 1 : 0;
	top = y > 0 ? y - 1 : 0;
	right = x < nx - 1 ? x + 1 : nx - 1;
	bottom = y < ny - 1 ? y + 1 : ny - 1;
	for (i = left; i <= right; i++) {
	    for (j = top; j <= bottom; j++) {
		if (!(i == x && j == y) &&
		    !G_is_d_null_value(&flagbuf[j * nx + i])) {
		    res[cnt].x = i;
		    res[cnt].y = j;
		    cnt++;
		}
	    }
	}
	break;
    }

    return cnt;
}

Coords *writeFrag(DCELL * flagbuf, Coords * actpos, int row, int col,
		  int nrows, int ncols, int nbr_cnt)
{
    int x, y, i;
    Position *list = (Position *) G_malloc(nrows * ncols * sizeof(Position));
    Position *first = list;
    Position *last = list;
    Position *nbr_list = (Position *) G_malloc(8 * sizeof(Position));

    /* count neighbors */
    int neighbors = 0;

    if (col <= 0 || !G_is_d_null_value(&flagbuf[row * ncols + col - 1]))
	neighbors++;
    if (row <= 0 || !G_is_d_null_value(&flagbuf[(row - 1) * ncols + col]))
	neighbors++;
    if (col >= ncols - 1 ||
	!G_is_d_null_value(&flagbuf[row * ncols + col + 1]))
	neighbors++;
    if (row >= nrows - 1 ||
	!G_is_d_null_value(&flagbuf[(row + 1) * ncols + col]))
	neighbors++;

    /* write first cell */
    actpos->x = col;
    actpos->y = row;
    actpos->neighbors = neighbors;
    actpos->value = flagbuf[row * ncols + col];
    actpos++;

    /* write position to id map */
    id_map[row * ncols + col] = fragcount - 1;

    /* delete position from buffer */
    G_set_d_null_value(&flagbuf[row * ncols + col], 1);

    /* push position on fifo-list */
    last->x = col;
    last->y = row;
    last++;

    while (first < last) {
	/* get position from fifo-list */
	int r = first->y;
	int c = first->x;

	first++;

	int left = c > 0 ? c - 1 : 0;
	int top = r > 0 ? r - 1 : 0;
	int right = c < ncols - 1 ? c + 1 : ncols - 1;
	int bottom = r < nrows - 1 ? r + 1 : nrows - 1;

	/* add neighbors to fifo-list */
	int cnt =
	    getNeighbors(nbr_list, flagbuf, c, r, ncols, nrows, nbr_cnt);

	for (i = 0; i < cnt; i++) {
	    x = nbr_list[i].x;
	    y = nbr_list[i].y;

	    /* add position to fifo-list */
	    last->x = x;
	    last->y = y;
	    last++;

	    /* count neighbors */
	    neighbors = 0;
	    if (x <= 0 || !G_is_d_null_value(&flagbuf[y * ncols + x - 1]))
		neighbors++;
	    if (y <= 0 || !G_is_d_null_value(&flagbuf[(y - 1) * ncols + x]))
		neighbors++;
	    if (x >= ncols - 1 ||
		!G_is_d_null_value(&flagbuf[y * ncols + x + 1]))
		neighbors++;
	    if (y >= nrows - 1 ||
		!G_is_d_null_value(&flagbuf[(y + 1) * ncols + x]))
		neighbors++;

	    /* set values */
	    actpos->x = x;
	    actpos->y = y;
	    actpos->neighbors = neighbors;
	    actpos->value = flagbuf[y * ncols + x];
	    actpos++;

	    /* write position to id map */
	    id_map[y * ncols + x] = fragcount - 1;

	    /* delete position from buffer */
	    G_set_d_null_value(&flagbuf[y * ncols + x], 1);
	}
    }

    G_free(list);
    G_free(nbr_list);
    return actpos;
}

void writeFragments(DCELL * flagbuf, int nrows, int ncols, int nbr_cnt)
{
    int row, col, i;
    Coords *p;

    fragcount = 0;
    Coords *actpos = fragments[0];

    /* find fragments */
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    if (!G_is_d_null_value(&flagbuf[row * ncols + col])) {
		fragcount++;

		fragments[fragcount] =
		    writeFrag(flagbuf, fragments[fragcount - 1], row, col,
			      nrows, ncols, nbr_cnt);
	    }
	}
    }

    return;
}
