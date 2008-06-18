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

/*!
  \brief Initialize Nviz class
*/
Nviz::Nviz()
{
    GS_libinit();
    /* GVL_libinit(); TODO */

    //GS_set_swap_func(swap_gl);
}

/*!
  \brief Swap GL buffers
*/
void Nviz::swap_gl()
{
    return;
}
