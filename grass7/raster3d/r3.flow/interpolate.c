/*!
   \file interpolate.c

   \brief Trilinear interpolation

   (C) 2014 by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2).  Read the file COPYING that comes with GRASS
   for details.

   \author Anna Petrasova
 */

#include <grass/raster3d.h>

/*!
   \brief Finds 8 nearest voxels from a point.

   \param region pointer to current 3D region
   \param north,east,top geographic coordinates
   \param[out] x,y,z pointer to indices of neighbouring voxels
 */
static void find_nearest_voxels(RASTER3D_Region * region,
				const double north, const double east,
				const double top, int *x, int *y, int *z)
{
    double n_minus, e_minus, t_minus;
    double n_plus, e_plus, t_plus;

    n_minus = north - region->ns_res / 2;
    n_plus = north + region->ns_res / 2;
    e_minus = east - region->ew_res / 2;
    e_plus = east + region->ew_res / 2;
    t_minus = top - region->tb_res / 2;
    t_plus = top + region->tb_res / 2;

    Rast3d_location2coord(region, n_minus, e_minus, t_minus, x++, y++, z++);
    Rast3d_location2coord(region, n_minus, e_plus, t_minus, x++, y++, z++);
    Rast3d_location2coord(region, n_plus, e_minus, t_minus, x++, y++, z++);
    Rast3d_location2coord(region, n_plus, e_plus, t_minus, x++, y++, z++);
    Rast3d_location2coord(region, n_minus, e_minus, t_plus, x++, y++, z++);
    Rast3d_location2coord(region, n_minus, e_plus, t_plus, x++, y++, z++);
    Rast3d_location2coord(region, n_plus, e_minus, t_plus, x++, y++, z++);
    Rast3d_location2coord(region, n_plus, e_plus, t_plus, x, y, z);
}

/*!
   \brief Trilinear interpolation

   Computation is based on the sum of values of nearest voxels
   weighted by the relative distance of a point
   to the center of the nearest voxels.

   \param array_values pointer to values of 8 (neigboring) voxels
   \param x,y,z relative coordinates (0 - 1)
   \param[out] interpolated pointer to the array (of size 3) of interpolated values
 */
static void trilinear_interpolation(const double *array_values,
				    const double x, const double y,
				    const double z, double *interpolated)
{
    int i, j;
    double rx, ry, rz, value;
    double weights[8];

    rx = 1 - x;
    ry = 1 - y;
    rz = 1 - z;
    weights[0] = rx * ry * rz;
    weights[1] = x * ry * rz;
    weights[2] = rx * y * rz;
    weights[3] = x * y * rz;
    weights[4] = rx * ry * z;
    weights[5] = x * ry * z;
    weights[6] = rx * y * z;
    weights[7] = x * y * z;


    /* weighted sum of surrounding values */
    for (i = 0; i < 3; i++) {
	value = 0;
	for (j = 0; j < 8; j++) {
	    value += weights[j] * array_values[i * 8 + j];
	}
	interpolated[i] = value;
    }
}

/*!
   \brief Converts geographic to relative coordinates

   Converts geographic to relative coordinates
   which are needed for trilinear interpolation.


   \param region pointer to current 3D region
   \param north,east,top geographic coordinates
   \param[out] x,y,z pointer to relative coordinates (0 - 1)
 */
static void get_relative_coords_for_interp(RASTER3D_Region * region,
					   const double north,
					   const double east,
					   const double top, double *x,
					   double *y, double *z)
{
    int col, row, depth;
    double temp;

    Rast3d_location2coord(region, north, east, top, &col, &row, &depth);

    /* x */
    temp = east - region->west - col * region->ew_res;
    *x = (temp > region->ew_res / 2 ?
	  temp - region->ew_res / 2 : temp + region->ew_res / 2)
	/ region->ew_res;
    /* y */
    temp = north - region->south - (region->rows - row - 1) * region->ns_res;
    *y = (temp > region->ns_res / 2 ?
	  temp - region->ns_res / 2 : temp + region->ns_res / 2)
	/ region->ns_res;
    /* z */
    temp = top - region->bottom - depth * region->tb_res;
    *z = (temp > region->tb_res / 2 ?
	  temp - region->tb_res / 2 : temp + region->tb_res / 2)
	/ region->tb_res;
}

/*!
   \brief Interpolates velocity at a given point.

   \param region pointer to current 3D region
   \param map pointer to array of 3 3D raster maps (velocity field)
   \param north,east,top geographic coordinates
   \param[out] vel_x,vel_y,vel_z interpolated velocity

   \return 0 success
   \return -1 out of region
 */
int interpolate_velocity(RASTER3D_Region * region, RASTER3D_Map ** map,
			 const double north, const double east,
			 const double top, double *vel_x, double *vel_y,
			 double *vel_z)
{
    int i, j;
    double values[24];		/* 3 x 8, 3 dimensions, 8 neighbors */
    double value;
    double interpolated[3];
    int x[8], y[8], z[8];
    double rel_x, rel_y, rel_z;
    int type;

    /* check if we are out of region, any array should work */
    if (!Rast3d_is_valid_location(region, north, east, top))
	return -1;

    find_nearest_voxels(region, north, east, top, x, y, z);
    /* get values of the nearest cells */
    for (i = 0; i < 3; i++) {
	type = Rast3d_tile_type_map(map[i]);
	for (j = 0; j < 8; j++) {

	    Rast3d_get_value_region(map[i], x[j], y[j], z[j], &value, type);
	    if (Rast_is_null_value(&value, type))
		values[i * 8 + j] = 0;
	    else
		values[i * 8 + j] = value;
	}
    }

    /* compute weights */
    get_relative_coords_for_interp(region, north, east, top,
                                   &rel_x, &rel_y, &rel_z);

    trilinear_interpolation(values, rel_x, rel_y, rel_z, interpolated);
    *vel_x = interpolated[0];
    *vel_y = interpolated[1];
    *vel_z = interpolated[2];

    return 0;
}
