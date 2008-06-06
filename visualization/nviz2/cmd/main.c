/****************************************************************************
 *
 * MODULE:       nviz_cmd
 *               
 * AUTHOR(S):    Martin Landa <landa.martin gmail.com>
 *               
 * PURPOSE:      Experimental NVIZ CLI prototype
 *               
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gsurf.h>
#include <grass/gstypes.h>

#include "local_proto.h"

int main (int argc, char *argv[])
{
    struct GModule *module;
    struct GParams *params;

    char *mapset;
    unsigned int i;
    int id;

    nv_data data;
    render_window offscreen;

    /* initialize GRASS */
    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("visualization, raster, vector");
    module->description = _("Experimental NVIZ CLI prototype.");

    params = (struct GParams*) G_malloc(sizeof (struct GParams));

    /* define options, call G_parser() */
    parse_command(argc, argv, params);

    GS_libinit();
    /* GVL_libinit(); TODO */

    GS_set_swap_func(swap_gl);

    /* define render window */
    render_window_init(&offscreen);
    render_window_create(&offscreen, 640, 480); /* TOD0: option dim */
    render_window_make_current(&offscreen);

    /* initialize nviz data */
    nv_data_init(&data);
    /* define default attributes for map objects */
    set_att_default();

    /* load data */
    if (params->elev->answers) {
	for (i = 0; params->elev->answers[i]; i++) {
	    mapset = G_find_cell2 (params->elev->answers[i], "");
	    if (mapset == NULL) {
		G_fatal_error(_("Raster map <%s> not found"),
			      params->elev->answers[i]);
	    }
	    
	    /* topography */
	    id = new_map_obj(MAP_OBJ_SURF,
			     G_fully_qualified_name(params->elev->answers[i], mapset),
			     &data);

	    /* color TODO: option */
	    set_attr(id, MAP_OBJ_SURF, ATT_COLOR, MAP_ATT,
		     G_fully_qualified_name(params->elev->answers[i], mapset),
		     &data);

	    /*
	      if (i > 1)
	      set_default_wirecolors(data, i);
	    */
	}
    }

    /* define view point */
    GS_init_view();
    viewpoint_set_height(&data,
			 atof(params->height->answer));
    viewpoint_set_position(&data,
			   atof(params->pos->answers[0]),
			   atof(params->pos->answers[1]));
    viewpoint_set_twist(&data,
			atoi(params->twist->answer));
    viewpoint_set_persp(&data,
			atoi(params->persp->answer));


    /* resize_window(400, 400); */

    /*
    light_set_position(&data, 0,
		       0.68, -0.68, 0.80, 0.0);
    light_set_position(&data, 1,
		       0.68, -0.68, 0.80, 0.0);
    light_set_position(&data, 2,
		       0.0, 0.0, 1.0, 0.0);
    light_set_bright(&data, 0,
		     0.8);
    light_set_bright(&data, 1,
		     0.8);
    light_set_bright(&data, 2,
		     0.5);
    light_set_color(&data, 0,
		    1.0, 1.0, 1.0);
    light_set_color(&data, 1,
		    1.0, 1.0, 1.0);
    light_set_color(&data, 2,
		    1.0, 1.0, 1.0);
    light_set_ambient(&data, 0,
		      0.2, 0.2, 0.2);
    light_set_ambient(&data, 1,
		      0.2, 0.2, 0.2);
    light_set_ambient(&data, 2,
		      0.3, 0.3, 0.3);
    */


    GS_clear(data.bgcolor);

    cplane_draw(&data, -1, -1);
    draw_all (&data);

    write_ppm("test.ppm");

    render_window_destroy(&offscreen);

    G_free ((void *) params);

    exit(EXIT_SUCCESS);
}
