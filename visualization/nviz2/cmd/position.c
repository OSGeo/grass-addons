/*!
  \file position.c
 
  \brief Position, focus settings
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/position.c

  \author Updated/modified by Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <grass/gsurf.h>
#include <grass/gstypes.h>
#include <grass/glocale.h>

#include "local_proto.h"

/*!
  Initialize view and position settings (focus)

  Set position to center of view
*/
void init_view()
{
    GS_init_view();
    focus_set_state(1); /* center of view */

    return;
}

/*!
  \brief Set focus state

  \param state_flag 1 for center view, 0 use viewdir

  \return 1 on success
  \return 0 on failure
*/
int focus_set_state(int state_flag)
{
    if (state_flag == 1)
	GS_set_infocus(); /* return center of view */
    else if (state_flag == 0)
	GS_set_nofocus(); /* no center of view -- use viewdir */
    else {
	G_warning (_("Unable to set focus"));
	return 0;
    }
    
    return 1;
}

/*!
  \brief Set focus based on loaded map

  If <i>map</i> is MAP_OBJ_UNDEFINED, set focus from first
  surface/volume in the list.

  \param type map object type
  \param id map object id

  \return 0 on no focus
  \return id id of map object used for setting focus
*/
int focus_set_map(int type, int id)
{
    if (GS_num_surfs() < 0 && GVL_num_vols() < 0) {
	GS_set_nofocus();
	return 0;
    }

    if (type == MAP_OBJ_UNDEFINED) {
	int *surf_list, num_surfs, *vol_list;

	if (GS_num_surfs() > 0) {
	    surf_list = GS_get_surf_list(&num_surfs);
	    id = surf_list[0];
	    G_free (surf_list);
	    
	    GS_set_focus_center_map(id);
	}

	if (GVL_num_vols() > 0) {
	    vol_list = GVL_get_vol_list(&num_surfs);
	    id = vol_list[0];
	    G_free (vol_list);
	    
	    GVL_set_focus_center_map(id);
	}
	return id;
    }

    if (type == MAP_OBJ_SURF) {
	GS_set_focus_center_map(id);
    }
    else if (type == MAP_OBJ_VOL) {
	GVL_set_focus_center_map(id);
    }
    
    return id;
}
