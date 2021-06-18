/* File: proj_geo.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/gprojects.h>
#include "ps_info.h"
#include "local_proto.h"


/* From: r.proj */
void init_proj(struct pj_info *iproj, struct pj_info *oproj)
{
    struct Key_Value *out_proj_info, *out_unit_info;

    /* Get projection info for output mapset */
    if ((out_proj_info = G_get_projinfo()) == NULL)
	G_fatal_error(_("Unable to get projection info of output raster map"));

    if ((out_unit_info = G_get_projunits()) == NULL)
	G_fatal_error(_("Unable to get projection units of output raster map"));

    if (pj_get_kv(oproj, out_proj_info, out_unit_info) < 0)
	G_fatal_error(_("Unable to get projection key values of output raster map"));

    G_free_key_value(out_proj_info);
    G_free_key_value(out_unit_info);

    /* In Info */
    if (GPJ_get_equivalent_latlong(iproj, oproj) < 0)
	G_fatal_error(_("Unable to set up lat/long projection"));

    return;
}

/*
 *
 */
int find_limits(double *north, double *south,
		double *east, double *west, struct pj_info *ll_proj,
		struct pj_info *xy_proj)
{
    int x, y;
    double d, z;

    /* West */
    if (PS.map.west < 500000)
	G_plot_where_en(10. * PS.map_x, 10. * PS.map_top, west, &d);
    else
	G_plot_where_en(10. * PS.map_x, 10. * PS.map_y, west, &d);
    pj_do_proj(west, &d, xy_proj, ll_proj);	/* UTM > LL */

    /* East */
    if (PS.map.west < 500000)
	G_plot_where_en(10. * PS.map_right, 10. * PS.map_top, east, &d);
    else
	G_plot_where_en(10. * PS.map_right, 10. * PS.map_y, east, &d);
    pj_do_proj(east, &d, xy_proj, ll_proj);	/* UTM > LL */

    /* d previous */
    z = (6. * PS.map.zone - 183.);
    pj_do_proj(&z, &d, ll_proj, xy_proj);	/* LL > UTM */
    G_plot_where_xy(z, d, &x, &y);	/* UTM > XY */

    /* North */
    G_plot_where_en(x, 10. * PS.map_top, &d, north);	/* XY > UTM */
    pj_do_proj(&d, north, xy_proj, ll_proj);	/* UTM > LL */

    /* South */
    z = (double)x / 10.;
    if ((z - PS.map_x) > (PS.map_right - z))
	G_plot_where_en(10. * PS.map_x, 10. * PS.map_y, &d, south);	/* XY > UTM */
    else
	G_plot_where_en(10. * PS.map_right, 10. * PS.map_y, &d, south);	/* XY > UTM */
    pj_do_proj(&d, south, xy_proj, ll_proj);	/* UTM > LL */
}
