#ifndef FUTURES_INPUTS_H
#define FUTURES_INPUTS_H

#include <stdbool.h>
#include <grass/segment.h>

#include "map.h"

enum development_type { DEV_TYPE_INITIAL = 0, DEV_TYPE_UNDEVELOPED = -1 };

enum DDF_subregions_source {
    DDF_DEFAULT = 0,
    DDF_POTENTIAL = -1,
    DDF_CUSTOM = -2,
    DDF_NONE = -3
};
struct Demand {
    const char *cells_filename;
    const char *population_filename;
    float **cells_table;
    float **population_table;
    int *years;
    int max_subregions;
    int max_steps;
    const char *separator;
    bool has_population;
};

struct Potential {
    const char *filename;
    double **predictors;
    double *intercept;
    double *devpressure;
    int *predictor_indices;
    int max_predictors;
    int max_subregions;
    float *incentive_transform;
    int incentive_transform_size;
    const char *separator;
};

struct PatchSizes {
    const char *filename;
    // array of patches
    int **patch_sizes;
    // array of number of patches per area
    int *patch_count;
    // maximum patch size
    int max_patch_size;
    // use single column for all regions
    bool single_column;
};

struct DepthDamageFunctions {
    const char *filename;
    double **damage;
    double *levels;
    int max_levels;
    int max_subregions;
    const char *separator;
    bool *loaded;
    enum DDF_subregions_source subregions_source;
};

struct SegmentMemory {
    int rows;
    int cols;
    int in_memory;
};

struct Segments {
    SEGMENT developed;
    SEGMENT subregions;
    SEGMENT potential_subregions;
    SEGMENT devpressure;
    SEGMENT aggregated_predictor;
    SEGMENT probability;
    SEGMENT weight;
    SEGMENT zone;
    SEGMENT density;
    SEGMENT density_capacity;
    SEGMENT HAND;
    SEGMENT HUC;
    SEGMENT flood_probability;
    SEGMENT adaptive_capacity;
    SEGMENT adaptation;
    SEGMENT DDF_subregions;
    SEGMENT flood_depths;
    bool use_zone;
    bool use_weight;
    bool use_potential_subregions;
    bool use_density;
    bool use_climate;
};

struct RasterInputs {
    const char *developed;
    const char *regions;
    const char *potential_regions;
    char **predictors;
    const char *devpressure;
    const char *weights;
    const char *zones;
    const char *density;
    const char *density_capacity;
    const char *HAND;
    const char *HUC;
    const char *adaptive_capacity;
    const char *adaptation;
    const char *DDF_regions;
};

struct DevelopableCell {

    size_t id;
    float probability;
    float cumulative_probability;
    bool tried;
};

struct Developables {
    int max_subregions;
    size_t *max;
    size_t *num;
    struct DevelopableCell **cells;
};

struct BBox {
    int n;
    int s;
    int e;
    int w;
};

struct BBoxes {
    int n_bbox;
    int max_bbox;
    map_int_t map;
    struct BBox *bbox;
};

struct FloodInput {
    int step;
    float return_period;
    const char *map;
};

struct FloodInputs {
    const char *filename;
    const char *separator;
    struct FloodInput *array;
    int size;
    float *return_periods;
    int num_return_periods;
    int *steps;
    int num_steps;
    bool depth;
};

// struct to hold single id, effect pair
struct Zone {
    int id;
    float effect;
    int region;
};

// dictionary-like structure for all zone id, effect pairs
struct ZoningEffects {
    struct Zone *zones;
    int num_zones;
    int num_regions;
    bool user_effects;
    float *stringency;
    const char *filename;
    const char *separator;
};

int get_developed_val_from_step(int step, bool abandon);
size_t estimate_undev_size(struct RasterInputs inputs);
void initialize_incentive(struct Potential *potential_info, float exponent);
void read_input_rasters(struct RasterInputs inputs, struct Segments *segments,
                        struct SegmentMemory segment_info,
                        map_int_t *region_map, map_int_t *reverse_region_map,
                        map_int_t *potential_region_map, map_int_t *HUC_map,
                        map_float_t *max_flood_probability_map,
                        map_int_t *DDF_region_map);
void read_predictors(struct RasterInputs inputs, struct Segments *segments,
                     const struct Potential *potential,
                     const struct SegmentMemory segment_info);
void read_demand_file(struct Demand *demandInfo, map_int_t *region_map);
void fill_predictor_map(struct RasterInputs inputs, map_int_t *predictor_map,
                        int num_predictors);
void read_potential_file(struct Potential *potentialInfo, map_int_t *region_map,
                         map_int_t *predictor_map);
void read_patch_sizes(struct PatchSizes *patch_sizes, map_int_t *region_map,
                      double discount_factor);
void read_DDF_file(struct DepthDamageFunctions *ddf, map_int_t *DDF_region_map);
void create_bboxes(SEGMENT *raster, SEGMENT *masking, struct BBoxes *bboxes);
void update_flood_probability(int step, const struct FloodInputs *flood_inputs,
                              struct Segments *segments, map_int_t *HUC_map,
                              map_float_t *max_flood_probability_map);
void read_flood_file(struct FloodInputs *flood_inputs);
void init_flood_segment(const struct FloodInputs *flood_inputs,
                        struct Segments *segments,
                        struct SegmentMemory segment_info);
void update_flood_depth(int step, const struct FloodInputs *flood_inputs,
                        struct Segments *segments,
                        map_float_t *max_flood_probability_map);
/* initialize zoning_effects to defaults */
void initialize_zoning_effects(struct ZoningEffects *zoning_effects);
/* read zoning effects from file */
void read_zoning_file(struct ZoningEffects *zoning_effects,
                      map_int_t *region_map);
/* convert zoning id to effect */
float zone_to_effect(struct ZoningEffects *zoning_effects, int id,
                     int region_idx);
#endif // FUTURES_INPUTS_H
