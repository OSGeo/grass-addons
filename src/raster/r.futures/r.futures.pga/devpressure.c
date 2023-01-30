/*!
   \file devpressure.c

   \brief Functions to compute development pressure

   (C) 2016-2019 by Anna Petrasova, Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
   \author Vaclav Petras
 */

#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/segment.h>

#include "devpressure.h"
#include "utils.h"

/*!
 * \brief Update development pressure for neighborhood of a single cell
 *
 *
 * \param row cell row
 * \param col cell column
 * \param segments segments
 * \param devpressure_info Development pressure parameters
 */
void update_development_pressure(int row, int col, struct Segments *segments,
                                 struct DevPressure *devpressure_info)
{
    int i, j;
    int cols, rows;
    double dist;
    double value;
    FCELL devpressure_value;

    cols = Rast_window_cols();
    rows = Rast_window_rows();
    /* this can be precomputed */
    for (i = row - devpressure_info->neighborhood;
         i <= row + devpressure_info->neighborhood; i++) {
        for (j = col - devpressure_info->neighborhood;
             j <= col + devpressure_info->neighborhood; j++) {
            if (i < 0 || j < 0 || i >= rows || j >= cols)
                continue;
            dist = get_distance(row, col, i, j);
            if (dist > devpressure_info->neighborhood)
                continue;
            if (devpressure_info->alg == OCCURRENCE)
                value = 1;
            else if (devpressure_info->alg == GRAVITY)
                value = devpressure_info->scaling_factor /
                        pow(dist, devpressure_info->gamma);
            else
                value = devpressure_info->scaling_factor *
                        exp(-2 * dist / devpressure_info->gamma);
            Segment_get(&segments->devpressure, (void *)&devpressure_value, i,
                        j);
            if (Rast_is_null_value(&devpressure_value, FCELL_TYPE))
                continue;
            devpressure_value += value;
            Segment_put(&segments->devpressure, (void *)&devpressure_value, i,
                        j);
        }
    }
}

/*!
 * \brief Update development pressure for neighborhood of a single cell
 *
 * Uses precomputed matrix to speed up computation.
 *
 * \param row cell row
 * \param col cell column
 * \param segments segments
 * \param devpressure_info Development pressure parameters
 */
void update_development_pressure_precomputed(
    int row, int col, struct Segments *segments,
    struct DevPressure *devpressure_info)
{
    int i, j, mi, mj;
    int cols, rows;
    float value;
    FCELL devpressure_value;

    cols = Rast_window_cols();
    rows = Rast_window_rows();
    for (i = row - devpressure_info->neighborhood;
         i <= row + devpressure_info->neighborhood; i++) {
        for (j = col - devpressure_info->neighborhood;
             j <= col + devpressure_info->neighborhood; j++) {
            if (i < 0 || j < 0 || i >= rows || j >= cols)
                continue;
            mi = devpressure_info->neighborhood - (row - i);
            mj = devpressure_info->neighborhood - (col - j);
            value = devpressure_info->matrix[mi][mj];
            if (value > 0) {
                Segment_get(&segments->devpressure, (void *)&devpressure_value,
                            i, j);
                if (Rast_is_null_value(&devpressure_value, FCELL_TYPE))
                    continue;
                devpressure_value += value;
                Segment_put(&segments->devpressure, (void *)&devpressure_value,
                            i, j);
            }
        }
    }
}

/*!
 * \brief Precompute development pressure matrix to speed up.
 * \param devpressure_info Development pressure parameters and matrix
 */
void initialize_devpressure_matrix(struct DevPressure *devpressure_info)
{
    int i, j;
    double dist;
    double value;

    devpressure_info->matrix =
        G_malloc(sizeof(float *) * (devpressure_info->neighborhood * 2 + 1));
    for (i = 0; i < devpressure_info->neighborhood * 2 + 1; i++)
        devpressure_info->matrix[i] =
            G_malloc(sizeof(float) * (devpressure_info->neighborhood * 2 + 1));
    /* this can be precomputed */
    for (i = 0; i < 2 * devpressure_info->neighborhood + 1; i++) {
        for (j = 0; j < 2 * devpressure_info->neighborhood + 1; j++) {
            dist = get_distance(i, j, devpressure_info->neighborhood,
                                devpressure_info->neighborhood);
            if (dist > devpressure_info->neighborhood)
                value = 0;
            else if (devpressure_info->alg == OCCURRENCE)
                value = 1;
            else if (devpressure_info->alg == GRAVITY)
                value = devpressure_info->scaling_factor /
                        pow(dist, devpressure_info->gamma);
            else
                value = devpressure_info->scaling_factor *
                        exp(-2 * dist / devpressure_info->gamma);
            devpressure_info->matrix[i][j] = value;
        }
    }
}
