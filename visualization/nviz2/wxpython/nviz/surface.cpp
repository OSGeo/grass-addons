/**
   \file map_obj.cpp
   
   \brief Experimental C++ wxWidgets Nviz prototype -- map object management

   Used by wxGUI Nviz extension.

   Copyright: (C) by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.

   \author Martin Landa <landa.martin gmail.com> (Google SoC 2008)

   \date 2008
*/

#include "nviz.h"

void Nviz::SetSurfaceColor(int id, bool map, const char *value)
{
    if (map) {
	Nviz_set_attr(id, MAP_OBJ_SURF, ATT_COLOR, MAP_ATT,
		      value, -1.0,
		      data);
    }
    else {
	float val;
	val = atof(value);
	Nviz_set_attr(id, MAP_OBJ_SURF, ATT_COLOR, CONST_ATT,
		      NULL, val,
		      data);
    }
	
    G_debug(1, "Nviz::SetSurfaceColor(): id=%d, map=%d, value=%s",
	    id, map, value);

    return;
}
