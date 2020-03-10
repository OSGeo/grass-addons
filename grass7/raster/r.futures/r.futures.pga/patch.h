#ifndef FUTURES_PATCH_H
#define FUTURES_PATCH_H

#include <grass/segment.h>

#include "inputs.h"


#define MAX_CANDIDATE_ITER 100
#define MAX_SEED_ITER 20

enum slow_grow { FORCE_GROW, SKIP };

struct CandidateNeighbor{
    double potential;      /* s'_i */
    double suitability;    /* s_i */
    size_t id;
    
};

struct CandidateNeighborsList
{
    int n;
    int max_n;
    int block_size;
    struct CandidateNeighbor *candidates;
    
};

struct PatchInfo
{
    int num_neighbors;
    float compactness_mean;
    float compactness_range;
    enum slow_grow strategy;
    
};

int get_patch_size(struct PatchSizes *patch_sizes);
void add_neighbour(int row, int col, int seed_row, int seed_col,
                   struct CandidateNeighborsList *candidate_list,
                   struct Segments *segments, struct PatchInfo *patch_info);
void add_neighbours(int row, int col, int seed_row, int seed_col,
                    struct CandidateNeighborsList *candidate_list,
                    struct Segments *segments,
                    struct PatchInfo *patch_info);
double get_distance(int row1, int col1, int row2, int col2);
int grow_patch(int seed_row, int seed_col, int patch_size, int step, int region,
               struct PatchInfo *patch_info, struct Segments *segments, int *patch_overflow, int *added_ids);

#endif // FUTURES_PATCH_H
