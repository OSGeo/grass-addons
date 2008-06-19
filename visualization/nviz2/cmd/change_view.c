/*!
  \file change_view.c
 
  \brief Change view settings
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/change_view.c

  \author Updated/modified by Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <stdlib.h>

#include <grass/gsurf.h>
#include <grass/gstypes.h>

#include "local_proto.h"

/*!
  \brief Update ranges

  Call whenever a new surface is added, deleted, or exag changes

  \return 1
*/
int update_ranges(nv_data *dc)
{
    float zmin, zmax, exag;

    GS_get_longdim(&(dc->xyrange));

    dc->zrange = 0.;

    /* Zrange is based on a minimum of Longdim */
    if (GS_global_exag()) {
	exag = GS_global_exag();
	dc->zrange = dc->xyrange / exag;
    }
    else {
	exag = 1.0;
    }

    GS_get_zrange_nz(&zmin, &zmax);	/* actual */

    zmax = zmin + (3. * dc->xyrange / exag);
    zmin = zmin - (2. * dc->xyrange / exag);

    if ((zmax - zmin) > dc->zrange)
	dc->zrange = zmax - zmin;

    return 1;
}

/*!
  \brief Change position of view

  \param data nviz data
  \param x_pos,y_pos x,y position (model coordinates)

  \return 1
*/
int viewpoint_set_position(nv_data *data,
			   float x_pos, float y_pos)
{
    float xpos, ypos, from[3];
    float tempx, tempy;
    
    xpos = x_pos;
    xpos = (xpos < 0) ? 0 : (xpos > 1.0) ? 1.0 : xpos;
    ypos = 1.0 - y_pos;
    ypos = (ypos < 0) ? 0 : (ypos > 1.0) ? 1.0 : ypos;

    GS_get_from(from);
    
    tempx = xpos * RANGE - RANGE_OFFSET;
    tempy = ypos * RANGE - RANGE_OFFSET;

    if ((from[X] != tempx) || (from[Y] != tempy)) {

	from[X] = tempx;
	from[Y] = tempy;

	GS_moveto(from);

	draw_quick(data);
    }

    return 1;
}

/*!
  \brief Change viewpoint height

  \param data nviz data
  \param height height value (world coordinates)

  \return 1
*/
int viewpoint_set_height(nv_data *data, float height)
{
    float from[3];

    GS_get_from_real(from);

    if (height != from[Z]) {
	from[Z] = height;

	GS_moveto_real(from);

	/*
	   normalize (from);
	   GS_setlight_position(1, from[X], from[Y], from[Z], 0);
	*/

	draw_quick(data);
    }

    return 1;
}

/*!
  \brief Change viewpoint perspective (field of view)

  \param data nviz data
  \param persp perspective value (0-100, in degrees)

  \return 1
*/
int viewpoint_set_persp(nv_data *data, int persp)
{
    int fov;

    fov = (int) (10 * persp);
    GS_set_fov(fov);

    draw_quick(data);

    return 1;
}

/*!
  \brief Change viewpoint twist

  \param data nviz data
  \param persp twist value (-180-180, in degrees)

  \return 1
*/
int viewpoint_set_twist(nv_data *data, int twist)
{
    GS_set_twist(10 * twist);
    
    draw_quick(data);

    return 1;
}

/*!
  \brief Change z-exag value

  \param data nviz data
  \param exag exag value

  \return 1
*/
int change_exag(nv_data *data, float exag)
{
    float temp;

    temp = GS_global_exag();

    if (exag != temp) {
	GS_set_global_exag(exag);
	update_ranges(data);
	
	draw_quick(data);
    }

    return 1;
}
