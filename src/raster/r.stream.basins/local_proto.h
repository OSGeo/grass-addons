#include "io.h"
#include "local_vars.h"

int process_coors(char **answers);
int process_vector(char *in_point);

int ram_fill_basins(OUTLET outlet, CELL **basins, CELL **dirs);
int ram_add_outlets(CELL **basins, int outlets_num);
int ram_process_streams(char **cat_list, CELL **streams, int number_of_streams,
                        CELL **dirs, int lasts, int cats);

int seg_fill_basins(OUTLET outlet, SEGMENT *basins, SEGMENT *dirs);
int seg_add_outlets(SEGMENT *basins, int outlets_num);
int seg_process_streams(char **cat_list, SEGMENT *streams,
                        int number_of_streams, SEGMENT *dirs, int lasts,
                        int cats);
