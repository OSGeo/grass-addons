#include "io.h"
#include "local_vars.h"

/* inits */
int ram_find_outlets(CELL **streams, int number_of_streams, CELL **dirs, int subs, int outs);
int ram_init_distance(CELL **streams, DCELL **distance, int outlets_num, int outs);
int ram_prep_null_elevation(DCELL **distance, DCELL **elevation);

int seg_find_outlets(SEGMENT *streams, int number_of_streams, SEGMENT *dirs, int subs, int outs);
int seg_prep_null_elevation(SEGMENT *distance, SEGMENT *elevation);
int seg_init_distance(SEGMENT *streams, SEGMENT *distance, int outlets_num, int outs);

/* calculate */
int ram_calculate_downstream(CELL **dirs, DCELL **distance, DCELL **elevation, OUTLET outlet, int outs);
int ram_fill_basins(OUTLET outlet, DCELL **distance, CELL **dirs);
int ram_calculate_upstream(DCELL **distance, CELL **dirs, DCELL **elevation, DCELL **tmp_elevation, int near);

int seg_calculate_downstream (SEGMENT *dirs, SEGMENT *distance, SEGMENT *elevation, OUTLET outlet, int outs);
int seg_fill_basins(OUTLET outlet, SEGMENT *distance, SEGMENT *dirs);
int seg_calculate_upstream(SEGMENT *distance, SEGMENT *dirs, SEGMENT *elevation, SEGMENT *tmp_elevation, int near);
