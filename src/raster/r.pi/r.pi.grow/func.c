#include "local_proto.h"

int gather_border(Position *res, int neighbors, int *flagbuf, int nrows,
                  int ncols)
{
    int count = 0;

    /* traverse all cells */
    int row, col;
    Position pos;

    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            if (flagbuf[row * ncols + col] == 0) {
                /* look for a patch neighbor */
                int x, y;

                switch (neighbors) {
                case 4:
                    if ((col > 0 && flagbuf[row * ncols + col - 1] == 1) ||
                        (col < ncols - 1 &&
                         flagbuf[row * ncols + col + 1] == 1) ||
                        (row > 0 && flagbuf[(row - 1) * ncols + col] == 1) ||
                        (row < nrows - 1 &&
                         flagbuf[(row + 1) * ncols + col] == 1)) {
                        /* add position to the list */
                        pos.x = col;
                        pos.y = row;
                        res[count] = pos;
                        count++;
                    }
                    break;

                case 8:
                    for (x = col - 1; x <= col + 1; x++) {
                        for (y = row - 1; y <= row + 1; y++) {
                            if (x >= 0 && x < ncols && y >= 0 && y < nrows &&
                                !(x == col && y == row) &&
                                flagbuf[y * ncols + x] == 1) {

                                /* add position to the list */
                                pos.x = col;
                                pos.y = row;
                                res[count] = pos;
                                count++;
                                break;
                            }
                        }
                    }
                    break;
                }
            }
        }
    }

    return count;
}

int find(Position *list, int count, int row, int col)
{
    int i;

    for (i = 0; i < count; i++) {
        if (list[i].x == col && list[i].y == row) {
            return i;
        }
    }

    return -1;
}

int add_neighbors(Position *res, int count, int row, int col, int nrows,
                  int ncols, int neighbors, int *flagbuf)
{
    /* look for free neighbors and add to list */
    int x, y;
    Position pos;

    switch (neighbors) {
    case 4:
        if (col > 0 && flagbuf[row * ncols + col - 1] == 0 &&
            find(res, count, row, col - 1) < 0) {
            /* add position to the list */
            pos.x = col - 1;
            pos.y = row;
            res[count] = pos;
            count++;
        }
        if (col < ncols - 1 && flagbuf[row * ncols + col + 1] == 0 &&
            find(res, count, row, col + 1) < 0) {
            pos.x = col + 1;
            pos.y = row;
            res[count] = pos;
            count++;
        }
        if (row > 0 && flagbuf[(row - 1) * ncols + col] == 0 &&
            find(res, count, row - 1, col) < 0) {
            pos.x = col;
            pos.y = row - 1;
            res[count] = pos;
            count++;
        }
        if (row < nrows - 1 && flagbuf[(row + 1) * ncols + col] == 0 &&
            find(res, count, row + 1, col) < 0) {
            pos.x = col;
            pos.y = row + 1;
            res[count] = pos;
            count++;
        }
        break;

    case 8:
        for (x = col - 1; x <= col + 1; x++) {
            for (y = row - 1; y <= row + 1; y++) {
                if (x >= 0 && x < ncols && y >= 0 && y < nrows &&
                    !(x == col && y == row) && find(res, count, x, y) < 0 &&
                    flagbuf[y * ncols + x] == 0) {

                    /* add position to the list */
                    pos.x = x;
                    pos.y = y;
                    res[count] = pos;
                    count++;
                }
            }
        }
        break;
    }

    return count;
}

int f_circular(Position *list, int count, int neighbors, int *flagbuf,
               int nrows, int ncols)
{
    int r;
    Position *p;

    if (count == 0) {
        return 0;
    }

    /* get random position */
    r = (int)((double)rand() / (double)RAND_MAX * (double)count);

    p = list + r;

    flagbuf[p->y * ncols + p->x] = 1;

    /* delete border cell */
    count--;
    list[r] = list[count];

    /* if border level is exceeded gather new border */
    if (count == 0) {
        /* go to the next level border */
        count = gather_border(list, neighbors, flagbuf, nrows, ncols);
    }

    return count;
}

int f_random(Position *list, int count, int neighbors, int *flagbuf, int nrows,
             int ncols)
{
    /* get random position */
    int r = (int)((double)rand() / (double)RAND_MAX * (double)count);

    Position p = list[r];

    flagbuf[p.y * ncols + p.x] = 1;

    /* delete border cell */
    count--;
    list[r] = list[count];

    /* add free neighbor cells */
    count =
        add_neighbors(list, count, p.y, p.x, nrows, ncols, neighbors, flagbuf);

    return count;
}

int f_costbased(Position *list, int count, int neighbors, int *flagbuf,
                int nrows, int ncols)
{
    /* build a cost array */
    double *costbuffer;
    int i;
    double sum = 0.0;
    double inv;
    double r;
    Position pb;

    costbuffer = G_malloc(count * sizeof(double));

    for (i = 0; i < count; i++) {
        double tmp;
        Position *p = list + i;

        costbuffer[i] = costmap[p->y * ncols + p->x];
        tmp = costbuffer[i];

        costbuffer[i] += sum;
        sum += tmp;

        /* fprintf(stderr, "%0.2f ", costbuffer[i]); */
    }
    /* fprintf(stderr, "\n"); */

    /* normalize */
    inv = 1.0 / sum;

    for (i = 0; i < count; i++) {
        costbuffer[i] *= inv;
    }

    /* get random number between 0.0 and 1.0 */
    r = (double)rand() / (double)RAND_MAX;

    /* get next position */
    pb = list[0];

    for (i = 0; i < count; i++) {
        if (r < costbuffer[i]) {
            pb = list[i];
            break;
        }
    }

    if (i == count) {
        G_message("i = %d", i);
        return 0;
    }

    flagbuf[pb.y * ncols + pb.x] = 1;

    /* delete border cell */
    count--;
    list[i] = list[count];

    /* add free neighbor cells */
    count = add_neighbors(list, count, pb.y, pb.x, nrows, ncols, neighbors,
                          flagbuf);

    G_free(costbuffer);

    return count;
}
