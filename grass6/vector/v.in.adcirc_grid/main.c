/*
 * MODULE:      v.in.adcirc_grid
 *
 * PURPOSE:     Loads ADCIRC fort.14 triangular mesh into a GRASS vector
 *
 * AUTHORS:     Hamish Bowman, Dunedin, New Zealand
 *              Adapted from v.in.ascii (USA CERL)
 *
 * COPYRIGHT:   (c) 2014 by Hamish Bowman, and The GRASS Development Team
 *              This program is free software under the GNU General Public
 *              License (>=v2). Read the file COPYING that comes with GRASS
 *              for details.
 *
 * Format spec:
 *   http://adcirc.org/home/documentation/users-manual-v50/input-file-descriptions/adcirc-grid-and-boundary-information-file-fort-14/
 */

/* TODO: when writing nodes as 3D points, store attrs for is_edge,is_land nodes */
/* TODO: option to write out the trianges as 3D faces and kernels */
/* TODO: on the fly reprojection for non-LL locations (see r.in.lidar) */

#include <stdio.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>

#define BUFFSIZE 12800

int get_index(int *, int, int);

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *infile, *outmap;
    struct Flag *points_flag;

    FILE *ascii;
    struct Map_info Map;
    struct Cell_head window;
    int zcoor, type;
    char buff[BUFFSIZE];
    int *node_array;
    int *node;
    double *xarray, *yarray, *zarray;
    double *x, *y, *z;
    int *triangle_id, *cnr1_array, *cnr2_array, *cnr3_array;
    int *id, *cnr1, *cnr2, *cnr3;
    int i;
    int n_triangles;  /* aka adcirc "elements" */
    int n_coords;     /* aka adcirc "nodes" */
    int n_sides;      /* always 3 */
    double xarr[4], yarr[4], zarr[4];
    int idx;
    struct line_pnts *Points;
    struct line_cats *Cats;
    char title[25];

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("Import, ADCIRC, vector");
    module->description =
	_("Loads ADCIRC fort.14 triangular mesh into a GRASS vector.");

    infile = G_define_standard_option(G_OPT_F_INPUT);
    outmap = G_define_standard_option(G_OPT_V_OUTPUT);

    points_flag = G_define_flag();
    points_flag->key = 'p';
    points_flag->description = _("Load node points instead of mesh lines");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    /* todo: on the fly reprojection from wgs84 lat/lon */
    G_get_set_window(&window);
    if (window.proj != PROJECTION_LL)
	G_fatal_error(_("This module can only be run from a lat/lon location."));

    if ((ascii = fopen(infile->answer, "r")) == NULL)
	G_fatal_error(_("Unable to open fort.14 file <%s>"), infile->answer);


    zcoor = WITH_Z; /* 3D */

    if (points_flag->answer)
	type = GV_POINT;
    else
	type = GV_LINE;

    Vect_open_new(&Map, outmap->answer, zcoor);
    Vect_hist_command(&Map);

    /* Must always use this to create an initialized line_pnts structure */
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();


    if (G_getl2(buff, BUFFSIZE - 1, ascii) == 0)
	G_fatal_error(_("Error reading %s"), infile->answer);
    strncpy(title, buff, 24);
    title[24] = '\0';
    Vect_set_map_name(&Map, title);

    if (G_getl2(buff, BUFFSIZE - 1, ascii) == 0)
	G_fatal_error(_("Error reading number of elements from %s"),
		      infile->answer);

    if (sscanf(buff, "%d %d", &n_triangles, &n_coords) < 2)
	G_fatal_error(_("Error reading number of nodes: [%s]"), buff);

    sprintf(buff, "ADCIRC fort.14 triangular mesh containing %d nodes", n_coords);
    Vect_set_comment(&Map, buff);


    node_array = (int *)G_calloc(n_coords, sizeof(int));
    xarray = (double *)G_calloc(n_coords, sizeof(double));
    yarray = (double *)G_calloc(n_coords, sizeof(double));
    zarray = (double *)G_calloc(n_coords, sizeof(double));

    node = node_array;
    x = xarray;
    y = yarray;
    z = zarray;

    for (i = 0; i < n_coords; i++) {
	if (G_getl2(buff, BUFFSIZE - 1, ascii) == 0)
	    G_fatal_error(_("End of file reached before end of coordinates"));

	if (sscanf(buff, "%d%lf%lf%lf", node, x, y, z) < 4)
	    G_fatal_error(_("Error reading file: (bad coord) [%s]"), buff);

	/* G_debug(5, "coor in: node=%d  x=%f  y=%f  z=%f", *node, *x, *y, *z); */

	node++;
	x++;
	y++;
	z++;
    }

    G_message("Scanned %d coordinates", n_coords);


    if (points_flag->answer) {
	for (i = 0; i < n_coords; i++) {

	    /* Allocation is handled for line_pnts */
	    if (0 > Vect_copy_xyz_to_pnts(Points, &xarray[i], &yarray[i],
					  &zarray[i], 1))
		G_fatal_error(_("Out of memory"));

	    Vect_cat_set(Cats, 1, node_array[i]);
	    Vect_write_line(&Map, type, Points, Cats);
	    Vect_reset_cats(Cats);
	}

	fclose(ascii);
	Vect_build(&Map);
	Vect_close(&Map);

	exit(EXIT_SUCCESS);
    }

    /*
    for (i = 0; i < 10; i++)
	G_debug(1, "i=%d,  val=%f", i, zarray[i]);
    */

    triangle_id = (int *)G_calloc(n_triangles, sizeof(int));
    cnr1_array = (int *)G_calloc(n_triangles, sizeof(int));
    cnr2_array = (int *)G_calloc(n_triangles, sizeof(int));
    cnr3_array = (int *)G_calloc(n_triangles, sizeof(int));

    id = triangle_id;
    cnr1 = cnr1_array;
    cnr2 = cnr2_array;
    cnr3 = cnr3_array;

    for (i = 0; i < n_triangles; i++) {
	if (G_getl2(buff, BUFFSIZE - 1, ascii) == 0)
	    G_fatal_error(_("End of file reached before end of triangle definition"));

	if (sscanf(buff, "%d%d%d%d%d", id, &n_sides, cnr1, cnr2, cnr3) < 5)
	    G_fatal_error(_("Error reading file: (bad coord) [%s]"), buff);

	if (n_sides != 3)
	    G_fatal_error(_("Funny triangle: [%s]"), buff);

	/* G_debug(0, "triangle in: id=%d  a=%d  b=%d  c=%d", *id, *cnr1, *cnr2, *cnr3); */

	id++;
	cnr1++;
	cnr2++;
	cnr3++;
    }

    G_message("Scanned %d triangles", n_triangles);

    /*
    for (i = 0; i < 10; i++) {
	idx = get_index(node_array, n_coords, cnr3_array[i]);
	G_debug(1, "i=%d  node=%d  val=%f", i, cnr3_array[i], zarray[idx]);
    }
    */

    for (i = 0; i < n_triangles; i++) {

	idx = get_index(node_array, n_coords, cnr1_array[i]);
	xarr[0] = xarray[idx];
	yarr[0] = yarray[idx];
	zarr[0] = zarray[idx] * -1;

	idx = get_index(node_array, n_coords, cnr2_array[i]);
	xarr[1] = xarray[idx];
	yarr[1] = yarray[idx];
	zarr[1] = zarray[idx] * -1;

	idx = get_index(node_array, n_coords, cnr3_array[i]);
	xarr[2] = xarray[idx];
	yarr[2] = yarray[idx];
	zarr[2] = zarray[idx] * -1;

	xarr[3] = xarr[0];
	yarr[3] = yarr[0];
	zarr[3] = zarr[0];

	/*
	G_debug(5, "tri %d: (%d,  %d,  %d)", triangle_id[i], cnr1_array[i],
		cnr2_array[i], cnr3_array[i]);
	G_debug(5, "tri %d: %f  %f  %f", triangle_id[i], zarr[0], zarr[1], zarr[2]);
	*/

	/* Allocation is handled for line_pnts */
	if (0 > Vect_copy_xyz_to_pnts(Points, xarr, yarr, zarr, 4))
	    G_fatal_error(_("Out of memory"));

	Vect_cat_set(Cats, 1, triangle_id[i]);
	Vect_write_line(&Map, type, Points, Cats);
	Vect_reset_cats(Cats);

	/* G_percent(i, n_triangles, 3); */
    }

    fclose(ascii);
    Vect_build(&Map);
    Vect_close(&Map);

    exit(EXIT_SUCCESS);
}


/* returns array idx, or -1 if not found */
int get_index(int *array, int size, int val)
{
    int i;

    /* first check the easy case when everything is sequentially ordered */
    if(val > 1 && val < size && array[val-1] == val)
	return val-1;

    /* if that didn't work, use brute force */
    for (i = 0; i < size; i++) {
	if (array[i] == val)
	    return i;
    }

    return -1;
}
