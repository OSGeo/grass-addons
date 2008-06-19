/*!
  \file change_view.c
 
  \brief Change view settings
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/change_view.c

  \author Updated/modified by Martin Landa <landa.martin gmail.com> (Google SoC 2008)

  \date 2008
*/

#include <grass/nviz.h>

/*!
  \brief GL canvas resized

  \param width window width
  \param height window height

  \return 1 on success
  \return 0 on failure (window resized by dafault to 20x20 px)
 */
int Nviz_resize_window(int width, int height)
{
    int ret;

    ret = 1;

    if (width < 1 || height < 1) {
	width = 20;
	height = 20;
	ret = 0;
    }

    GS_set_viewport(0, width, 0, height);

    /*   GS_clear(0x0000FF); causes red flash - debug only */
    GS_set_draw(GSD_BACK);
    GS_ready_draw();
    GS_alldraw_wire();
    GS_done_draw();

    return ret;
}
