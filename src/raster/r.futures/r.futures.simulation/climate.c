/*!
   \file climate.c

   \brief Functions for climate scenarios (flooding)

   (C) 2020-2021 by Anna Petrasova and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
 */
#include <math.h>
#include <stdbool.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>
#include <grass/glocale.h>

#include "inputs.h"
#include "map.h"
#include "climate.h"
#include "random.h"
#include "utils.h"

/*!
 * \brief Initialize flood response
 * \param response_relation
 */
void initialize_flood_response(struct ACDamageRelation *response_relation,
                               char **response, float stddev)
{
    response_relation->vulnerability_a = atof(response[0]);
    response_relation->vulnerability_b = atof(response[1]);
    response_relation->resilience_a = atof(response[2]);
    response_relation->resilience_b = atof(response[3]);
    response_relation->stddev = stddev;
}

void initialize_flood_log(struct FloodLog *log, int maxsize)
{
    log->steps = G_malloc(maxsize * sizeof(int));
    log->HUC_indices = G_malloc(maxsize * sizeof(int));
    log->flood_levels = G_malloc(maxsize * sizeof(float));
    log->size = 0;
}

void log_flood(struct FloodLog *log, int step, int HUC_idx,
               float flood_probability)
{
    log->steps[log->size] = step;
    log->HUC_indices[log->size] = HUC_idx;
    log->flood_levels[log->size] = flood_probability;
    log->size++;
}

void write_flood_log(struct FloodLog *log, const char *filename,
                     map_int_t *HUC_map)
{
    FILE *fp;
    int i;
    map_int_t rev_HUC_map;
    map_iter_t iter;
    int *huc_idx;
    int *huc_id;
    const char *key;
    map_init(&rev_HUC_map);

    iter = map_iter(HUC_map);
    while ((key = map_next(HUC_map, &iter))) {
        huc_idx = map_get(HUC_map, key);
        map_set_int(&rev_HUC_map, *huc_idx, atoi(key));
    }

    fp = fopen(filename, "w");
    for (i = 0; i < log->size; i++) {
        huc_id = map_get_int(&rev_HUC_map, log->HUC_indices[i]);
        fprintf(fp, "%d,%d,%.4f\n", log->steps[i], *huc_id,
                log->flood_levels[i]);
    }
    fclose(fp);
    map_deinit(&rev_HUC_map);
}
/*!
 * \brief Adapt pixel to flooding.
 *
 * Selects adaptation one step higher than the current flood.
 *
 * \param adaptation Adaptation segment
 * \param flood_probability flood probability (0 - 1)
 * \param row
 * \param col
 */
void adapt(SEGMENT *adaptation, float flood_probability, int row, int col)
{
    unsigned i;
    int rp[] = {2, 5, 10, 20, 50, 100};

    for (i = 0; i < sizeof(rp) / sizeof(int); i++) {
        if (1 / flood_probability < rp[i]) {
            i++;
            break;
        }
    }
    Segment_put(adaptation, (void *)&rp[i - 1], row, col);
}
/*!
 * \brief Check if pixel is adapted for certain flood frequency
 *
 * \param adaptation Adaptation segment
 * \param flood_probability flood probability (0 - 1)
 * \param row
 * \param col
 * \return T/F
 */
bool is_adapted(SEGMENT *adaptation, float flood_probability, int row, int col)
{
    int adapted;

    Segment_get(adaptation, (void *)&adapted, row, col);
    if (Rast_is_null_value(&adapted, CELL_TYPE) || adapted == 0)
        return false;
    return flood_probability >= (1. / adapted);
}

/*!
 * \brief Stay trapped - saves state into adaptation segment
 * \param adaptation
 * \param row
 * \param col
 */
void stay(SEGMENT *adaptation, int row, int col)
{
    int stay = 0;
    Segment_put(adaptation, (void *)&stay, row, col);
}
/*!
 * \brief Converts water depth to structural damage
 * using depth-damage-function.
 *
 * \param water depth (height from bottom of structure)
 * \param func depth-damage function
 * \return structural damage (0: no damage, 1: total destruction)
 */
static float depth_to_damage(float depth, int region_idx,
                             const struct DepthDamageFunctions *ddf)
{
    int i;

    for (i = 0; i < ddf->max_levels; i++) {
        if (depth < ddf->levels[i])
            return ddf->damage[region_idx][i] / 100;
    }
    return ddf->damage[region_idx][ddf->max_levels - 1] / 100;
}

/*!
 * \brief Returns region index for which to look up
 * DDF. If DDF is the same for entire area, returns 0.
 * Doesn't check for nulls.
 *
 * \param segments Segments
 * \param ddf DepthDamageFunctions structure
 * \param row row
 * \param col col
 * \return index of a region
 */
static int get_DDF_region_index(struct Segments *segments,
                                const struct DepthDamageFunctions *ddf, int row,
                                int col)
{
    CELL DDF_region_idx;

    if (ddf->subregions_source == DDF_CUSTOM)
        Segment_get(&segments->DDF_subregions, (void *)&DDF_region_idx, row,
                    col);
    else if (ddf->subregions_source == DDF_DEFAULT)
        Segment_get(&segments->subregions, (void *)&DDF_region_idx, row, col);
    else if (ddf->subregions_source == DDF_POTENTIAL)
        Segment_get(&segments->potential_subregions, (void *)&DDF_region_idx,
                    row, col);
    else
        DDF_region_idx = 0;

    return DDF_region_idx;
}
/*!
 * \brief Decide if flood event occurrs and if yes,
 * what probability is the flood associated with
 * (e.g. 100yr flood = 0.01)
 *
 * \param flood_probability_map contains flood frequencies/probabilities (0-1)
 * \param region_idx region index (HUC)
 * \param flood_probability resulting flood frequency (as probability)
 * \return true if flood event occures, otherwise false
 */
