/*!
  \file write_img.c
 
  \brief Save current GL screen to image file.
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  Based on visualization/nviz/src/anim_support.c

  \author Updated/modified by Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <grass/gsurf.h>
#include <grass/gstypes.h>

#include "local_proto.h"

/*!
  \brief Save current GL screen to an ppm file.

  \param name filename
*/

int write_ppm(const char *name)
{
    GS_write_ppm(name);
    
    return 1;
}
