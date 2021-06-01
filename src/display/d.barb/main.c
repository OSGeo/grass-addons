/*
 * MODULE:      d.barb
 *
 * PURPOSE:     Draws wind barbs based on data from raster maps or a vector
 *              points map with data stored as attributes in database column
 *
 * AUTHORS:     Hamish Bowman, Dunedin, New Zealand
 *              Grid code derived from d.rast.arrow
 *
 * COPYRIGHT:   (c) 2008-2014 by Hamish Bowman, and The GRASS Development Team
 *              This program is free software under the GNU General Public
 *              License (>=v2). Read the file COPYING that comes with GRASS
 *              for details.
 */

//#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/display.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"


int main(int argc, char *argv[])
{

    struct GModule *module;

    struct Option *dir_opt, *magn_opt, *u_opt, *v_opt,
	*color_opt, *type_opt, *skip_opt, *scale_opt,
	*vinput_opt, *vlayer_opt, *style_opt, *keyat_opt,
	*keyvelo_opt, *keyfont_opt, *peak_opt;
    struct Flag *from_to;

    int color, aspect_type, skip, vlayer, style;
    int is_vector, is_component;	/* boolean */
    double scale, peak, key_fontsize;
    char dir_u_map[GNAME_MAX], mag_v_map[GNAME_MAX];
    int i, num_leg_at, num_leg_velo;


    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("");
    module->description = _("Draws flow barbs.");

    dir_opt = G_define_standard_option(G_OPT_R_INPUT);
    dir_opt->key = "direction";
    dir_opt->description =
	_("Raster map (or attribute column) containing velocity direction");
    dir_opt->required = NO;
    dir_opt->guisection = _("Input");

    magn_opt = G_define_standard_option(G_OPT_R_INPUT);
    magn_opt->key = "magnitude";
    magn_opt->description =
	_("Raster map (or attribute column) containing velocity magnitude");
    magn_opt->required = NO;
    magn_opt->guisection = _("Input");

    u_opt = G_define_standard_option(G_OPT_R_INPUT);
    u_opt->key = "u";
    u_opt->description =
	_("Raster map (or attribute column) containing u-component of velocity");
    u_opt->required = NO;
    u_opt->guisection = _("Input");

    v_opt = G_define_standard_option(G_OPT_R_INPUT);
    v_opt->key = "v";
    v_opt->description =
	_("Raster map (or attribute column) containing v-component of velocity");
    v_opt->required = NO;
    v_opt->guisection = _("Input");

    vinput_opt = G_define_standard_option(G_OPT_V_INPUT);
    vinput_opt->required = NO;
    vinput_opt->guisection = _("Input");

    vlayer_opt = G_define_standard_option(G_OPT_V_FIELD);
    vlayer_opt->guisection = _("Input");

    style_opt = G_define_option();
    style_opt->key = "style";
    style_opt->type = TYPE_STRING;
    style_opt->answer = "arrow";
    style_opt->options = "arrow,barb,small_barb,straw";
    style_opt->description = _("Style");

    color_opt = G_define_standard_option(G_OPT_C_FG);

    skip_opt = G_define_option();
    skip_opt->key = "skip";
    skip_opt->type = TYPE_INTEGER;
    skip_opt->required = NO;
    skip_opt->answer = "10";
    skip_opt->description = _("Draw arrow every Nth grid cell");
    skip_opt->guisection = _("Raster");

    scale_opt = G_define_option();
    scale_opt->key = "scale";
    scale_opt->type = TYPE_DOUBLE;
    scale_opt->required = NO;
    scale_opt->answer = "1.0";
    scale_opt->description = _("Scale factor for arrow rendering");

    peak_opt = G_define_option();
    peak_opt->key = "peak";
    peak_opt->type = TYPE_DOUBLE;
    peak_opt->required = NO;
    peak_opt->description =
	_("Maximum value for scaling (overrides map's maximum)");

    type_opt = G_define_option();
    type_opt->key = "aspect_type";
    type_opt->type = TYPE_STRING;
    type_opt->required = NO;
    type_opt->answer = "cartesian";
    type_opt->options = "cartesian,compass";
    type_opt->description = _("Direction map aspect type");


    /* legend  draw vertical (N facing) barb and exit */
    keyat_opt = G_define_option();
    keyat_opt->key = "legend_at";
    keyat_opt->key_desc = "x,y";
    keyat_opt->type = TYPE_DOUBLE;
    keyat_opt->answer = "10.0,10.0";
    keyat_opt->options = "0-100";
    keyat_opt->required = NO;
    keyat_opt->multiple = YES;
    keyat_opt->label =
	_("Screen percentage for legend barb ([0,0] is bottom-left)");
    keyat_opt->description = _("Draws a single barb and exits");
    keyat_opt->guisection = _("Legend");

    keyvelo_opt = G_define_option();
    keyvelo_opt->key = "legend_velo";
    keyvelo_opt->type = TYPE_DOUBLE;
    keyvelo_opt->required = NO;
    keyvelo_opt->multiple = YES;
    keyvelo_opt->description = _("Velocity for legend key arrow");
    keyvelo_opt->guisection = _("Legend");

    keyfont_opt = G_define_option();
    keyfont_opt->key = "legend_fontsize";
    keyfont_opt->type = TYPE_DOUBLE;
    keyfont_opt->answer = "14";
    keyfont_opt->description = _("Font size used in legend");
    keyfont_opt->guisection = _("Legend");

    /* TODO */
    from_to = G_define_flag();
    from_to->key = 'r';
    from_to->label = _("Rotate direction 180 degrees");
    from_to->description =
	_("Useful for switching between atmospheric and oceanographic conventions");


    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    G_warning("This module is still a work in progress.");

    /* check parms */
    if ((u_opt->answer && (dir_opt->answer || magn_opt->answer)) ||
	(v_opt->answer && (dir_opt->answer || magn_opt->answer)))
	G_fatal_error(_("Specify either direction and magnitude or u and v components"));

    if (!(!(dir_opt->answer && magn_opt->answer) ||
	  !(u_opt->answer && v_opt->answer)))
	G_fatal_error(_("Specify either direction and magnitude or u and v components"));

    if (u_opt->answer && v_opt->answer) {
	is_component = TRUE;
	strncpy(dir_u_map, u_opt->answer, sizeof(dir_u_map) - 1);
	strncpy(mag_v_map, v_opt->answer, sizeof(mag_v_map) - 1);
    }
    else if (dir_opt->answer && magn_opt->answer) {
	is_component = FALSE;
	strncpy(dir_u_map, dir_opt->answer, sizeof(dir_u_map) - 1);
	strncpy(mag_v_map, magn_opt->answer, sizeof(mag_v_map) - 1);
    }
    dir_u_map[sizeof(dir_u_map) - 1] = '\0';	/* strncpy() doesn't null-terminate on overflow */
    mag_v_map[sizeof(mag_v_map) - 1] = '\0';

    if (vinput_opt->answer)
	is_vector = TRUE;
    else
	is_vector = FALSE;

    scale = atof(scale_opt->answer);
    skip = atoi(skip_opt->answer);
    vlayer = atoi(vlayer_opt->answer);
    if (peak_opt->answer)
	peak = atof(peak_opt->answer);
    else
	peak = 0./0.; /* NaN */

    if (strcmp(type_opt->answer, "compass") == 0)
	aspect_type = TYPE_COMPASS;
    else
	aspect_type = TYPE_GRASS;

    if (G_strcasecmp(style_opt->answer, "arrow") == 0)
	style = TYPE_ARROW;
    else if (G_strcasecmp(style_opt->answer, "barb") == 0)
	style = TYPE_BARB;
    else if (G_strcasecmp(style_opt->answer, "small_barb") == 0)
	style = TYPE_SMLBARB;
    else if (G_strcasecmp(style_opt->answer, "straw") == 0)
	style = TYPE_STRAW;
    else
	G_fatal_error("Invalid style: %s", style_opt->answer);


    if (keyvelo_opt->answer) {
	/* Coords from Command Line */
	/* Test for number coordinate pairs */
	for (i = 0; keyat_opt->answers[i]; i += 2)
	    num_leg_at = i + 2;

	for (i = 0, num_leg_velo = 0; keyvelo_opt->answers[i]; i++)
	    num_leg_velo++;

	if (num_leg_at != num_leg_velo * 2)
	    G_fatal_error(
	       _("Unequal number of legend placement and velocity requests (%d vs. %d)"),
			  num_leg_at, num_leg_velo);

	key_fontsize = atof(keyfont_opt->answer);
    }

    if (R_open_driver() != 0)
	G_fatal_error(_("No graphics device selected"));

    /* Parse and select foreground color */
    color = D_parse_color(color_opt->answer, 0);


    // is D_setup() actually needed?
    D_setup(0);

    if (keyvelo_opt->answer) {

	do_legend(keyat_opt->answers, keyvelo_opt->answers, num_leg_velo,
		  key_fontsize, style, scale, peak, color);

	D_add_to_list(G_recreate_command());
	R_close_driver();
	exit(EXIT_SUCCESS);
    }

    if (is_vector)
	do_barb_points(vinput_opt->answer, vlayer,
		       dir_u_map, mag_v_map, is_component, color,
		       aspect_type, scale, peak, style, from_to->answer);
    else
	do_barb_grid(dir_u_map, mag_v_map, is_component, color,
		     aspect_type, scale, peak, skip, style, from_to->answer);


    D_add_to_list(G_recreate_command());
    R_close_driver();
    exit(EXIT_SUCCESS);
}
