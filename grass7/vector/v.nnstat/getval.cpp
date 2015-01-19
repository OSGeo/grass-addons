#include "local_proto.h"

extern "C" {
  /* get array of values from attribute column (function based on part of v.buffer2 (Radim Blazek, Rosen Matev)) */
  double *get_col_values(struct Map_info *map, int field, const char *column)
  {
    int i, nrec, ctype;
    struct field_info *Fi;

    dbCatValArray cvarr;
    dbDriver *Driver;

    double *values, *vals;

    db_CatValArray_init(&cvarr);	/* array of categories and values initialised */

    Fi = Vect_get_field(map, field);	/* info about call of DB */
    if (Fi == NULL)
      G_fatal_error(_("Database connection not defined for layer %d"),
		    field);
    Driver = db_start_driver_open_database(Fi->driver, Fi->database);	/* started connection to DB */
    if (Driver == NULL)
      G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
		    Fi->database, Fi->driver);

    /* Note do not check if the column exists in the table because it may be expression */

    /* TODO: only select values we need instead of all in column */

    /* Select pairs key/value to array, values are sorted by key (must be integer) */
    nrec =
      db_select_CatValArray(Driver, Fi->table, Fi->key, column, NULL,
			    &cvarr);
    if (nrec < 0)
      G_fatal_error(_("Unable to select data from table <%s>"), Fi->table);
    G_message(_("Reading elevations from attribute table: %d records selected"), nrec);
    ctype = cvarr.ctype;
    
    db_close_database_shutdown_driver(Driver);

    values = (double *) G_malloc(cvarr.n_values * sizeof(double));
    vals = &values[0];

    for (i = 0; i < cvarr.n_values; i++) {
      if (ctype == DB_C_TYPE_INT) {
	*vals = (double) cvarr.value[i].val.i;
      }
      if (ctype == DB_C_TYPE_DOUBLE) {
	*vals = cvarr.value[i].val.d;
      }
      if (ctype == DB_C_TYPE_STRING) {
	G_fatal_error(_("The column must be numeric..."));
      }
      vals++;
    }

    return values;
  }

/* get coordinates of input points */
  void read_points(struct Map_info *map, int field, struct nna_par *xD,
		const char *zcol, struct points *point)
  {
    int ctrl, n, type, nskipped, pass;

    struct line_pnts *Points;	/* structures to hold line *Points (map) */
    double *rx, *ry, *rz;
    double *z_attr, *z;

    Points = Vect_new_line_struct();
    n = point->n = Vect_get_num_primitives(map, GV_POINT);	/* topology required */
    point->r = (double *) G_malloc(n*3 * sizeof(double));

    rx = &point->r[0];
    ry = &point->r[1];
    rz = &point->r[2];

    /* Get 3rd coordinate of 2D points from attribute column -> 3D interpolation */
    if (xD->v3 == FALSE && zcol != NULL) {
      xD->zcol = (char *) G_malloc(strlen(zcol) * sizeof(char));
      strcpy(xD->zcol, zcol);
      z_attr = get_col_values(map, field, zcol);
      z = &z_attr[0];
    }
    else {
      xD->zcol = NULL;
    }
            
    nskipped = ctrl = pass = 0;
    
    while (TRUE) {
      type = Vect_read_next_line(map, Points, NULL);
      if (type == -1)
	G_fatal_error(_("Unable to read vector map"));
      if (type == -2)
	break;

      if (type != GV_POINT) {
	nskipped++;
	continue;
      }

      *rx = Points->x[0];
      *ry = Points->y[0];
      
      // 3D points or 2D points without attribute column -> 2D interpolation
      if (xD->zcol == NULL) {
	if (xD->v3 == TRUE && xD->i3 == FALSE) {
	  *rz = 0.;
	}
	else {
	  *rz = Points->z[0];
	}
      }
      else {
	*rz = *z;
	z++;
      }

      /* Find extends */	
      if (ctrl == 0) {
	point->r_min = point->r_max = triple(*rx, *ry, *rz);
      }
      else {
	point->r_min = triple(MIN(*point->r_min, *rx), MIN(*(point->r_min+1), *ry), MIN(*(point->r_min+2), *rz));
	point->r_max = triple(MAX(*point->r_max, *rx), MAX(*(point->r_max+1), *ry), MAX(*(point->r_max+2), *rz));
      }
      if (ctrl < point->n - 1) {
	rx += 3;
	ry += 3;
	rz += 3;
      }
      ctrl++;
    }

    if (nskipped > 0)
      G_warning(_("%d features skipped, only points are accepted"),
		nskipped);

    Vect_destroy_line_struct(Points);

    if (ctrl <= 0)
      G_fatal_error(_("Unable to read coordinates of point layer"));
  }
} // end extern "C"
