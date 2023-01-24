#include "local_proto.h"

Coords *writeFrag_dist(int *flagbuf, Coords *actpos, int row, int col,
                       int nrows, int ncols, double distance);
int getNeighbors(Position *res, int *flagbuf, int x, int y, int nx, int ny,
                 double distance);

int getNeighbors(Position *res, int *flagbuf, int x, int y, int nx, int ny,
                 double distance)
{
    int left, right, top, bottom;
    int i, j;
    double dist_q = distance * distance;
    int cnt = 0;

    left = x - distance < 0 ? 0 : Round(x - distance);
    right = x + distance > nx - 1 ? nx - 1 : Round(x + distance);
    top = y - distance < 0 ? 0 : Round(y - distance);
    bottom = y + distance > ny - 1 ? ny - 1 : Round(y + distance);

    for (i = left; i <= right; i++) {
        for (j = top; j <= bottom; j++) {
            if (!(i == x && j == y) && flagbuf[j * nx + i] == 1) {
                int dx = i - x;
                int dy = j - y;
                int q_sum = dx * dx + dy * dy;

                if (q_sum <= dist_q) {
                    res[cnt].x = i;
                    res[cnt].y = j;
                    cnt++;
                }
            }
        }
    }

    return cnt;
}

Coords *writeFrag_dist(int *flagbuf, Coords *actpos, int row, int col,
                       int nrows, int ncols, double distance)
{
    int x, y, i;
    Position *list = (Position *)G_malloc(nrows * ncols * sizeof(Position));
    Position *first = list;
    Position *last = list;
    int neighb_max_count = Round(4 * distance * distance);
    Position *nbr_list =
        (Position *)G_malloc(neighb_max_count * sizeof(Position));

    /* count neighbors */
    int neighbors = 0;

    if (col > 0 && flagbuf[row * ncols + col - 1] != 0)
        neighbors++;
    if (row > 0 && flagbuf[(row - 1) * ncols + col] != 0)
        neighbors++;
    if (col < ncols - 1 && flagbuf[row * ncols + col + 1] != 0)
        neighbors++;
    if (row < nrows - 1 && flagbuf[(row + 1) * ncols + col] != 0)
        neighbors++;

    /* write first cell */
    actpos->x = col;
    actpos->y = row;
    actpos->neighbors = neighbors;
    actpos++;
    flagbuf[row * ncols + col] = -1;

    /* push position on fifo-list */
    last->x = col;
    last->y = row;
    last++;

    while (first < last) {
        /* get position from fifo-list */
        int r = first->y;
        int c = first->x;

        /* add neighbors to fifo-list */
        int cnt = getNeighbors(nbr_list, flagbuf, c, r, ncols, nrows, distance);

        first++;

        for (i = 0; i < cnt; i++) {
            x = nbr_list[i].x;
            y = nbr_list[i].y;

            /* add position to fifo-list */
            last->x = x;
            last->y = y;
            last++;

            /* count neighbors */
            neighbors = 0;
            if (x > 0 && flagbuf[y * ncols + x - 1] != 0)
                neighbors++;
            if (y > 0 && flagbuf[(y - 1) * ncols + x] != 0)
                neighbors++;
            if (x < ncols - 1 && flagbuf[y * ncols + x + 1] != 0)
                neighbors++;
            if (y < nrows - 1 && flagbuf[(y + 1) * ncols + x] != 0)
                neighbors++;

            /* set values */
            actpos->x = x;
            actpos->y = y;
            actpos->neighbors = neighbors;
            actpos++;

            flagbuf[y * ncols + x] = -1;
        }
    }

    G_free(list);
    G_free(nbr_list);

    return actpos;
}

int writeFragments_dist(int *flagbuf, int nrows, int ncols, double distance)
{
    int row, col;
    int fragcount = 0;

    /* find fragments */
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            if (flagbuf[row * ncols + col] == 1) {
                fragcount++;

                fragments[fragcount] =
                    writeFrag_dist(flagbuf, fragments[fragcount - 1], row, col,
                                   nrows, ncols, distance);
            }
        }
    }

    return fragcount;
}
