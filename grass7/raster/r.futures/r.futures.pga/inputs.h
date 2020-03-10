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
};

struct PatchSizes
{
    const char *filename;
    int max_patches;
    int *patch_sizes;
    int max_patch_size;
    
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
    SEGMENT predictors;
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


void initialize_incentive(struct Potential *potential_info, float exponent);
void read_input_rasters(struct RasterInputs inputs, struct Segments *segments,
                        struct SegmentMemory segment_info, struct KeyValueIntInt *region_map, 
                        struct KeyValueIntInt *potential_region_map, int num_predictors);
void read_demand_file(struct Demand *demandInfo, struct KeyValueIntInt *region_map);
void read_potential_file(struct Potential *potentialInfo, struct KeyValueIntInt *region_map,
                         int num_predictors);
void read_patch_sizes(struct PatchSizes *patch_info, double discount_factor);

#endif // FUTURES_INPUTS_H
