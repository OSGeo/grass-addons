#ifndef FUTURES_REDISTRIBUTE_H
#define FUTURES_REDISTRIBUTE_H

#include "map.h"
#include "inputs.h"

struct RedistributionMatrix {
    const char *filename;
    const char *output_basename;
    float **probabilities;
    float **moved_px;
    int dim_from;
    int dim_to;
    int max_dim_from;
    map_int_t from_map;         /* key is 'from' region id */
    map_int_t to_map;           /* key is 'to' region index */
    map_int_t reverse_from_map; /* key is 'from' region index */
};

void redistribute(struct RedistributionMatrix *matrix, struct Demand *demand,
                  int regionID, int num_px, map_int_t *region_map, int step,
                  float *leaving_population);
void read_redistribution_matrix(struct RedistributionMatrix *matrix);
bool check_matrix_filenames_exist(const struct RedistributionMatrix *matrix,
                                  int nsteps);
void write_redistribution_matrix(struct RedistributionMatrix *matrix, int step,
                                 int nsteps);
void free_redistribution_matrix(struct RedistributionMatrix *matrix);
#endif // FUTURES_REDISTRIBUTE_H
