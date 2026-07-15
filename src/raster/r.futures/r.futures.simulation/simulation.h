#ifndef FUTURES_SIMULATION_H
#define FUTURES_SIMULATION_H

#include <grass/gis.h>

#include "map.h"
#include "inputs.h"
#include "patch.h"
#include "redistribute.h"
#include "climate.h"

enum seed_search { RANDOM, PROBABILITY };

int find_probable_seed(struct Developables *dev_cells, int region);
int get_seed(struct Developables *dev_cells, int region_idx,
             enum seed_search method, int *row, int *col);
double get_develop_probability_xy(struct Segments *segments, FCELL *values,
                                  struct Potential *potential_info,
                                  int region_index, int row, int col,
                                  struct ZoningEffects *zoning_effects);
void recompute_probabilities(struct Developables *developable_cells,
                             struct Segments *segments,
                             struct Potential *potential_info,
                             bool use_developed,
                             struct ZoningEffects *zoning_effects);
void attempt_grow_patch(
    struct Developables *dev_cells, enum seed_search search_alg,
    struct Segments *segments, struct PatchSizes *patch_sizes,
    struct PatchInfo *patch_info, struct DevPressure *devpressure_info,
    int *patch_overflow, int step, int region, enum patch_type type,
    bool overgrow, bool force_convert_all, bool *allow_already_tried_ones,
    int *unsuccessful_tries, int *patch_ids, int total_cells_to_convert,
    int *cells_converted, float *popul_placed);
void compute_step(struct Developables *undev_cells,
                  struct Developables *dev_cells, struct Demand *demand,
                  enum seed_search search_alg, struct Segments *segments,
                  struct PatchSizes *patch_sizes, struct PatchInfo *patch_info,
                  struct DevPressure *devpressure_info, int *patch_overflow,
                  float *population_overflow,
                  struct RedistributionMatrix *redistr_matrix, int step,
                  int region, map_int_t *reverse_region_map, bool overgrow);
void climate_step(struct Segments *segments, struct Demand *demand,
                  struct BBoxes *bboxes, struct RedistributionMatrix *matrix,
                  map_int_t *region_map, map_int_t *reverse_region_map,
                  int step, float *leaving_population,
                  struct HAND_bbox_values *HAND_bbox_vals, float percentile,
                  map_float_t *flood_probability_map,
                  const struct FloodInputs *flood_inputs, struct FloodLog *log,
                  const struct DepthDamageFunctions *ddf,
                  const struct ACDamageRelation *response_relation,
                  int HUC_idx);

#endif // FUTURES_SIMULATION_H
