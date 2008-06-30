/*!
  \file draw.cpp
 
  \brief Experimental C++ wxWidgets Nviz prototype -- Draw map objects to GLX context
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/draw.c and
  visualization/nviz/src/togl_flythrough.c

  \author Updated/modified by Martin Landa <landa.martin gmail.com> (Google SoC 2008)

  \date 2008
*/

#include "nviz.h"

/*!
  \brief Draw map

  \param quick true for quick rendering
*/
void Nviz::Draw(bool quick)
{
    GS_clear(data->bgcolor);
    
    Nviz_draw_cplane(data, -1, -1);

    if (data->draw_coarse) { /* coarse */
	GS_set_draw(GSD_BACK);
	GS_ready_draw();
	GS_alldraw_wire();
	GS_done_draw();

	G_debug(1, "Nviz::Draw(): mode=coarse");
    }
    else { /* fine / both */
	if (!quick)
	    Nviz_draw_all (data);
	else
	    Nviz_draw_quick(data); // ?

	G_debug(1, "Nviz::Draw(): mode=fine, quick=%d", quick);
    }

    return;
}

/*!
  \brief Erase map display (with background color)
*/
void Nviz::EraseMap()
{
    GS_clear(data->bgcolor);

    G_debug(1, "Nviz::EraseMap()");

    return;
}

/*!
  \brief Set draw mode

  Draw modes:
   - DRAW_COARSE
   - DRAW_FINE
   - DRAW_BOTH

  \param mode draw mode
*/
void Nviz::SetDrawMode(int mode)
{
    Nviz_set_draw_mode(data, mode);

    G_debug(1, "Nviz::SetDrawMode(): mode=%d",
	    mode);
    return;
}
