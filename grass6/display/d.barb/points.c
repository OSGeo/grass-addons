#include <float.h>
#include <grass/gis.h>
//#include <grass/Vect.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "local_proto.h"


/* load and plot barbs from data stored in a vector map's attribute table */
void do_barb_points(char *vinput_name, int vlayer, char *dir_u_col,
		    char *mag_v_col, int is_component, int color,
		    int aspect_type, double scale, double setpeak,
		    int style, int reverse)
{

    struct Map_info vMap;
    char *mapset;
    int num_pts;
    double *coord_x, *coord_y, *magn, *dirn;
    int i;
    double peak = -DBL_MAX, scale_fact;

    //? needed?    static struct line_pnts *Points;
    //    /* Create and initialize struct's where to store points/lines and categories */
    //    Points = Vect_new_line_struct();
    //    Cats = Vect_new_cats_struct();

    magn = NULL;		/* init in case it isn't used */

    G_debug(1, "Doing sparse points ...");

    if ((mapset = G_find_vector2(vinput_name, "")) == NULL)
	G_fatal_error(_("Vector map <%s> not found"), vinput_name);

    /* Predetermine level at which a map will be opened for reading */
    if (Vect_set_open_level(2))
	G_fatal_error(_("Unable to set predetermined vector open level"));

    /* Open existing vector for reading lib/vector/Vlib/open.c */
    if (1 > Vect_open_old(&vMap, vinput_name, mapset))
	G_fatal_error(_("Unable to open vector map <%s>"), vinput_name);

    G_debug(3, "<%s> is open", vinput_name);

    /* we need to scan through and find the greatest value in of the
       magnitude within the current region and scale from that. hence
       the following complexity ... */
    num_pts = count_pts_in_region(&vMap);
    G_debug(2, "  %d points found in region", num_pts);

    coord_x = G_calloc(num_pts + 1, sizeof(double));
    coord_y = G_calloc(num_pts + 1, sizeof(double));
    dirn = G_calloc(num_pts + 1, sizeof(double));
    if (mag_v_col)
	magn = G_calloc(num_pts + 1, sizeof(double));
    else
	magn = NULL;

    fill_arrays(&vMap, vlayer, dir_u_col, mag_v_col, is_component,
		coord_x, coord_y, dirn, magn);

    G_debug(3, "Arrays are filled.");

    if (aspect_type == TYPE_GRASS) {
	for (i = 0; i < num_pts; i++) {
	    //G_debug(5, "in=%.1f  out=%.1f", dirn[i], 90-dirn[i] < 0 ? 360+90-dirn[i] : 90-dirn[i]);
	    dirn[i] = 90 - dirn[i];
	    if (dirn[i] < 0)
		dirn[i] += 360;
	}
    }

    if (reverse) {
	for (i = 0; i < num_pts; i++) {
	    //G_debug(5, "in=%.1f  out=%.1f", dirn[i], 90-dirn[i] < 0 ? 360+90-dirn[i] : 90-dirn[i]);
	    dirn[i] = dirn[i] + 180;
	    if (dirn[i] > 360)
		dirn[i] -= 360;
	}
    }

    if(!isnan(setpeak))
	peak = setpeak;
    else
	peak = max_magnitude(magn, num_pts);
    
    G_debug(2, "  peak = %.2f", peak);
    if (style == TYPE_BARB || style == TYPE_SMLBARB) {
	if(peak > 150)
	    G_warning(_("Maximum wind barb displayed is 150 knots"));
    }

    scale_fact = 20. * scale / peak;

    G_debug(3, "Ready to draw");

    for (i = 0; i < num_pts; i++) {
	draw_barb(coord_x[i], coord_y[i], magn[i] * scale_fact, dirn[i],
		  color, scale, style);
    }

    Vect_close(&vMap);

    return;
}

/* counts point features in the current region box */
int count_pts_in_region(struct Map_info *Map)
{
    int count = 0, nlines, ltype;
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct Cell_head window;

    G_debug(3, "count_pts_in_region()");
    G_get_window(&window);
    G_debug(4, "  n=%.2f s=%.2f e=%.2f w=%.2f", window.north, window.south,
	    window.east, window.west);

    /* Create and initialize struct's where to store points/lines and categories */
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    nlines = Vect_get_num_lines(Map);
    G_debug(2, "  %d features found in map", nlines);

    Vect_rewind(Map);

    while (1) {
	ltype = Vect_read_next_line(Map, Points, Cats);
	switch (ltype) {
	case -1:
	    G_fatal_error(_("Can't read vector map"));
	case -2:		/* EOF */
	    return count;
	}

	if (!(ltype & GV_POINTS))
	    continue;

	if (Points->x[0] > window.east || Points->x[0] < window.west ||
	    Points->y[0] > window.north || Points->y[0] < window.south)
	    continue;

	count++;
    }

    return -1;			/* shouldn't get here */
}


