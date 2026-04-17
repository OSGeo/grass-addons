#ifndef FUTURES_PATCH_H
#define FUTURES_PATCH_H

#include <grass/segment.h>

#include "inputs.h"

#define MAX_CANDIDATE_ITER 100
#define MAX_SEED_ITER      20
#define MAX_TRIES_ITER     1000

enum slow_grow { FORCE_GROW, SKIP };
enum patch_type { PATCH_TYPE_NEW, PATCH_TYPE_REDEVELOP, PATCH_TYPE_ABANDON };

struct CandidateNeighbor {
    double selection_probability; /* dev potential s'_i */
    double ranking;               /* suitability s_i, p. 6 */
    size_t id;
};

struct CandidateNeighborsList {
    int n;
    int max_n;
    int block_size;
    struct CandidateNeighbor *candidates;
};

struct PatchInfo {
    int num_neighbors;
    float compactness_mean;
    float compactness_range;
    enum slow_grow strategy;
    // leg 1 means next step can be redeveloped
    int redevelopment_lag;
};

int get_patch_size(struct PatchSizes *patch_sizes, int region);
bool can_develop(CELL development, enum patch_type type, int step, int lag);
float get_patch_density(int *patch_cell_ids, int patch_size,
                        struct Segments *segments);
float update_patch_density(float new_density, int *patch_cell_ids,
                           int patch_size, struct Segments *segments);
void add_neighbour(int row, int col, int seed_row, int seed_col, int rows,
                   int cols, struct CandidateNeighborsList *candidate_list,
                   struct Segments *segments, struct PatchInfo *patch_info,
                   int step, enum patch_type type);
void add_neighbours(int row, int col, int seed_row, int seed_col, int rows,
                    int cols, struct CandidateNeighborsList *candidate_list,
                    struct Segments *segments, struct PatchInfo *patch_info,
                    int step, enum patch_type type);
double get_distance(int row1, int col1, int row2, int col2);
int grow_patch(int seed_row, int seed_col, int patch_size, int step, int region,
               struct PatchInfo *patch_info, struct Segments *segments,
               int *patch_overflow, int *added_ids, enum patch_type type);

#endif // FUTURES_PATCH_H
