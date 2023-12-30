#include "local_proto.h"

int getNeighbors(Position *res, DCELL *map, int x, int y, int nx, int ny,
                 int nbr_cnt);

int getNeighbors(Position *res, DCELL *map, int x, int y, int nx, int ny,
                 int nbr_cnt)
{
    int left, right, top, bottom;
    int i, j;
    int cnt = 0;

    switch (nbr_cnt) {
    case 4: /* von Neumann neighborhood */
        if (x > 0 && !Rast_is_d_null_value(&map[y * nx + x - 1])) {
            res[cnt].x = x - 1;
            res[cnt].y = y;
            cnt++;
        }
        if (y > 0 && !Rast_is_d_null_value(&map[(y - 1) * nx + x])) {
            res[cnt].x = x;
            res[cnt].y = y - 1;
            cnt++;
        }
        if (x < nx - 1 && !Rast_is_d_null_value(&map[y * nx + x + 1])) {
            res[cnt].x = x + 1;
            res[cnt].y = y;
            cnt++;
        }
        if (y < ny - 1 && !Rast_is_d_null_value(&map[(y + 1) * nx + x])) {
            res[cnt].x = x;
            res[cnt].y = y + 1;
            cnt++;
        }
        break;

    case 8: /* Moore neighborhood */
        left = x > 0 ? x - 1 : 0;
        top = y > 0 ? y - 1 : 0;
        right = x < nx - 1 ? x + 1 : nx - 1;
        bottom = y < ny - 1 ? y + 1 : ny - 1;
        for (i = left; i <= right; i++) {
            for (j = top; j <= bottom; j++) {
                if (!(i == x && j == y) &&
                    !Rast_is_d_null_value(&map[j * nx + i])) {
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

void clearPatch(DCELL *map, int *flagbuf, int flagval, int row, int col,
                int nrows, int ncols, int nbr_cnt)
{
    int x, y, i;
    Position *stack = (Position *)G_malloc(nrows * ncols * sizeof(Position));
    Position *top = stack;
    Position *nbr_list = (Position *)G_malloc(8 * sizeof(Position));

    /* push position on stack */
    top->x = col;
    top->y = row;
    top++;

    while (top > stack) {
        int r, c, cnt;

        /* pop position from stack */
        top--;
        r = top->y;
        c = top->x;

        /* mark cell on the flag buffer */
        flagbuf[r * ncols + c] = flagval;

        /* delete cell from map */
        Rast_set_d_null_value(&map[r * ncols + c], 1);

        /* get neighbors */
        cnt = getNeighbors(nbr_list, map, c, r, ncols, nrows, nbr_cnt);

        /* push neighbors on the stack */
        for (i = 0; i < cnt; i++) {
            x = nbr_list[i].x;
            y = nbr_list[i].y;

            top->x = x;
            top->y = y;
            top++;
        }
    }

    G_free(stack);
    G_free(nbr_list);
}
