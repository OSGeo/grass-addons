/**
   \file init.cpp
   
   \brief Experimental C++ wxWidgets Nviz prototype -- initialization

   Used by wxGUI Nviz extension.

   Copyright: (C) by the GRASS Development Team

   This program is free software under the GNU General Public
   License (>=v2). Read the file COPYING that comes with GRASS
   for details.

   \author Martin Landa <landa.martin gmail.com> (Google SoC 2008)

   \date 2008
*/

#include "nviz.h"

static void swap_gl();

/*!
  \brief Initialize Nviz class instance
*/
Nviz::Nviz()
{
    G_gisinit(""); /* GRASS functions */

    GS_libinit();
    /* GVL_libinit(); TODO */

    GS_set_swap_func(swap_gl);

    /* initialize render window */
    rwind = Nviz_new_render_window();
    Nviz_init_render_window(rwind);
}

/*!
  \brief Destroy Nviz class instance
*/
Nviz::~Nviz()
{
    Nviz_destroy_render_window(rwind);

    G_free((void *) rwind);
}

/*!
  \brief Swap GL buffers
*/
void swap_gl()
{
    return;
}

/*!
  \brief Associate display with render window

  \return 1 on success
  \return 0 on failure
*/
int Nviz::SetDisplay(void *display, int width, int height)
{
    if (!rwind)
	return 0;

    Nviz_create_render_window(rwind, display, width, height);
    Nviz_make_current_render_window(rwind);

    return 1;
}
