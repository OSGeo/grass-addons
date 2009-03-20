
/**********************************************************************
 * 
 * MODULE:       v.in.gshhs (based on gshhstograss.c)
 * 
 * AUTHORS:      Simon Cox (simon@ned.dem.csiro.au) & (gshhstograss.c)
 * 		 Paul Wessel (wessel@soest.hawaii.edu) & (gshhstograss.c)
 *		 Bob Covill <bcovill@tekmap.ns.ca> (v.in.gshhs)
 *               Markus Metz <markus.metz.giswork googlemail.com> (v.in.gshhs for grass 6.4)
 * 
 * PURPOSE:	 To extract GRASS binary vector data from binary gshhs
 *		 shoreline data as described in
 *               Wessel, P., and W.H.F. Smith. A Global Self-consistent, 
 *               Hierarchical, High-resolution Shoreline Database, 
 *               J. Geophys. Res., 101(B4), 8741-8743, 1996.
 *		 http://www.soest.hawaii.edu/wessel/hshhs/gshhs.html
 * 
 * LICENSE:      This program is free software under the 
 *               GNU General Public License (>=v2). 
 *               Read the file COPYING that comes with GRASS
 *               for details.
 *
 **********************************************************************/

#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/Vect.h>
#include <grass/gprojects.h>
#include <grass/glocale.h>

/* updating to a newer GSHHS version can be as easy as replacing gshhs.h
 * if not too many changes were introduced */
#include "gshhs.h"

int write_line_tiled(struct Map_info *, int, struct line_pnts *,
	    struct line_cats *, double);

struct pj_info info_in;
struct pj_info info_out;


