/*!
  \file nviz.c
 
  \brief Nviz library -- Data management
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/

  \author Updated/modified by Martin Landa <landa.martin gmail.com> (Google SoC 2008)

  \date 2008
*/

#include <grass/nviz.h>

/*!
  \brief Initialize Nviz data

  \param data nviz data
*/
void Nviz_init_data(nv_data *data)
{
    unsigned int i;

    /* data range */
    data->zrange = 0;
    data->xyrange = 0;
    
    /* clip planes, turn off by default*/
    data->num_cplanes = 0;
    data->cur_cplane = 0;
    for (i = 0; i < MAX_CPLANES; i++) {
	Nviz_new_cplane(data, i);
	Nviz_off_cplane(data, i);
    }
    
    /* lights */
    for (i = 0; i < MAX_LIGHTS; i++) {
	Nviz_new_light(data);
    }

    return;
}

/*!
  \brief Set background color

  \param data nviz data
  \param color color value
*/
void Nviz_set_bgcolor(nv_data *data, int color)
{
    data->bgcolor = color;
    
    return;
}
