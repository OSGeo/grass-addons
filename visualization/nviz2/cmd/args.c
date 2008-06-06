/*!
  \file args.c
 
  \brief Parse command
  
  COPYRIGHT: (C) 2008 by the GRASS Development Team

  This program is free software under the GNU General Public
  License (>=v2). Read the file COPYING that comes with GRASS
  for details.

  \author Martin Landa <landa.martin gmail.com>

  \date 2008
*/

#include <stdlib.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"

/*!
   \brief Parse command

   \param argc number of arguments
   \param argv arguments array
   \param params GRASS parameters

   \return 1
*/
void parse_command(int argc, char* argv[], struct GParams *params)
{
    params->elev = G_define_standard_option(G_OPT_R_ELEV);
    params->elev->required = YES;
    params->elev->multiple = YES;
    params->elev->description = _("Name of raster map(s) for elevation");
    params->elev->guisection = _("Raster");

    params->exag = G_define_option();
    params->exag->key = "exag";
    params->exag->key_desc = "value";
    params->exag->type = TYPE_DOUBLE;
    params->exag->required = NO;
    params->exag->multiple = NO;
    params->exag->description = _("Vertical exaggeration");
    params->exag->answer = "1.0";
    params->exag->options = "0-10";

    params->pos = G_define_option();
    params->pos->key = "position";
    params->pos->key_desc = "x,y";
    params->pos->type = TYPE_DOUBLE;
    params->pos->required = NO;
    params->pos->multiple = NO;
    params->pos->description = _("Viewpoint position (x,y model coordinates)");
    params->pos->guisection = _("Viewpoint");
    params->pos->answer = "0.85,0.85";

    params->height = G_define_option();
    params->height->key = "height";
    params->height->key_desc = "value";
    params->height->type = TYPE_INTEGER;
    params->height->required = NO;
    params->height->multiple = NO;
    params->height->description = _("Viewpoint height (in map units)");
    params->height->guisection = _("Viewpoint");
    params->height->answer = "10561";

    params->persp = G_define_option();
    params->persp->key = "perspective";
    params->persp->key_desc = "value";
    params->persp->type = TYPE_INTEGER;
    params->persp->required = NO;
    params->persp->multiple = NO;
    params->persp->description = _("Viewpoint field of view (in degrees)");
    params->persp->guisection = _("Viewpoint");
    params->persp->answer = "40";
    params->persp->options = "0-100";

    params->twist = G_define_option();
    params->twist->key = "twist";
    params->twist->key_desc = "value";
    params->twist->type = TYPE_INTEGER;
    params->twist->required = NO;
    params->twist->multiple = NO;
    params->twist->description = _("Viewpoint twist angle (in degrees)");
    params->twist->guisection = _("Viewpoint");
    params->twist->answer = "0";
    params->twist->options = "-180-180";

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    return;
}
