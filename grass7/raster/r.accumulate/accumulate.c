#include <grass/raster.h>
#include "global.h"

double
accumulate(CELL ** dir_buf, RASTER_MAP weight_buf, RASTER_MAP acc_buf,
	   char **done, int row, int col)
{
    int rows = weight_buf.rows, cols = weight_buf.cols;
    int i, j, neighbor_dir, loop_dir;
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
	    neighbor_dir = dir_buf[row + i][col + j];
	    loop_dir = 0;
	    switch (i) {
	    case -1:
		switch (j) {
		case -1:
		    if (neighbor_dir == SE)
			loop_dir = NW;
		    break;
		case 0:
		    if (neighbor_dir == S)
			loop_dir = N;
		    break;
		case 1:
		    if (neighbor_dir == SW)
			loop_dir = NE;
		    break;
		}
		break;
	    case 0:
		switch (j) {
		case -1:
		    if (neighbor_dir == E)
			loop_dir = W;
		    break;
		case 1:
		    if (neighbor_dir == W)
			loop_dir = E;
		    break;
		}
		break;
	    case 1:
		switch (j) {
		case -1:
		    if (neighbor_dir == NE)
			loop_dir = SW;
		    break;
		case 0:
		    if (neighbor_dir == N)
			loop_dir = S;
		    break;
		case 1:
		    if (neighbor_dir == NW)
			loop_dir = SE;
		    break;
		}
		break;
	    }
	    if (loop_dir && dir_buf[row][col] != loop_dir)
		acc +=
		    accumulate(dir_buf, weight_buf, acc_buf, done, row + i,
			       col + j);
	}
    }

    set(acc_buf, row, col, acc);
    done[row][col] = 1;

    return acc;
}
