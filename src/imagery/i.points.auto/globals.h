#include "defs.h"
#include "crs.h"

#ifndef GLOBAL
#define GLOBAL extern
#endif

GLOBAL struct Control_Points sPoints;
GLOBAL struct Cell_head cellhd1;
GLOBAL struct Cell_head cellhd2;
GLOBAL struct Cell_head curr_window;
GLOBAL struct Cell_head tgt_window;
GLOBAL double rms_threshold;

GLOBAL int correlation_window_dim;
GLOBAL int K;
GLOBAL int transform_order;
GLOBAL int n_new_points;
GLOBAL int detail;

GLOBAL Group group;

GLOBAL char interrupt_char;
GLOBAL char *tempfile1;
GLOBAL char *tempfile2;
GLOBAL char *tempfile3;
