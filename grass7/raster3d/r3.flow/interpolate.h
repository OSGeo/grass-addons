#ifndef INTERPOLATE_H
#define INTERPOLATE_H

#include <grass/raster3d.h>

int interpolate_velocity(RASTER3D_Region *region, RASTER3D_Map **map,
			 const double north, const double east,
			 const double top, double *vel_x, double *vel_y,
			 double *vel_z);
#endif // INTERPOLATE_H
