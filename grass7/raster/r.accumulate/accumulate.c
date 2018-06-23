#include <grass/raster.h>
#include "global.h"

double
accumulate(CELL ** dir_buf, RASTER_MAP weight_buf, RASTER_MAP acc_buf,
	   char **done, int row, int col)
{
    static int dir_checks[3][3][2] = {
	{{SE, NW}, {S, N}, {SW, NE}},
	{{E, W}, {0, 0}, {W, E}},
	{{NE, SW}, {N, S}, {NW, SE}}
    };
    int rows = weight_buf.rows, cols = weight_buf.cols;
    int i, j;
    double acc;

    if (done[row][col])
	return get(acc_buf, row, col);

    if (weight_buf.map.v)
	acc = get(weight_buf, row, col);
    else
	acc = 1.0;

    for (i = -1; i <= 1; i++) {
	if (row + i < 0 || row + i >= rows)
	    continue;
	for (j = -1; j <= 1; j++) {
	    if (col + j < 0 || col + j >= cols || (i == 0 && j == 0))
		continue;
	    if (dir_buf[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
		dir_buf[row][col] != dir_checks[i + 1][j + 1][1])
		acc +=
		    accumulate(dir_buf, weight_buf, acc_buf, done, row + i,
			       col + j);
	}
    }

    set(acc_buf, row, col, acc);
    done[row][col] = 1;

    return acc;
}
