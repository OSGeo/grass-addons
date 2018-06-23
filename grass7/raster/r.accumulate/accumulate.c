#include <math.h>
#include <grass/raster.h>
#include "global.h"

#define NW 135
#define N 90
#define NE 45
#define E 360
#define SE 315
#define S 270
#define SW 225
#define W 180

double
accumulate(CELL ** dir_buf, RASTER_MAP weight_buf, RASTER_MAP acc_buf,
           char **done, char neg, int row, int col)
{
    static int dir_checks[3][3][2] = {
        {{SE, NW}, {S, N}, {SW, NE}},
        {{E, W}, {0, 0}, {W, E}},
        {{NE, SW}, {N, S}, {NW, SE}}
    };
    int rows = weight_buf.rows, cols = weight_buf.cols;
    int i, j;
    char incomplete = 0;
    double acc;

    if (done[row][col])
        return fabs(get(acc_buf, row, col));

    if (weight_buf.map.v)
        acc = get(weight_buf, row, col);
    else
        acc = 1.0;

    for (i = -1; i <= 1; i++) {
        if (row + i < 0 || row + i >= rows) {
            incomplete = 1;
            continue;
        }
        for (j = -1; j <= 1; j++) {
            if (i == 0 && j == 0)
                continue;
            if (col + j < 0 || col + j >= cols) {
                incomplete = 1;
                continue;
            }
            if (dir_buf[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                dir_buf[row][col] != dir_checks[i + 1][j + 1][1]) {
                acc +=
                    accumulate(dir_buf, weight_buf, acc_buf, done, neg,
                               row + i, col + j);
                if (done[row + i][col + j] == 2)
                    incomplete = 1;
            }
        }
    }

    set(acc_buf, row, col, neg && incomplete ? -acc : acc);
    done[row][col] = 1 + incomplete;

    return acc;
}