/* populates arrays */
/* rather redundant WRT count_pts_in_region() ... */
void fill_arrays(struct Map_info *Map, int layer, char *dir_u, char *mag_v,
		 int is_uv, double *Xs, double *Ys, double *Dirs,
		 double *Mags)
{
    int i, ltype, nrec;
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct Cell_head window;
    struct field_info *fi = NULL;
    dbDriver *driver = NULL;
    dbCatValArray cvarr_dir_u, cvarr_mag_v;
    dbCatVal *cv_dir_u = NULL, *cv_mag_v = NULL;
    double theta, r;

    G_debug(3, "fill_arrays()");

    G_get_window(&window);


    fi = Vect_get_field(Map, (layer > 0 ? layer : 1));
    if (fi == NULL) {
	G_fatal_error(_("Database connection not defined for layer %d"),
		      (layer > 0 ? layer : 1));
    }

    driver = db_start_driver_open_database(fi->driver, fi->database);
    if (driver == NULL) {
	G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		      fi->database, fi->driver);
    }

    /* Create and initialize struct's where to store points/lines and categories */
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    db_CatValArray_init(&cvarr_dir_u);
    if (Mags)
	db_CatValArray_init(&cvarr_mag_v);


    nrec = db_select_CatValArray(driver, fi->table, fi->key,
				 dir_u, NULL, &cvarr_dir_u);
    G_debug(3, "nrec (%s) = %d", dir_u, nrec);

    if (cvarr_dir_u.ctype != DB_C_TYPE_INT &&
	cvarr_dir_u.ctype != DB_C_TYPE_DOUBLE)
	G_fatal_error(_("Direction/u column (%s) is not a numeric."), dir_u);

    if (nrec < 0)
	G_fatal_error(_("Cannot select data (%s) from table"), dir_u);
    G_debug(3, "%d records selected from table", nrec);

    if (Mags) {
	nrec = db_select_CatValArray(driver, fi->table, fi->key,
				     mag_v, NULL, &cvarr_mag_v);
	G_debug(4, "nrec (%s) = %d", mag_v, nrec);

	if (cvarr_mag_v.ctype != DB_C_TYPE_INT &&
	    cvarr_mag_v.ctype != DB_C_TYPE_DOUBLE)
	    G_fatal_error(_("Magnitude/v column (%s) is not a numeric."),
			  mag_v);

	if (nrec < 0)
	    G_fatal_error(_("Cannot select data (%s) from table"), mag_v);
	G_debug(3, "%d records selected from table", nrec);
    }

    Vect_rewind(Map);
    i = 0;

    G_debug(3, "Select is done.");

    while (1) {
	ltype = Vect_read_next_line(Map, Points, Cats);
	switch (ltype) {
	case -1:
	    db_close_database_shutdown_driver(driver);
	    G_fatal_error(_("Can't read vector map"));
	case -2:		/* EOF */
	    db_close_database_shutdown_driver(driver);
	    G_debug(3, "  Array fill done.");
	    return;
	}

	if (!(ltype & GV_POINTS))
	    continue;

	if (Points->x[0] > window.east || Points->x[0] < window.west ||
	    Points->y[0] > window.north || Points->y[0] < window.south)
	    continue;

	Xs[i] = Points->x[0];
	Ys[i] = Points->y[0];
	G_debug(5, "  Xs[%d] = %.2f  Ys[%d] = %.2f  cat = %d", i, Xs[i],
		i, Ys[i], Cats->cat[0]);


	/* Read rotation from db */
	if (db_CatValArray_get_value(&cvarr_dir_u, Cats->cat[0], &cv_dir_u) != DB_OK)
	    Dirs[i] = 0.0 / 0.0;	/* NaN */
	else
	    Dirs[i] = cvarr_dir_u.ctype == DB_C_TYPE_INT ?
		(double)cv_dir_u->val.i : cv_dir_u->val.d;


	/* Read magnitude from db */
	if (Mags) {
	    if (db_CatValArray_get_value
		(&cvarr_mag_v, Cats->cat[0], &cv_mag_v) != DB_OK)
		Mags[i] = 0.0 / 0.0;	/* NaN */
	    else
		Mags[i] = cvarr_mag_v.ctype == DB_C_TYPE_INT ?
		    (double)cv_mag_v->val.i : cv_mag_v->val.d;
	    if (!is_uv) {
		if (Mags[i] < 0)	/* magnitude is scalar and can only be positive */
		    Mags[i] = 0;
	    }
	}

	if (is_uv) {
	    /* now that we have the data loaded, cycle back and process it */
	    theta = R2D(atan2(Mags[i], Dirs[i]));
	    r = sqrt(Dirs[i] * Dirs[i] + Mags[i] * Mags[i]);
	    Dirs[i] = theta;
	    Mags[i] = r;
	}

	G_debug(5, "    Dirs[%d] = %.2f  Mags[%d] = %.2f", i, Dirs[i],
		i, Mags[i]);
	i++;
    }

    db_close_database_shutdown_driver(driver);
    return;	/* shouldn't get here */
}


/* scan for biggest value in magnitude array */
double max_magnitude(double *magn, int n)
{
    double maxmag = -DBL_MAX;
    int i;

    for (i = 0; i < n; i++) {
	if (magn[i] > maxmag)
	    maxmag = magn[i];
    }
    return maxmag;
}
