/*!
  \file nviz.c
 
  \brief Nviz subroutines
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/

  \author Updated/modified by Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <grass/gsurf.h>
#include <grass/gstypes.h>

#include "local_proto.h"

void nv_data_init(nv_data *data)
{
    unsigned int i;

    /* data range */
    data->zrange = 0;
    data->xyrange = 0;
    
    /* clip planes, turn off by default*/
    data->num_cplanes = 0;
    data->cur_cplane = 0;
    for (i = 0; i < MAX_CPLANES; i++) {
	cplane_new(data, i);
	cplane_off(data, i);
    }
    
    data->bgcolor = 16777215; /* TODO: option bgcolor */

    /* lights */
    for (i = 0; i < MAX_LIGHTS; i++) {
	light_new(data);
    }

    return;
}