int main(int argc, char **argv)
{
    double w, e, s, n, area, lon, lat;
    double minx = -180., maxx = 180., miny = -90., maxy = 90.;
    char *dataname, *outname;
    char buf[2000], source;
    static char *slevel[] = { "land", "lake", "island in lake",
	"pond in island in lake" };
    int shore_levels = 4;
    /* taken from gshhs.c, keep in sync */
    FILE *fp;
    int k, i, n_read, flip, level, version, greenwich, src;
    int max_east = 180000000;	/* max_east = 270000000: confuses GRASS */
    int cnt = 0, getme = 0;
    struct GSHHS_POINT p;	/* renamed to avoid conflict */
    struct GSHHS h;
    /* GRASS specific */
    struct Key_Value *out_proj_keys, *out_unit_keys;
    int type, zone;
    struct Cell_head region;
    struct Map_info VectMap;
    struct line_pnts *Points;
    struct line_cats *Cats;
    double lat_nw, lon_nw, lat_ne, lon_ne;
    double lat_sw, lon_sw, lat_se, lon_se;
    struct
    {
	struct Option *input, *output, *n, *s, *e, *w;
    } parm;
    struct
    {
	struct Flag *r, *topo, *a;
    } flag;
    struct GModule *module;

    /* attribute table */
    struct field_info *Fi;
    dbDriver *driver;
    dbString sql, strval;
    char *cat_col_name = "cat";

    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    module->description = 
	_("Imports Global Self-consistent Hierarchical High-resolution "
	  "Shoreline (GSHHS) vector data.");

    parm.input = G_define_option();
    parm.input->key = "input";
    parm.input->type = TYPE_STRING;
    parm.input->required = YES;
    parm.input->gisprompt = "old_file,file,gshhs";
    parm.input->description =
	_("Name of GSHHS shoreline file: gshhs_[f|h|i|l|c].b");

    parm.output = G_define_standard_option(G_OPT_V_OUTPUT);

    flag.r = G_define_flag();
    flag.r->key = 'r';
    flag.r->description = _("Limit import to the current region");

    flag.topo = G_define_flag();
    flag.topo->key = 't';
    flag.topo->description = _("Do not build topology for output vector");

    /* Importing as boundary causes problems with subregions, incorrect boundaries */
    /*    flag.a = G_define_flag();
       flag.a->key = 'a';
       flag.a->description =
       "Import shoreline as type line (default = boundary)";
     */

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    /* get parameters */
    dataname = parm.input->answer;
    outname = parm.output->answer;

    G_get_window(&region);
    zone = region.zone;

    /* Out Info */
    out_proj_keys = G_get_projinfo();
    out_unit_keys = G_get_projunits();

    if (pj_get_kv(&info_out, out_proj_keys, out_unit_keys) < 0) {
	exit(0);
    }
    G_free_key_value(out_proj_keys);
    G_free_key_value(out_unit_keys);

    /* In Info */
    /* N.B. GSHHS data is not referenced to any ellipsoid or datum. This
     * limits its precision to several hundred metres. Hence it does not
     * matter which ellipsoid we use in the input projection keys as the
     * precision of the data is less than the maximum error that could be 
     * caused by projecting using the 'wrong' ellipsoid.
     * Anyone who understands this better than me feel free to change it.
     * PK March 2003 */

    /* GSHHS spatial reference
     * GSHHS is a combination of WVS and WDBII
     * The WVS dataset uses WGS84 according to
     * http://shoreline.noaa.gov/data/datasheets/wvs.html
     * The WDBII dataset may have used wgs72 but is inaccurate anyway
     * Safest would be to always use wgs84
     * MM Jan 2009 */

    /* set input projection to lat/long w/ same ellipsoid as output */
    /* TODO: use wgs84 datum and ellipsoid */
    info_in.zone = 0;
    info_in.meters = 1.;
    sprintf(info_in.proj, "ll");
    if ((info_in.pj = pj_latlong_from_proj(info_out.pj)) == NULL)
	G_fatal_error(_("Unable to set up lat/long projection parameters"));

    if (flag.r->answer) {
	/* get coordinates from current region */
	minx = region.west;
	maxx = region.east;
	miny = region.south;
	maxy = region.north;

	if (G_projection() != PROJECTION_LL) {
	    /* convert to latlon and print bounds */

	    /* NW */
	    lon_nw = minx;
	    lat_nw = maxy;
	    if (pj_do_proj(&lon_nw, &lat_nw, &info_out, &info_in) < 0) {
		G_fatal_error(
		    _("Error in coordinate transformation for north-west corner"));
	    }

	    /* NE */
	    lon_ne = maxx;
	    lat_ne = maxy;
	    if (pj_do_proj(&lon_ne, &lat_ne, &info_out, &info_in) < 0) {
		G_fatal_error(
		    _("Error in coordinate transformation for north-east corner"));
	    }

	    /* SE */
	    lon_se = maxx;
	    lat_se = miny;
	    if (pj_do_proj(&lon_se, &lat_se, &info_out, &info_in) < 0) {
		G_fatal_error(
		    _("Error in coordinate transformation for south-east corner"));
	    }

	    /* SW */
	    lon_sw = minx;
	    lat_sw = miny;
	    if (pj_do_proj(&lon_sw, &lat_sw, &info_out, &info_in) < 0) {
		G_fatal_error(
		    _("Error in coordinate transformation for south-west corner"));
	    }

	    /* get north max */
	    maxy = lat_nw > lat_ne ? lat_nw : lat_ne;
	    /* get south min */
	    miny = lat_sw < lat_se ? lat_sw : lat_se;
	    /* get east max */
	    maxx = lon_ne > lon_se ? lon_ne : lon_se;
	    /* get west min */
	    minx = lon_nw < lon_sw ? lon_nw : lon_sw;
	}
    }

    /* check coordinate accuracy */
#if 0
    /* don't check coordinate accuracy,
     * it's the current window set with g.region */
    if (maxx < minx) {
	G_fatal_error(_("maxx %f < minx %f."), maxx, minx);
    }

    if (maxy < miny) {
	G_fatal_error(_("maxy %f < miny %f."), maxy, miny);
    }
#endif

    while (maxx > 180.0)
	maxx -= 360.0;
    while (maxx < -180.0)
	maxx += 360.0;	

    while (minx > 180.0)
	minx -= 360.0;
    while (minx < -180.0)
	minx += 360.0;	

    G_message(_("Using lat/lon bounds N=%f S=%f E=%f W=%f"), maxy, miny,
	      maxx, minx);

    if (maxx < minx)
	maxx += 360.; /* easier to get overlapping features */

    /* open GSHHS shoreline for reading */
    if ((fp = fopen(dataname, "rb")) == NULL) {
	G_fatal_error(_("Could not find file <%s>"), dataname);
    }

    /* Open new vector */
    if (0 > Vect_open_new(&VectMap, outname, 0)) {
	G_fatal_error(_("Cannot open new vector map <%s>"), outname);
    }

    /* set vector line type to GV_LINE, GV_BOUNDARY is currently not supported */
    type = GV_LINE;

    /* Initialize vector line struct */
    Points = Vect_new_line_struct();

    /* Initialize vector category struct */
    Cats = Vect_new_cats_struct();

    /* read header from GSHHS database */
    n_read = fread((void *)&h, (size_t) sizeof(struct GSHHS), (size_t) 1, fp);
    version = (h.flag >> 8) & 255;
    flip = (version < 4);	/* Take as sign that byte-swapping is needed */
    if (flip) {
	version = swabi4((unsigned int)h.flag);
	version = (version >> 8) & 255;
    }

    /* read lines from GSHHS database */
    while (n_read == 1) {
	/* taken from gshhs.c, keep in sync */
	if (flip) {
	    h.id = swabi4((unsigned int)h.id);
	    h.n = swabi4((unsigned int)h.n);
	    h.west = swabi4((unsigned int)h.west);
	    h.east = swabi4((unsigned int)h.east);
	    h.south = swabi4((unsigned int)h.south);
	    h.north = swabi4((unsigned int)h.north);
	    h.area = swabi4((unsigned int)h.area);
	    h.flag = swabi4((unsigned int)h.flag);
	}
	level = h.flag & 255;
	/* version = (h.flag >> 8) & 255; */
	greenwich = (h.flag >> 16) & 255;
	src = (h.flag >> 24) & 255;
	w = h.west * GSHHS_SCL;	/* Convert from microdegrees to degrees */
	e = h.east * GSHHS_SCL;
	s = h.south * GSHHS_SCL;
	n = h.north * GSHHS_SCL;
	/* skip WDBII data because they are too inacurate? */
	source = (src == 1) ? 'W' : 'C';	/* Either WVS or CIA (WDBII) pedigree */
	area = 0.1 * h.area;	/* Now im km^2 */

        /* GRASS specific, max_east must always be 180 */
	while (w > 180.)
	    w -= 360.0;
	while (e > 180.)
	    e -= 360.0;

	if (maxx > 180. && w < 0)
	    w += 360.;
	if (maxx > 180. && e < 0)
	    e += 360.;

	getme = 1;
	if (flag.r->answer) {
	    getme = 0;
	    /* check gshhs bbox */
	    if (w >= minx && w < maxx && e <= maxx && e > minx &&
		s >= miny && s < maxy && n <= maxy && n > miny) {
		getme = 1; /* inside current region */
	    }
	    else if (w < maxx && e > minx && s < maxy && n > miny) {
		getme = 2; /* overlap */
	    }
	}
	
	if (getme) {
	    /* abusing getme flag a bit */
	    if (getme == 2)
		getme = 0;
	    
	    Vect_reset_line(Points);
	    Vect_reset_cats(Cats);
	    /* simple table and cats for layer 1: not unique, just per slevel */
	    Vect_cat_set(Cats, 1, level);
	    /* cats for layer 2 are unique ID, same like GSHHS ID */
	    Vect_cat_set(Cats, 2, h.id);

	    for (k = 0; k < h.n; k++) {
		if (fread
		    ((void *)&p, (size_t) sizeof(struct GSHHS_POINT),
		     (size_t) 1, fp) != 1)
		    G_fatal_error(_("Error reading data"));

		if (flip) {
		    p.x = swabi4((unsigned int)p.x);
		    p.y = swabi4((unsigned int)p.y);
		}
		lon = p.x * GSHHS_SCL;
		if (p.x > max_east) /* GSHHS lon coords are 0 - 360 */
		    lon -= 360.0;
		lat = p.y * GSHHS_SCL;

		if (getme == 0) { /* overlap */
		    /* datum border wrap around work around, clumsy code but works */
		    if (maxx > 180. && lon < 0) {
			if (lat >= miny && lat <= maxy && (lon + 360.) >= minx && (lon + 360.) <= maxx) {
			    /* vertex inside current region, import line */
			    getme = 1;
			}
		    }
		    else {
			if (lat >= miny && lat <= maxy && lon >= minx && lon <= maxx) {
			    /* vertex inside current region, import line */
			    getme = 1;
			}
		    }
		
		}
		/* needed for accurate bboxes */
		if (Points->n_points) {
		    if (Points->x[Points->n_points - 1] - lon < -180.)
			lon -= 360.;
		    if (Points->x[Points->n_points - 1] - lon > 180.)
			lon += 360.;
		}
		/* The GSHHS Antarctica problem: convert from 0 - 360 to -180 - 180  */
		if (s < -80 && lon < -180) {
		    Vect_append_point(Points, lon, lat, 0.);
		    /* ...and close polygon */
		    Vect_append_point(Points, -180, -90, 0.);
		    Vect_append_point(Points, 180, -90, 0.);
		    lon += 360;
		}

		Vect_append_point(Points, lon, lat, 0.);
		
	    }			/* done with line */

	    if (getme && Points->n_points) {
		/* change thresh if you want longer line segments */
		write_line_tiled(&VectMap, type, Points, Cats, 2.);
	    }
	    else
		cnt++;
	}
	else {
	    G_debug(1, "skipped line box west: %f, east: %f, north: %f, south: %f",
		    w, e, n, s);
	    fseek(fp, (long)(h.n * sizeof(struct GSHHS_POINT)), SEEK_CUR);
	    cnt++;
	}
	/* 270 needed for more than Eurasiafrica only, solved above */
	/* max_east = 180000000; */ /* Only Eurasiafrica needs 270 */

	n_read =
	    fread((void *)&h, (size_t) sizeof(struct GSHHS), (size_t) 1, fp);
    }
    /* done with gshhs file */
    fclose(fp);

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    /* write out vect header info */
    Vect_set_scale(&VectMap, 100000);
    sprintf(buf, "GSHHS shorelines version %d imported by v.in.gshhs",
	    version);
    Vect_set_comment(&VectMap, buf);

    /* create table for layer 1 and link new vector to table, code taken from v.in.ogr */
    db_init_string(&sql);
    db_init_string(&strval);

    Fi = Vect_default_field_info(&VectMap, 1, NULL, GV_1TABLE);

    Vect_map_add_dblink(&VectMap, 1, NULL, Fi->table,
			cat_col_name, Fi->database, Fi->driver);

    sprintf(buf, "create table %s (%s integer, type varchar(25))",
	    Fi->table, cat_col_name);
    db_set_string(&sql, buf);

    driver =
	db_start_driver_open_database(Fi->driver,
				      Vect_subst_var(Fi->database, &VectMap));

    if (driver == NULL) {
	G_fatal_error(_("Cannot open database <%s> by driver <%s>"),
		      Vect_subst_var(Fi->database, &VectMap), Fi->driver);
    }

    G_debug(1, "table: %s", Fi->table);
    G_debug(1, "driver: %s", Fi->driver);
    G_debug(1, "database: %s", Fi->database);

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	db_close_database(driver);
	db_shutdown_driver(driver);
	G_fatal_error(_("Cannot create table: <%s>"), db_get_string(&sql));
    }

    if (db_create_index2(driver, Fi->table, cat_col_name) != DB_OK)
	G_warning(_("Cannot create index"));

    if (db_grant_on_table
	(driver, Fi->table, DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK)
	G_fatal_error(_("Cannot grant privileges on table <%s>"), Fi->table);

    db_begin_transaction(driver);

    for (i = 0; i < shore_levels; i++) {
	sprintf(buf, "insert into %s values ( %d, \'%s\')", Fi->table, i + 1,
		slevel[i]);
	db_set_string(&sql, buf);

	if (db_execute_immediate(driver, &sql) != DB_OK) {
	    db_close_database(driver);
	    db_shutdown_driver(driver);
	    G_fatal_error(_("Cannot insert new row: <%s>"),
			  db_get_string(&sql));
	}
    }

    db_commit_transaction(driver);
    db_close_database_shutdown_driver(driver);

    /* table for layer 1 created */

    if (flag.topo->answer) {
	G_message(_("Run \"v.build map=%s option=build\" to build topology"),
		  outname);
    }
    else {
	Vect_build(&VectMap);
    }

    Vect_hist_command(&VectMap);
    Vect_close(&VectMap);

    G_message("--------------------------------------");
    G_message(_("Skipped GSHHS lines: %d"), cnt);
    G_message(_("GSHHS shoreline version %d import complete"), version);

    exit(EXIT_SUCCESS);
}

