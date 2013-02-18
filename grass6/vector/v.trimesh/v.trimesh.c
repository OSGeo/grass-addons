
/*****************************************************************************/
/*  MODULE: v.trimesh                                                        */
/*  AUTHOR: Jaime Carrera-Hernandez, University of Alberta, Edmonton Canada  */
/*              jaime.carrera-AT-ualberta.ca                                 */
/*              jaime.carrerah-AT-gmail.com                                  */
/*  PURPOSE: v.trimesh creates a triangular mesh                              */
/*         using Triangle (by Jonathan Richard Shewchunk)                    */
/*                                                                           */
/* COPYRIGHT: (C) 2008 by the GRASS development team                         */
/*                                                                           */

/*****************************************************************************/


#ifdef SINGLE
#define REAL float
#else /* not SINGLE */
#define REAL double
#endif /* not SINGLE */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/glocale.h>
#include <grass/dbmi.h>
#include "triangle.h"

int main(int argc, char *argv[])
{
    struct Option *input, *output;
    struct Flag *nomaxarea;
    struct Map_info Map;
    struct GModule *module;
    struct field_info *Fi;
    dbValue *dbvalue;
    dbDriver *driver;
    dbCursor cursor;
    dbString stmt;
    dbColumn *col;
    dbTable *table;
    char buf[2000];
    int type, ctype, i, cat, j, firstnode, segments, h;
    int numberofregions, c, nnodes, nlines;
    int count, more, of;

    /* val is used for area constraints... currently set to int values */

    double *xptr, *yptr, *zptr, x, y, areaconst;

    struct triangulateio in, out;

    /* I need dynamic allocation */
    double pointlist[10000];

    /* regionlist is used for centroids         */
    /* val is for area constraints centroids    */
    double regionlist[40];
    int val[40];
    int segmentlist[10000];

    /*    int holelist[30]; */
    struct line_pnts *Points;
    struct line_cats *Cats;
    struct Option *column;

    /*To determine centroids */
    int left, center, right;
    double xleft, yleft, xcenter, ycenter, xright, yright;
    double xm1, xm2, ym, m1, m2, b1, b2;

    int area, areas, centroid;

    G_gisinit(argv[0]);


    module = G_define_module();
    module->keywords = _("vector");
    module->description = _("Create a triangular mesh from a vector map");

    input = G_define_standard_option(G_OPT_V_INPUT);

    column = G_define_option();
    column->key = "column";
    column->type = TYPE_STRING;
    column->required = YES;
    column->multiple = NO;
    column->description =
	_("Column name with area constraints/centroid attributes");

    output = G_define_standard_option(G_OPT_V_OUTPUT);

    nomaxarea = G_define_flag();
    nomaxarea->key = 'a';
    nomaxarea->description = _("Do not use areal constraint");
    /* The vector map is opened */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    Vect_set_open_level(2);
    Vect_open_old(&Map, input->answer, "");

    /* The vector map is now read (boundaries and centroids) */

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    areas = Vect_get_num_areas(&Map);
    printf("areas=%i\n", areas);

    /* Verifying if data were input properly */
    if (!column->answer)
	G_fatal_error("Please assign a column with areal constraints");

    h = 0;
    c = 0;
    j = 0;
    segments = 0;

    for (area = 1; area <= areas; area++) {
	centroid = Vect_get_area_centroid(&Map, area);
	firstnode = j;

	Vect_get_area_points(&Map, area, Points);
	printf("Reading boundaries for area %i\n", area);
	xptr = Points->x;
	yptr = Points->y;

	while (Points->n_points--) {
	    pointlist[j * 2] = *xptr++;
	    pointlist[j * 2 + 1] = *yptr++;
	    j++;
	}
	j--;
	printf("before reading nodes from boundary\n");
	for (i = firstnode; i < j; i++) {
	    if (i < j - 1) {
		segmentlist[i * 2] = i;
		segmentlist[i * 2 + 1] = i + 1;
	    }
	    else {
		segmentlist[i * 2] = i;
		segmentlist[i * 2 + 1] = firstnode;
	    }
	    segments++;
	}
    }


    /****************************************************************/
    /*                Get area constraints                          */

    /****************************************************************/

    c = 0;
    while ((type = Vect_read_next_line(&Map, Points, Cats)) > 0) {
	if (type == GV_CENTROID && Cats->cat[0] > 0) {
	    xptr = Points->x;
	    yptr = Points->y;
	    regionlist[c * 2] = *xptr;
	    regionlist[c * 2 + 1] = *yptr;
	    for (i = 0; i < Cats->n_cats; i++) {
		Fi = Vect_get_field(&Map, Cats->field[i]);
		driver =
		    db_start_driver_open_database(Fi->driver, Fi->database);
		printf("select %s from %s where %s=%-10d\n", column->answer,
		       Fi->table, Fi->key, Cats->cat[i]);

		sprintf(buf, "select %s from %s where %s=%-10d\n",
			column->answer, Fi->table, Fi->key, Cats->cat[i]);
		db_init_string(&stmt);
		db_append_string(&stmt, buf);
		if (db_open_select_cursor
		    (driver, &stmt, &cursor, DB_SEQUENTIAL) != DB_OK)
		    G_fatal_error("Cannot open select cursor: '%s'",
				  db_get_string(&stmt));
		table = db_get_cursor_table(&cursor);
		col = db_get_table_column(table, 0);	/* first column   */
		ctype = db_sqltype_to_Ctype(db_get_column_sqltype(col));
		if (ctype != DB_C_TYPE_INT)
		    G_fatal_error("area constraint must be integer");

		dbvalue = db_get_column_value(col);
		/* fetch the data */
		count = 0;
		while (1) {
		    if (db_fetch(&cursor, DB_NEXT, &more) != DB_OK)
			return (-1);
		    if (!more)
			break;
		    /* somehow it didn't work with double val[c], so only int values are used */
		    if (count == 0)
			val[c] = db_get_value_int(dbvalue);
		    count++;
		}
		db_close_cursor(&cursor);
		db_free_string(&stmt);

		printf("c=%i, val[%i]=%i\n", c, c, val[c]);
		c++;
	    }
	}
    }
    Vect_close(&Map);
    /*printf("ocas 4\n"); */

    /************************************/
    /* Creating Triangle's data input : */

    /************************************/

    in.numberofpoints = j;
    in.numberofpointattributes = 0;

    in.pointlist = (REAL *) malloc(in.numberofpoints * 2 * sizeof(REAL));
    /* This is a really dirty way to do it */
    for (i = 0; i < j; i++) {
	for (of = 0; of < 2; of++) {
	    in.pointlist[i * 2 + of] = pointlist[i * 2 + of];
	}
    }

    in.numberofsegments = segments;
    in.segmentlist = (int *)malloc(in.numberofsegments * 2 * sizeof(int));
    for (i = 0; i < segments; i++) {
	for (of = 0; of < 2; of++) {
	    in.segmentlist[i * 2 + of] = segmentlist[i * 2 + of];
	    /*      printf("segmentlist[%i]=%i in.segmentlist[%i]=%i\n",i*2+of,segmentlist[i*2+of],i*2+of,in.segmentlist[i*2+of]);
	       }
	       printf("segment %i= %i--%i\n",i,in.segmentlist[i*2],in.segmentlist[i*2+1]);
	     */
	}
    }
    in.numberofregions = c;
    in.regionlist = (REAL *) malloc(in.numberofregions * 4 * sizeof(REAL));

    for (i = 0; i < in.numberofregions; i++) {
	in.regionlist[i * 4] = regionlist[i * 2];
	in.regionlist[i * 4 + 1] = regionlist[i * 2 + 1];
	in.regionlist[i * 4 + 2] = 0;
	in.regionlist[i * 4 + 3] = val[i];
	/*printf("val[%i]=%i\n",i,val[i]); */
    }
    /* For some reason Triangle doesn't like these lines */
    /* In case holes are present; so no holes!) */
    /* Tabernacle!
       if(h>0){
       in.numberofholes=h;
       printf("shouldn't be in...\n");
       in.holelist=(REAL *) malloc(in.numberofholes * 2 * sizeof(REAL));
       out.holelist= (int *) NULL;
       for(i=0;i<in.numberofholes;i++){
       for(of=0;of<2;of++){
       in.holelist[i*2+of]=holelist[i*2+of];
       }
       }
       }
     */

    /* variables need to be initialized for Triangle */
    in.numberofholes = 0;
    in.segmentmarkerlist = (int *)NULL;
    in.holelist = (REAL *) NULL;

    out.pointlist = (REAL *) NULL;
    out.trianglelist = (int *)NULL;
    out.segmentlist = (int *)NULL;
    out.edgelist = (int *)NULL;

    /* Triangulate the points: read and write a PSLG (p), number everything */
    /* from zero (z), create a quality mesh (q) and use area constraints (a) */
    /* voronoi polygons not needed, thus vorout== NULL */

    /* Use FLAGS for either constrained Delaunay, area constraints */
    printf("number of regions = %i\n", c);
    printf("calling triangle \n");

    /* 10/7/2009 Paolo Zatelli: avoids segmentation fault at lines 14133-14136 of triangle.c */
    /* due to non-null pointer; in.pointmarkerlist is never used in v.trivertex */
    in.pointmarkerlist = (int *)NULL;

    if (nomaxarea->answer)
	triangulate("pzqDBeQj", &in, &out, (struct triangulateio *)NULL);
    else
	triangulate("pzqDaBeQj", &in, &out, (struct triangulateio *)NULL);

    if (0 > Vect_open_new(&Map, output->answer, 0))
	G_fatal_error(_("Unable to create vector map %s"), output->answer);

    driver =
	db_start_driver_open_database(Fi->driver,
				      Vect_subst_var(Fi->database, &Map));

    if (driver == NULL)
	G_fatal_error(_("Cannot open database %s by driver %s"),
		      Vect_subst_var(Fi->database, &Map), Fi->driver);

    printf("driver= %s\n", Fi->driver);

    db_begin_transaction(driver);

    sprintf(buf, "create table %snodes (cat int)", output->answer);
    db_init_string(&stmt);
    db_append_string(&stmt, buf);
    printf("buf=%s\n", buf);

    if (db_execute_immediate(driver, &stmt) != DB_OK)
	G_fatal_error(_("Cannot create table %s"), db_get_string(&stmt));


    sprintf(buf, "%snodes", output->answer);
    Vect_map_add_dblink(&Map, 1, NULL, buf, "cat", Fi->database, Fi->driver);

    /* Writing the output to GRASS */

    /*********************/
    /* Writing NODES     */

    /*********************/
    for (i = 0; i < out.numberofpoints; i++) {
	Vect_reset_line(Points);
	Vect_reset_cats(Cats);
	x = out.pointlist[i * 2];
	y = out.pointlist[i * 2 + 1];
	Vect_append_point(Points, x, y, 0);
	Vect_cat_set(Cats, 1, i + 1);
	Vect_write_line(&Map, GV_POINT, Points, Cats);
	sprintf(buf, "insert into %snodes values(%i)", output->answer, i + 1);
	db_init_string(&stmt);
	db_append_string(&stmt, buf);
	if (db_execute_immediate(driver, &stmt) != DB_OK)
	    G_fatal_error(_("Cannot add values to table %snodes"),
			  output->answer);
    }

    /*********************/
    /* Writing BOUNDARIES */

    /*********************/
    for (i = 0; i < out.numberofedges; i++) {
	Vect_reset_line(Points);
	Vect_reset_cats(Cats);
	for (of = 0; of < 2; of++) {
	    j = out.edgelist[i * 2 + of];
	    x = out.pointlist[j * 2];
	    y = out.pointlist[j * 2 + 1];
	    Vect_append_point(Points, x, y, 0);
	    Vect_cat_set(Cats, 1, i + 1);
	    Vect_write_line(&Map, GV_BOUNDARY, Points, Cats);
	}
    }

    /*********************/
    /* Writing CENTROIDS */

    /*********************/
    sprintf(buf, "create table %stricentr (cat int)", output->answer);
    db_init_string(&stmt);
    db_append_string(&stmt, buf);

    if (db_execute_immediate(driver, &stmt) != DB_OK)
	G_fatal_error(_("Cannot create table %s"), db_get_string(&stmt));

    sprintf(buf, "%stricentr", output->answer);
    Vect_map_add_dblink(&Map, 2, NULL, buf, "cat", Fi->database, Fi->driver);

    for (i = 0; i < out.numberoftriangles; i++) {
	Vect_reset_line(Points);
	Vect_reset_cats(Cats);
	left = out.trianglelist[i * 3];
	center = out.trianglelist[i * 3 + 1];
	right = out.trianglelist[i * 3 + 2];

	xleft = out.pointlist[left * 2];
	yleft = out.pointlist[left * 2 + 1];
	xcenter = out.pointlist[center * 2];
	ycenter = out.pointlist[center * 2 + 1];
	xright = out.pointlist[right * 2];
	yright = out.pointlist[right * 2 + 1];

	xm1 = xleft + ((xcenter - xleft) / 2);
	ym = yleft + ((ycenter - yleft) / 2);
	m1 = (yright - ym) / (xright - xm1);
	b1 = yright - (m1 * xright);

	xm2 = xcenter + ((xright - xcenter) / 2);
	ym = ycenter + ((yright - ycenter) / 2);
	m2 = (yleft - ym) / (xleft - xm2);
	b2 = yleft - (m2 * xleft);
	/* in case a median is a vertical line */
	if ((xright - xm1) == 0 || (xleft - xm2) == 0) {
	    if ((xright - xm1) == 0) {
		x = xm1;
		y = (m2 * x) + b2;
	    }
	    else {
		x = xm2;
		y = (m1 * x) + b1;
	    }
	}
	else {
	    x = (b2 - b1) / (m1 - m2);
	    y = (m1 * x) + b1;
	}

	Vect_append_point(Points, x, y, 0);
	Vect_cat_set(Cats, 2, i + 1);
	Vect_write_line(&Map, GV_CENTROID, Points, Cats);
	sprintf(buf, "insert into %stricentr values(%i)", output->answer,
		i + 1);
	db_init_string(&stmt);
	db_append_string(&stmt, buf);
	if (db_execute_immediate(driver, &stmt) != DB_OK) {
	    G_fatal_error(_("Cannot add values to table %stricentr"),
			  output->answer);
	}
    }
    db_close_database(driver);
    db_shutdown_driver(driver);
    Vect_build_partial(&Map, GV_BUILD_NONE);
    Vect_build(&Map);

    Vect_close(&Map);

    return (EXIT_SUCCESS);
}
