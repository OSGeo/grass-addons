/*!
   \file flowline.c

   \brief Generates flowlines as vector lines

   (C) 2014 by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2).  Read the file COPYING that comes with GRASS
   for details.

   \author Anna Petrasova
*/
#include <grass/raster3d.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "r3flow_structs.h"
#include "integrate.h"
#include "flowline.h"
#include "voxel_traversal.h"

/*!
   \brief Computes flowline by integrating velocity field.

   \param region pointer to current 3D region
   \param seed starting seed (point)
   \param velocity_field pointer to array of 3 3D raster maps
   \param integration pointer to integration struct
   \param flowline_vec pointer to Map_info struct of flowline vector
   \param cats pointer to line_cats struct of flowline vector
   \param points pointer to line_pnts struct of flowline vector
   \param cat category of the newly created flow line
*/
void compute_flowline(RASTER3D_Region * region, const struct Seed *seed,
		      RASTER3D_Map ** velocity_field, RASTER3D_Map *flowacc,
		      struct Integration *integration,
		      struct Map_info *flowline_vec, struct line_cats *cats,
		      struct line_pnts *points, const int cat)
{
    int i, j, count;
    double delta_t;
    double velocity_norm;
    double point[3], new_point[3];
    double vel_x, vel_y, vel_z;
    double min_step, max_step;
    int col, row, depth;
    int last_col, last_row, last_depth;
    int coor_diff;
    FCELL value;
    int *trav_coords;
    int size, trav_count;

    point[0] = seed->x;
    point[1] = seed->y;
    point[2] = seed->z;

    last_col = last_row = last_depth = -1;

    size = 5;
    trav_coords = G_malloc(3 * size * sizeof(int));

    if (seed->flowline) {
	/* append first point */
	Vect_append_point(points, seed->x, seed->y, seed->z);
    }
    count = 1;
    while (count <= integration->limit) {
	if (get_velocity(region, velocity_field, point[0], point[1], point[2],
			 &vel_x, &vel_y, &vel_z) < 0)
	    break;		/* outside region */
	velocity_norm = norm(vel_x, vel_y, vel_z);

	if (velocity_norm <= VELOCITY_EPSILON)
	    break;		/* zero velocity means end of propagation */

	/* convert to time */
	delta_t = get_time_step(integration->unit, integration->step,
				velocity_norm, integration->cell_size);

	/* integrate */
	min_step = get_time_step("cell", MIN_STEP, velocity_norm,
				 integration->cell_size);
	max_step = get_time_step("cell", MAX_STEP, velocity_norm,
				 integration->cell_size);
	delta_t *= integration->direction;
	if (rk45_integrate_next
	    (region, velocity_field, point, new_point,
	     &delta_t, min_step, max_step) < 0)
	    break;

	if (seed->flowline)
	    Vect_append_point(points, new_point[0], new_point[1],
			      new_point[2]);
	if (seed->flowaccum) {
            Rast3d_location2coord(region, new_point[1], new_point[0], new_point[2],
                                  &col, &row, &depth);
            if (!(last_col == col && last_row == row && last_depth == depth)) {
                value = Rast3d_get_float(flowacc, col, row, depth);
                Rast3d_put_float(flowacc, col, row, depth, value + 1);
                if (last_col >= 0) {
                    coor_diff = (abs(last_col - col) + abs(last_row - row) +
                                 abs(last_depth - depth));
                    /* if not run for the 1. time and previous and next point coordinates
                    differ by more than 1 voxel coordinate */
                    if (coor_diff > 1) {
                        traverse(region, point, new_point, trav_coords, &size, &trav_count);
                        for (j = 0; j < trav_count; j++) {
                            value = Rast3d_get_float(flowacc, trav_coords[3 * j + 0],
                                                     trav_coords[3 * j + 1],
                                                     trav_coords[3 * j + 2]);
                            Rast3d_put_float(flowacc, trav_coords[3 * j + 0],
                                             trav_coords[3 * j + 1],
                                             trav_coords[3 * j + 2],
                                             value + 1);
                        }
                    }
                }
                last_col = col;
                last_row = row;
                last_depth = depth;
            }
        }
	for (i = 0; i < 3; i++) {
	    point[i] = new_point[i];
	}
	count++;

    }
    if (seed->flowline) {
        if (points->n_points > 1) {
            Vect_cat_set(cats, 1, cat);
            Vect_write_line(flowline_vec, GV_LINE, points, cats);
            G_debug(1, "Flowline ended after %d steps", count - 1);
        }
        Vect_reset_line(points);
        Vect_reset_cats(cats);
    }
}
