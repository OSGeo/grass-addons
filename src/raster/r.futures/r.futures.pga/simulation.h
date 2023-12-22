#ifndef FUTURES_SIMULATION_H
#define FUTURES_SIMULATION_H

#include <grass/gis.h>

#include "inputs.h"
#include "patch.h"

enum seed_search { RANDOM, PROBABILITY };

int find_probable_seed(struct Undeveloped *undev_cells, int region);
int get_seed(struct Undeveloped *undev_cells, int region_idx,
             enum seed_search method, int *row, int *col);
double get_develop_probability_xy(struct Segments *segments, FCELL *values,
                                  struct Potential *potential_info,
                                  int region_index, int row, int col);
void recompute_probabilities(struct Undeveloped *undeveloped_cells,
                             struct Segments *segments,
                             struct Potential *potential_info);
void compute_step(struct Undeveloped *undev_cells, struct Demand *demand,
                  enum seed_search search_alg, struct Segments *segments,
                  struct PatchSizes *patch_sizes, struct PatchInfo *patch_info,
                  struct DevPressure *devpressure_info, int *patch_overflow,
                  int step, int region,
                  struct KeyValueIntInt *reverse_region_map, bool overgrow);

#endif // FUTURES_SIMULATION_H