/*!
   \brief Splits line in segments using maximum bounding box dimensions
   The maximum bbox size of a line segment will be thresh x thresh
   The bbox will be not wider than thres and not higher than thresh

   The function calls G_fatal_error() on error.

   \param Map pointer to vector map
   \param type feature type
   \param points feature geometry
   \param cats feature categories
   \param thresh bbox dimension threshold for splitting

   \return number of line segments written out
 */

int write_line_tiled(struct Map_info *Map, int type,
    struct line_pnts *Points, struct line_cats *Cats, double thresh) {

    int i, nsegs = 0;
    double currx, curry, lastx = 0., lasty = 0.;
    double minx, maxx, miny, maxy;
    struct line_pnts *BPoints;
    
    if (Points->n_points) {
	lastx = Points->x[0];
	lasty = Points->y[0];
    }
    else
	return nsegs;
    
    BPoints = Vect_new_line_struct();

    minx = maxx = miny = maxy = 0.;

    for (i = 0; i < Points->n_points; i++) {

	/* restrict bbox side length to thresh */
	currx = Points->x[i];
	curry = Points->y[i];
	if (minx > (currx - lastx))
	    minx = currx - lastx;
	if (maxx < (currx - lastx))
	    maxx = currx - lastx;
	if (miny > (curry - lasty))
	    miny = curry - lasty;
	if (maxy < (curry - lasty))
	    maxy = curry - lasty;
	    
	if (BPoints->n_points > 1 && ((maxx - minx) > thresh || (maxy - miny) > thresh)) {

	    lastx = BPoints->x[BPoints->n_points - 1]; /* keep last x for new line */
	    lasty = BPoints->y[BPoints->n_points - 1]; /* keep last y for new line */

	    Vect_write_line(Map, type, BPoints, Cats);
	    Vect_reset_line(BPoints);
	    Vect_append_point(BPoints, lastx, lasty, 0.);
	    minx = maxx = miny = maxy = 0.;
	    nsegs++;
	}
	/* reprojection is v.in.gshhs specific */
	if (G_projection() != PROJECTION_LL) {
	    if (pj_do_proj(&currx, &curry, &info_in, &info_out) < 0) {
		G_fatal_error(_("Error in coordinate transformation"));
	    }
	}
	Vect_append_point(BPoints, currx, curry, 0.);
    }
    /* last line segment always has >=2 vertices */
    Vect_write_line(Map, type, BPoints, Cats);
    nsegs++;

    Vect_destroy_line_struct(BPoints);

    return nsegs;
}
