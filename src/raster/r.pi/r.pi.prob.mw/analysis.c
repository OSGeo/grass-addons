#include "local_proto.h"

int gather_positions(Position *res, int *map, int *mask, int x, int y, int sx,
                     int sizex, int sizey, int patch_only)
{
    int i, j;
    int count = 0;

    for (j = y; j < y + sizey; j++) {
        for (i = x; i < x + sizex; i++) {
            /* test if position should be considered */
            if (mask[j * sx + i] &&
                ((!patch_only || (patch_only && map[j * sx + i] > -1)))) {
                res[count].x = i;
                res[count].y = j;
                count++;
            }
        }
    }

    return count;
}

int perform_test(Position *positions, int count, int *map, int sx)
{
    int p1, p2;
    int x1, x2, y1, y2;
    int val1, val2;

    /* pick two random position */
    p1 = Random(count);
    p2 = Random(count);

    /* get both values */
    x1 = positions[p1].x;
    y1 = positions[p1].y;
    x2 = positions[p2].x;
    y2 = positions[p2].y;
    val1 = map[y1 * sx + x1];
    val2 = map[y2 * sx + x2];

    /* compare values */
    if (val1 > -1 && val1 == val2) {
        return 1;
    }
    else {
        return 0;
    }
}

void perform_analysis(DCELL *values, int *map, int *mask, int n, int size,
                      int patch_only, int sx, int sy)
{
    int x, y, nx, ny, sizex, sizey, i;
    Position *pos_arr;
    int count;
    int value;
    int progress = 0;

    if (size > 0) {
        pos_arr = (Position *)G_malloc(size * size * sizeof(Position));
    }
    else {
        pos_arr = (Position *)G_malloc(sx * sy * sizeof(Position));
    }

    nx = size > 0 ? sx - size + 1 : 1;
    ny = size > 0 ? sy - size + 1 : 1;
    sizex = size > 0 ? size : sx;
    sizey = size > 0 ? size : sy;

    /* for each window */
    for (y = 0; y < ny; y++) {
        for (x = 0; x < nx; x++) {
            /* get relevant positions */
            count = gather_positions(pos_arr, map, mask, x, y, sx, sizex, sizey,
                                     patch_only);

            if (count > 0) {
                /* perform test n times */
                value = 0;
                for (i = 0; i < n; i++) {
                    value += perform_test(pos_arr, count, map, sx);
                }
            }
            else {
                value = -1;
            }
            values[y * nx + x] = (DCELL)value / (DCELL)n;

            progress++;
            G_percent(progress, nx * ny, 1);
        }
    }

    return;
}
