#ifndef FUTURES_INPUTS_H
#define FUTURES_INPUTS_H

#include <stdbool.h>
#include <grass/segment.h>

#include "keyvalue.h"


struct Demand
{
    const char *filename;
    int **table;
    int *years;
    int max_subregions;
    int max_steps;
    const char *separator;
};

struct Potential
{
    const char *filename;
    double **predictors;
    double *intercept;
    double *devpressure;
    int max_predictors;
    int max_subregions;
    float *incentive_transform;
    int incentive_transform_size;
    const char *separator;
};

struct PatchSizes
{
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

struct SegmentMemory
{
    int rows;
    int cols;
    int in_memory;
};

struct Segments
{
    SEGMENT developed;
    SEGMENT subregions;
    SEGMENT potential_subregions;
    SEGMENT devpressure;
    SEGMENT aggregated_predictor;
    SEGMENT probability;
    SEGMENT weight;
    bool use_weight;
    bool use_potential_subregions;
};

struct RasterInputs
{
    const char *developed;
    const char *regions;
    const char *potential_regions;
    char **predictors;
    const char *devpressure;
    const char *weights;
};


struct UndevelopedCell
{

    size_t id;
    float probability;
    float cumulative_probability;
    bool tried;
};

struct Undeveloped
{
    int max_subregions;
    size_t *max;
    size_t *num;
    struct UndevelopedCell **cells;
};

size_t estimate_undev_size(struct RasterInputs inputs);
void initialize_incentive(struct Potential *potential_info, float exponent);
void read_input_rasters(struct RasterInputs inputs, struct Segments *segments,
                        struct SegmentMemory segment_info, struct KeyValueIntInt *region_map,
                        struct KeyValueIntInt *reverse_region_map,
                        struct KeyValueIntInt *potential_region_map);
void read_predictors(struct RasterInputs inputs, struct Segments *segments,
                     const struct Potential *potential,
                     const struct SegmentMemory segment_info);
void read_demand_file(struct Demand *demandInfo, struct KeyValueIntInt *region_map);
void read_potential_file(struct Potential *potentialInfo, struct KeyValueIntInt *region_map,
                         int num_predictors);
void read_patch_sizes(struct PatchSizes *patch_sizes, struct KeyValueIntInt *region_map,
                      double discount_factor);

#endif // FUTURES_INPUTS_H
