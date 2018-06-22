#include <grass/raster.h>
#include "global.h"

double
accumulate(CELL ** dir_buf, RASTER_MAP weight_buf, RASTER_MAP acc_buf,
	   char **done, int row, int col)
{
    int rows = weight_buf.rows, cols = weight_buf.cols;
    int i, j, neighbor_dir, loop_dir, has_inflow;
    double acc_flow;

    if (done[row][col])
	return get(acc_buf, row, col);

    if (weight_buf.map.v)
	acc_flow = get(weight_buf, row, col);
    else
	acc_flow = 1.0;

    for (i = -1; i <= 1; i++) {
	if (row + i < 0 || row + i >= rows)
	    continue;
	for (j = -1; j <= 1; j++) {
	    if (col + j < 0 || col + j >= cols || (i == 0 && j == 0))
		continue;
	    has_inflow = 0;
	    neighbor_dir = dir_buf[row + i][col + j];
	    loop_dir = 0;
	    switch (i) {
	    case -1:
		switch (j) {
		case -1:
		    if (neighbor_dir == 315) {
			has_inflow = 1;
			loop_dir = 135;
		    }
		    break;
		case 0:
		    if (neighbor_dir == 270) {
			has_inflow = 1;
			loop_dir = 90;
		    }
		    break;
		case 1:
		    if (neighbor_dir == 225) {
			has_inflow = 1;
			loop_dir = 45;
		    }
		    break;
		}
		break;
	    case 0:
		switch (j) {
		case -1:
		    if (neighbor_dir == 360) {
			has_inflow = 1;
			loop_dir = 180;
		    }
		    break;
		case 1:
		    if (neighbor_dir == 180) {
			has_inflow = 1;
			loop_dir = 360;
		    }
		    break;
		}
		break;
	    case 1:
		switch (j) {
		case -1:
		    if (neighbor_dir == 45) {
			has_inflow = 1;
			loop_dir = 225;
		    }
		    break;
		case 0:
		    if (neighbor_dir == 90) {
			has_inflow = 1;
			loop_dir = 270;
		    }
		    break;
		case 1:
		    if (neighbor_dir == 135) {
			has_inflow = 1;
			loop_dir = 315;
		    }
		    break;
		}
		break;
	    }
	    if (has_inflow && dir_buf[row][col] != loop_dir)
		acc_flow +=
		    accumulate(dir_buf, weight_buf, acc_buf, done, row + i,
			       col + j);
	}
    }

    set(acc_buf, row, col, acc_flow);
    done[row][col] = 1;

    return acc_flow;
}
