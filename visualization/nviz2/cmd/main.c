/****************************************************************************
 *
 * MODULE:       nviz_cmd
 *               
 * AUTHOR(S):    Martin Landa <landa.martin gmail.com>
 *               
 * PURPOSE:      Experimental NVIZ CLI prototype
 *               Google SoC 2008
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
    unsigned int nelev, ncolor_map, ncolor_const, nvect;
    float vp_height; /* calculated viewpoint height */

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
    /* set background color */
    nv_data_set_bgcolor(&data, color_from_cmd(params->bgcolor->answer)); 

    /* load data */
    nelev = ncolor_map = ncolor_const = 0;

    i = 0;
    while(params->color_map->answer && params->color_map->answers[i++])
	ncolor_map++;

    i = 0;
    while(params->color_const->answer && params->color_const->answers[i++])
	ncolor_const++;

    /* load rasters */
    if (params->elev->answer) {
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

	    if (i < ncolor_map) { /* check for color map */
		mapset = G_find_cell2 (params->color_map->answers[i], "");
		if (mapset == NULL) {
		    G_fatal_error(_("Raster map <%s> not found"),
				  params->color_map->answers[i]);
		}

		set_attr(id, MAP_OBJ_SURF, ATT_COLOR, MAP_ATT,
			 G_fully_qualified_name(params->color_map->answers[i], mapset), -1.0,
			 &data);
	    }
	    else if (i < ncolor_const) { /* check for color value */
		set_attr(id, MAP_OBJ_SURF, ATT_COLOR, CONST_ATT,
			 NULL, color_from_cmd(params->color_const->answers[i]),
			 &data);
	    }
	    else { /* use by default elevation map for coloring */
		set_attr(id, MAP_OBJ_SURF, ATT_COLOR, MAP_ATT,
			 G_fully_qualified_name(params->elev->answers[i], mapset), -1.0,
			 &data);
	    }
	    
	    /*
	      if (i > 1)
	      set_default_wirecolors(data, i);
	    */
	    nelev++;
	}
    }

    /* load vectors */
    if (params->vector->answer) {
	if (!params->elev->answer && GS_num_surfs() == 0) { /* load base surface if no loaded */
	    int *surf_list, nsurf;

	    new_map_obj(MAP_OBJ_SURF, NULL, &data);

	    surf_list = GS_get_surf_list(&nsurf);
	    GS_set_att_const(surf_list[0], ATT_TRANSP, 255);
	}

	for (i = 0; params->vector->answers[i]; i++) {
	    mapset = G_find_vector2 (params->vector->answers[i], "");
	    if (mapset == NULL) {
		G_fatal_error(_("Vector map <%s> not found"),
			      params->vector->answers[i]);
	    }
	    new_map_obj(MAP_OBJ_VECT,
			G_fully_qualified_name(params->vector->answers[i], mapset), &data);
	}
	nvect++;
    }
	    
    /* init view */
    init_view();
    focus_set_map(MAP_OBJ_UNDEFINED, -1);

    /* set lights */
    /* TODO: add options */
    light_set_position(&data, 0,
		       0.68, -0.68, 0.80, 0.0);
    light_set_bright(&data, 0,
		     0.8);
    light_set_color(&data, 0,
		    1.0, 1.0, 1.0);
    light_set_ambient(&data, 0,
		      0.2, 0.2, 0.2);

    /*
    light_set_position(&data, 1,
		       0.68, -0.68, 0.80, 0.0);
    light_set_bright(&data, 1,
		     0.8);
    light_set_color(&data, 1,
		    1.0, 1.0, 1.0);
    light_set_ambient(&data, 1,
		      0.2, 0.2, 0.2);
    */

    light_set_position(&data, 1,
		       0.0, 0.0, 1.0, 0.0);
    light_set_bright(&data, 1,
		     0.5);
    light_set_color(&data, 1,
		    1.0, 1.0, 1.0);
    light_set_ambient(&data, 1,
		      0.3, 0.3, 0.3);
    
    /* define view point */
    if (params->height->answer) {
	vp_height = atof(params->height->answer);
    }
    else {
	exag_get_height(&vp_height, NULL, NULL);
    }
    viewpoint_set_height(&data,
			 vp_height);
    change_exag(&data,
		atof(params->exag->answer));
    viewpoint_set_position(&data,
			   atof(params->pos->answers[0]),
			   atof(params->pos->answers[1]));
    viewpoint_set_twist(&data,
			atoi(params->twist->answer));
    viewpoint_set_persp(&data,
			atoi(params->persp->answer));


    // resize_window(600, 480);

    GS_clear(data.bgcolor);

    /* draw */
    cplane_draw(&data, -1, -1);
    draw_all (&data);

    write_ppm("test.ppm"); /* TODO: option 'format' */

    render_window_destroy(&offscreen);

    G_free ((void *) params);

    exit(EXIT_SUCCESS);
}
