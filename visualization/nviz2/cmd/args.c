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
    /* raster */
    params->elev = G_define_standard_option(G_OPT_R_ELEV);
    params->elev->required = NO;
    params->elev->multiple = YES;
    params->elev->description = _("Name of raster map(s) for elevation");
    params->elev->guisection = _("Raster");

    params->color_map = G_define_standard_option(G_OPT_R_MAP);
    params->color_map->multiple = YES;
    params->color_map->required = NO;
    params->color_map->description = _("Name of raster map(s) for color");
    params->color_map->guisection = _("Raster");
    params->color_map->key = "color_map";

    params->color_const = G_define_standard_option(G_OPT_C_FG);
    params->color_const->multiple = YES;
    params->color_const->label = _("Color value");
    params->color_const->guisection = _("Raster");
    params->color_const->key = "color_value";
    params->color_const->answer = NULL;

    /* vector */
    params->vector = G_define_standard_option(G_OPT_V_MAP);
    params->vector->multiple = YES;
    params->vector->required = NO;
    params->vector->description = _("Name of vector overlay map(s)");
    params->vector->guisection = _("Vector");
    params->vector->key = "vector";

    /* misc */
    params->exag = G_define_option();
    params->exag->key = "zexag";
    params->exag->key_desc = "value";
    params->exag->type = TYPE_DOUBLE;
    params->exag->required = NO;
    params->exag->multiple = NO;
    params->exag->description = _("Vertical exaggeration");
    params->exag->answer = "1.0";
    params->exag->options = "0-10";

    params->bgcolor = G_define_standard_option(G_OPT_C_BG);

    /* viewpoint */
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

/*!
  \brief Get color value from color string (name or RGB triplet)

  \param color_str color string

  \return color value
*/
int color_from_cmd(const char *color_str)
{
    int red, grn, blu;

    if (G_str_to_color(color_str, &red, &grn, &blu) != 1) {
	G_warning (_("Invalid color (%s), using \"white\" as default"),
		   color_str);
	red = grn = blu = 255;
    }

    return (red & RED_MASK) + ((int)((grn) << 8) & GRN_MASK) + ((int)((blu) << 16) & BLU_MASK);
}