bool generate_flood(map_float_t *flood_probability_map, int region_idx,
                    float *flood_probability)
{
    float *max_flood_probability;
    double p;

    max_flood_probability = map_get_int(flood_probability_map, region_idx);
    if (max_flood_probability && *max_flood_probability > 0) {
        p = G_drand48();
        if (p <= *max_flood_probability) {
            *flood_probability = p;
            return true;
        }
    }
    return false;
}

/*!
 * \brief Get maximum Height Above Nearest Drainage within flooded area.
 *
 * This assumes flood probabilities do not correspond well to HAND,
 * therefore we take worst case inundation height.
 *
 * \param segments segments (flood probability and HAND)
 * \param bbox BBox of area where to search for it
 * \param flood_probability
 * \return max HAND value
 */
float get_max_HAND(struct Segments *segments, const struct BBox *bbox,
                   float flood_probability,
                   struct HAND_bbox_values *HAND_bbox_vals, float percentile)
{
    FCELL flood_probability_value;
    FCELL HAND_value;
    float max_HAND_value;
    int row, col;
    int i;

    i = 0;
    max_HAND_value = 0;
    for (row = bbox->n; row <= bbox->s; row++)
        for (col = bbox->w; col <= bbox->w; col++) {
            Segment_get(&segments->flood_probability,
                        (void *)&flood_probability_value, row, col);
            if (flood_probability_value >= flood_probability) {
                Segment_get(&segments->HAND, (void *)&HAND_value, row, col);
                if (!Rast_is_null_value(&HAND_value, FCELL_TYPE)) {
                    HAND_bbox_vals->array[i] = HAND_value;
                    i++;
                }
            }
        }
    if (i > 0)
        max_HAND_value = get_percentile(HAND_bbox_vals->array, i, percentile);
    return max_HAND_value;
}

float get_depth(SEGMENT *flood_depths, float flood_probability, int row,
                int col, FCELL *values, const struct FloodInputs *flood_inputs)
{
    int i = flood_inputs->num_return_periods;
    Segment_get(flood_depths, values, row, col);
    if (Rast_is_null_value(&values[0], FCELL_TYPE))
        return 0;
    /* assumes sorted (0.01 0.2 0.5), if in between takes the more extreme */
    /* TODO: maybe interpolate inbetween */
    while (i--) {
        if (flood_probability > flood_inputs->return_periods[i]) {
            if (Rast_is_null_value(&values[i], FCELL_TYPE))
                return 0;
            return values[i];
        }
    }
    /* if flood prob is lower than minimum, return depth for min prob flood */
    if (Rast_is_null_value(&values[0], FCELL_TYPE))
        return 0;
    return values[0];
}

float get_depth_flood_level(SEGMENT *hand, float flood_level, int row, int col)
{
    FCELL HAND_value;
    float depth;
    Segment_get(hand, (void *)&HAND_value, row, col);
    depth = flood_level - HAND_value;
    return depth > 0 ? depth : 0;
}

/*!
 * \brief Get damage caused by flooding.
 *
 * Checks if pixel was adapted (in the future adaptation
 * could be for certain level).
 * If yes, damage is 0.
 *
 * \param segments HAND and adaptation segments
 * \param ddf depth-damage functions
 * \param flood_level height of inundation
 * \param row row
 * \param col col
 * \return structural damage (0: no damage, 1: total destruction)
 */
float get_damage(struct Segments *segments,
                 const struct DepthDamageFunctions *ddf,
                 float flood_probability, float depth, int row, int col)
{
    int DDF_region_idx;
    float damage;

    damage = 0;
    if (depth > 0) {
        if (!is_adapted(&segments->adaptation, flood_probability, row, col)) {
            DDF_region_idx = get_DDF_region_index(segments, ddf, row, col);
            damage = depth_to_damage(depth, DDF_region_idx, ddf);
        }
    }
    return damage;
}

/*!
 * \brief Stochastically simulates flood response (retreat, adaptation, stay)
 * as a function of damage and adaptive capacity.
 * \param damage damage (0-1)
 * \param adaptive_capacity adaptive capacity (0-1)
 * \param response structure containing info about damage-AC relation
 * \return one of Retreat, Adapt, Stay
 */
enum FloodResponse flood_response(float damage, float adaptive_capacity,
                                  const struct ACDamageRelation *response)
{
    double x, y;
    double response_val;

    if (response->stddev == 0)
        x = y = 0;
    else
        gauss_xy(0, response->stddev, &x, &y);
    if (adaptive_capacity + x > 0) {
        response_val = response->resilience_a * (adaptive_capacity + x) +
                       response->resilience_b;
        if (damage + y > response_val)
            return Retreat;
        else
            return Adapt;
    }
    else {
        response_val = response->vulnerability_a * (adaptive_capacity + x) +
                       response->vulnerability_b;
        if (damage + y > response_val)
            return Retreat;
        else
            return Stay;
    }
}
