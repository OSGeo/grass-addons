/**
   \file change_view.cpp
   
   \brief Experimental C++ wxWidgets Nviz prototype -- Change viewport

   Used by wxGUI Nviz extension.

   Copyright: (C) by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.

   \author Martin Landa <landa.martin gmail.com> (Google SoC 2008)

   \date 2008
*/

#include "nviz.h"

/*!
  \brief GL canvas resized

  \param width window width
  \param height window height

  \return 1 on success
  \return 0 on failure (window resized by dafault to 20x20 px)
 */
int Nviz::ResizeWindow(int width, int height)
{
    return Nviz_resize_window(width, height);
}

void Nviz::SetViewportDefault()
{
    float vp_height;
    /* determine height */
    Nviz_get_exag_height(&vp_height, NULL, NULL);

    Nviz_set_viewpoint_height(data,
			      vp_height);
    Nviz_change_exag(data,
		     1.0);
    Nviz_set_viewpoint_position(data,
				0.85, 0.85);
    Nviz_set_viewpoint_twist(data,
			     0.0);
    Nviz_set_viewpoint_persp(data,
			     40);

    return;
}
