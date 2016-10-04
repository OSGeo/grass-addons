#include "local_proto.h"

#ifndef MAX
#define MIN(a,b)      ((a<b) ? a : b)
#define MAX(a,b)      ((a>b) ? a : b)
#endif

/* get array of values from attribute column (function based on part of v.buffer2 (Radim Blazek, Rosen Matev)) */
double *get_col_values(struct Map_info *map, struct int_par *xD,
                       struct points *pnts, int field, const char *column,
                       int detrend)
{
    struct select *in_reg = &pnts->in_reg;

    int i, n, nrec, ctype;
    struct field_info *Fi;

    dbCatValArray cvarr;
    dbDriver *Driver;

    int *index;
    double *values, *vals;

    int save;

    if (xD == NULL) {
        save = 0;
    }
    else {
        save = 1;
    }

    G_message(_("Reading values from attribute column <%s>..."), column);

    db_CatValArray_init(&cvarr);        /* array of categories and values initialised */
    Fi = Vect_get_field(map, field);    /* info about call of DB */
    if (Fi == NULL) {
        if (save == 1 && xD->report.write2file == TRUE) {       // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Database connection not defined for layer %d"),
                      field);
    }

    Driver = db_start_driver_open_database(Fi->driver, Fi->database);   /* started connection to DB */
    if (Driver == NULL) {
        if (save == 1 && xD->report.write2file == TRUE) {       // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);
    }

    /* Note do not check if the column exists in the table because it may be expression */

    /* TODO: only select values we need instead of all in column */

    /* Select pairs key/value to array, values are sorted by key (must be integer) */
    nrec =
        db_select_CatValArray(Driver, Fi->table, Fi->key, column, NULL,
                              &cvarr);
    if (nrec < 0) {
        if (save == 1 && xD->report.write2file == TRUE) {       // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Unable to select data from table <%s>"), Fi->table);
    }

    ctype = cvarr.ctype;
    if (ctype != DB_C_TYPE_INT && ctype != DB_C_TYPE_DOUBLE) {
        if (save == 1 && xD->report.write2file == TRUE) {       // close report file
            fprintf(xD->report.fp,
                    "Error (see standard output). Process killed...");
            fclose(xD->report.fp);
        }
        G_fatal_error(_("Column must be numeric"));
    }

    db_close_database_shutdown_driver(Driver);
    G_free(Fi);

    /* Output cats/values list */
    switch (in_reg->out) {
    case 0:
        index = NULL;
        n = cvarr.n_values;
        break;
    default:
        index = &in_reg->indices[0];
        n = in_reg->n;
        break;
    }

    values = (double *)G_malloc(n * sizeof(double));
    vals = &values[0];

    for (i = 0; i < n; i++) {
        /* TODO: Only for point data:
         * - store indexes of skipped points in read_points and compare them with database
         */
        if (index == NULL || (index != NULL && *index == i)) {
            if (ctype == DB_C_TYPE_INT)
                *vals = (double)cvarr.value[i].val.i;
            else if (ctype == DB_C_TYPE_DOUBLE) {
                *vals = cvarr.value[i].val.d;
            }
            vals++;
            if (index != NULL)
                index++;
        }
    }

    if (detrend == 1) {
        double *x, *y, *z;

        x = (double *)G_malloc(n * sizeof(double));
        y = (double *)G_malloc(n * sizeof(double));
        z = (double *)G_malloc(n * sizeof(double));

        mat_struct *A, *gR, *T, *res;

        x = &pnts->r[0];
        y = &pnts->r[1];
        z = &pnts->r[2];
        vals = &values[0];
        // Number of columns of design matrix A
        A = G_matrix_init(n, 2, n);     // initialise design matrix, normal grav: 7
        gR = G_matrix_init(n, 1, n);    // initialise vector of observations

        for (i = 0; i < n; i++) {
            G_matrix_set_element(A, i, 0, *x);
            G_matrix_set_element(A, i, 1, *y);
            G_matrix_set_element(gR, i, 0, *vals);
            x += 3;
            y += 3;
            z += 3;
            vals++;
        }
        T = LSM(A, gR);         // Least Square Method
        res = G_matrix_product(A, T);

        FILE *fp;

        x = &pnts->r[0];
        y = &pnts->r[1];
        z = &pnts->r[2];
        fp = fopen("trend.txt", "w");

        vals = &values[0];
        double *resid;

        resid = &res->vals[0];
        for (i = 0; i < n; i++) {
            *vals = *vals - *resid;
            fprintf(fp, "%f %f %f %f\n", *x, *y, *z, *vals);
            x += 3;
            y += 3;
            z += 3;
            vals++;
            resid++;
        }
        fclose(fp);
        //G_debug(0,"a=%f b=%f c=%f d=%f", T->vals[0], T->vals[1], T->vals[2], T->vals[3]);
        pnts->trend = T;
    }

    if (xD->report.write2file && xD->phase == 0) {
        write2file_values(&xD->report, column);
        test_normality(n, values, &xD->report);
    }

    db_CatValArray_free(&cvarr);        // free memory of the array of categories and values

    return values;
}

/* get coordinates of input points */
void read_points(struct Map_info *map, struct reg_par *reg,
                 struct points *point, struct int_par *xD, const char *zcol,
                 int field, struct write *report)
{
    int type;                   // check elements of vector layer
    int i3 = xD->i3;            // 2D / 3D interpolation
    int n;                      // # of all elements in vector layer
    int nskipped;               // # of skipped elements (all except points)
    int n_in_reg = 0;           // # of points within a region
    int out_reg = 0;            // # of points out of region
    double *z_attr;             // vertical coordinate from attribute value

    struct line_pnts *Points;   // structures to hold line *Points (map)

    // create spatial index R-tree
    point->Rtree_hz = RTreeCreateTree(-1, 0, 2);        // create 2D spatial index
    if (i3 == TRUE) {           // 3D:
        point->R_tree = RTreeCreateTree(-1, 0, 3);      // create 3D spatial index
        point->Rtree_vert = RTreeCreateTree(-1, 0, 1);  // create 1D spatial index
    }

    int sid = 0;                // id of the rectangle (will be increased by 1)

    double *rx, *ry, *rz;       // pointers to coordinates
    int ind = 0;                // index of the point     
    int *indices;               // indices of the points within the region
    int *index;                 // pointer to the vector of indices

    G_message(_("Reading coordinates..."));

    Points = Vect_new_line_struct();    // Make point structure  
    n = Vect_get_num_primitives(map, GV_POINT); // Number of points - topology required

    point->r = (double *)G_malloc(n * 3 * sizeof(double));      // coords: x0 y0 z0 ... xn yn zn
    indices = (int *)G_malloc(n * sizeof(int)); // indices of pts within region

    point->r_min = (double *)G_malloc(3 * sizeof(double));      // minimum
    point->r_max = (double *)G_malloc(3 * sizeof(double));      // maximum

    rx = &point->r[0];          // pointer to x coordinate
    ry = &point->r[1];          // pointer to y coordinate
    rz = &point->r[2];          // pointer to z coordinate
    index = &indices[0];        // pointer to indices

    // Get 3rd coordinate of 2D points from attribute column -> 3D interpolation
    if (xD->v3 == FALSE && zcol != NULL) {
        z_attr = get_col_values(map, NULL, point, field, zcol, FALSE);
    }

    nskipped = 0;               // # of skipped elements (lines, areas)

    // Read points and set them into the structures
    while (TRUE) {
        type = Vect_read_next_line(map, Points, NULL);
        if (type == -1) {
            if (report->write2file == TRUE) {   // close report file
                fprintf(report->fp,
                        "Error (see standard output). Process killed...");
                fclose(report->fp);
            }
            G_fatal_error(_("Unable to read vector map"));
        }
        if (type == -2) {
            break;
        }

        // skip everything except points
        if (type != GV_POINT) {
            nskipped++;
            continue;
        }

        if (isnan(Points->x[0]) || isnan(Points->y[0]) || isnan(Points->z[0])) {
            if (report->write2file == TRUE) {   // close report file
                fprintf(report->fp,
                        "Error (see standard output). Process killed...");
                fclose(report->fp);
            }
            G_fatal_error(_("Input coordinates must be a number. Check point no. %d..."),
                          ind);
        }

        // take every point in region...
        if ((reg->west <= Points->x[0] && Points->x[0] <= reg->east) &&
            (reg->south <= Points->y[0] && Points->y[0] <= reg->north)) {
            *rx = Points->x[0]; // set up x coordinate
            *ry = Points->y[0]; // set up y coordinate

            insert_rectangle(2, sid, point);    // R-tree node 2D (2D and 3D kriging)

            if (i3 == TRUE) {   // 3D interpolation:
                if (reg->bot <= Points->z[0] && Points->z[0] <= reg->top) {
                    if (zcol == NULL) { // 3D layer:
                        *rz = Points->z[0];     // set up z coordinate

                        if (*rz != Points->z[0]) {
                            if (report->write2file == TRUE) {   // close report file
                                fprintf(report->fp,
                                        "Error (see standard output). Process killed...");
                                fclose(report->fp);
                            }
                            G_fatal_error(_("Error reading input coordinates z..."));
                        }
                    }
                    else {      // 2D layer with z-column:
                        *rz = *z_attr;  // set up x coordinate
                    }           // end else (2,5D layer)

                    insert_rectangle(3, sid, point);    // R-tree node 3D (just 3D kriging)
                    insert_rectangle(1, sid, point);    // R-tree node 1D (just 3D kriging)
                }               // end if rb, rt

                else {          // point is out of region:
                    goto out_of_region;
                }
            }                   // end if 3D interpolation

            else {              // 2D interpolation:
                *rz = 0.;       // set up z coordinate
            }

            // Find extends   
            if (n_in_reg == 0) {
                triple(*rx, *ry, *rz, point->r_min);
                triple(*rx, *ry, *rz, point->r_max);
            }

            else {
                triple(MIN(*point->r_min, *rx), MIN(*(point->r_min + 1), *ry),
                       MIN(*(point->r_min + 2), *rz), point->r_min);
                triple(MAX(*point->r_max, *rx), MAX(*(point->r_max + 1), *ry),
                       MAX(*(point->r_max + 2), *rz), point->r_max);
            }                   // end else (extent test)

            n_in_reg++;         // # of points in region 
            *index = ind;       // store index of point within the region
            index++;            // go to next index

            rx += 3;            // go to new x coordinate
            ry += 3;            // go to new y coordinate
            rz += 3;            // go to new z coordinate

            sid++;              // go to new ID for spatial indexing

            goto finish;
        }                       // end in region

      out_of_region:
        out_reg++;
        continue;

      finish:
        if (zcol != NULL) {
            z_attr++;
        }
        ind++;
    }                           // end while (TRUE)

    point->in_reg.total = n;
    point->in_reg.n = n_in_reg;
    point->in_reg.out = out_reg;
    point->n = n_in_reg;

    point->in_reg.indices = (int *)G_malloc(n_in_reg * sizeof(int));
    memcpy(point->in_reg.indices, indices, n_in_reg * sizeof(int));
    G_free(indices);

    if (nskipped > 0) {
        G_warning(_("%d features skipped, only points are accepted"),
                  nskipped);
    }

    Vect_destroy_line_struct(Points);

    if (n_in_reg == 0) {
        if (report->write2file == TRUE) {       // close report file
            fprintf(report->fp,
                    "Error (see standard output). Process killed...");
            fclose(report->fp);
        }
        G_fatal_error(_("Unable to read coordinates of point layer (all points are out of region)"));
    }

    if (out_reg > 0) {
        G_message(_("Unused points: %d (out of region)"), out_reg);
    }

    if (xD->report.write2file == TRUE && xD->phase == 0) {      // initial phase:
        write2file_vector(xD, point);   // describe properties
    }
}

void get_region_pars(struct int_par *xD, struct reg_par *reg)
{
    /* Get extent and resolution of output raster 2D/3D */
    if (xD->i3 == FALSE) {      /* 2D region */
        /* Get database region parameters */
        Rast_get_window(&reg->reg_2d);  /* stores the current default window in region */
        reg->west = reg->reg_2d.west;
        reg->east = reg->reg_2d.east;
        reg->north = reg->reg_2d.north;
        reg->south = reg->reg_2d.south;
        reg->ew_res = reg->reg_2d.ew_res;
        reg->ns_res = reg->reg_2d.ns_res;
        reg->nrows = reg->reg_2d.rows;
        reg->ncols = reg->reg_2d.cols;
        reg->ndeps = 1;
    }
    if (xD->i3 == TRUE) {       /* 3D region */
        Rast3d_init_defaults();
        /* Get database region parameters */
        Rast3d_get_window(&reg->reg_3d);        /* stores the current default window in region */
        if (reg->reg_3d.bottom == 0 &&
            (reg->reg_3d.tb_res == 0 || reg->reg_3d.depths == 0)) {
            if (xD->report.write2file == TRUE) {        // close report file
                fprintf(xD->report.fp,
                        "Error (see standard output). Process killed...");
                fclose(xD->report.fp);
            }
            G_fatal_error
                ("To process 3D interpolation, please set 3D region settings.");
        }
        reg->west = reg->reg_3d.west;
        reg->east = reg->reg_3d.east;
        reg->north = reg->reg_3d.north;
        reg->south = reg->reg_3d.south;
        reg->bot = reg->reg_3d.bottom;  /* output 3D raster */
        reg->top = reg->reg_3d.top;     /* output 3D raster */
        reg->ew_res = reg->reg_3d.ew_res;
        reg->ns_res = reg->reg_3d.ns_res;
        reg->bt_res = reg->reg_3d.tb_res;
        reg->nrows = reg->reg_3d.rows;
        reg->ncols = reg->reg_3d.cols;
        reg->ndeps = xD->i3 == TRUE ? reg->reg_3d.depths : 1;   /* 2D/3D interpolation */
    }
    reg->nrcd = reg->nrows * reg->ncols * reg->ndeps;   /* number of cells */
}

// read values from temporary files
void read_tmp_vals(const char *file_name, struct parameters *var_par,
                   struct int_par *xD)
{
    FILE *fp;

    int j, nLag_vert;
    double lag_vert, max_dist_vert;
    double *v_elm, *g_elm;
    double sill_hz, sill_vert;


    fp = fopen(file_name, "r");
    if (fp == NULL) {
        G_fatal_error(_("Temporary file <%s> is missing, please repeat an initial phase..."),
                      file_name);
    }

    else {                      // file exists:
        int i, type;
        int nLag;
        double lag, max_dist, td_hz, sill;
        double *h_elm, *gamma;
        int file, file_length;

        for (i = 0; i < 2; i++) {
            if (fscanf(fp, "%d", &file_length) == 0) {  // filename length
                G_fatal_error(_("Nothing to scan..."));
            }
            if (file_length > 3) {
                if (fscanf(fp, "%d", &file) == 0) {
                    G_fatal_error(_("Nothing to scan..."));
                }
                if (file == 9) {        // filetype code (9 - report, 8 - crossval)
                    xD->report.name =
                        (char *)G_malloc(file_length * sizeof(char));
                    if (fscanf(fp, "%s", xD->report.name) == 0) {       // filename
                        G_fatal_error(_("Nothing to scan..."));
                    }
                    continue;
                }
                else if (file == 8) {
                    xD->crossvalid.name =
                        (char *)G_malloc(file_length * sizeof(char));
                    if (fscanf(fp, "%s", xD->crossvalid.name) == 0) {
                        G_fatal_error(_("Nothing to scan..."));
                    }
                    continue;
                }
            }
            else {
                type = file_length;
                goto no_file;
            }
        }                       // todo: test without report and crossval

        if (fscanf(fp, "%d", &type) == 0) {     // read type
            G_fatal_error(_("Nothing to scan..."));
        }

      no_file:

        switch (type) {
        case 2:                // bivariate variogram
            var_par->type = type;
            if (fscanf
                (fp, "%d %lf %lf %d %lf %lf %lf", &nLag_vert, &lag_vert,
                 &max_dist_vert, &nLag, &lag, &max_dist, &td_hz) < 7) {
                G_fatal_error(_("Nothing to scan..."));
            }

            var_par->horizontal.h = (double *)G_malloc(nLag * sizeof(double));
            h_elm = &var_par->horizontal.h[0];
            for (i = 0; i < nLag; i++) {
                if (fscanf(fp, "%lf", h_elm) == 0) {
                    G_fatal_error(_("Nothing to scan..."));
                }
                h_elm++;
            }

            var_par->vertical.h =
                (double *)G_malloc(nLag_vert * sizeof(double));
            v_elm = &var_par->vertical.h[0];
            for (i = 0; i < nLag_vert; i++) {
                if (fscanf(fp, "%lf", v_elm) == 0) {
                    G_fatal_error(_("Nothing to scan..."));
                }
                v_elm++;
            }

            var_par->gamma = G_matrix_init(nLag, nLag_vert, nLag);
            g_elm = &var_par->gamma->vals[0];
            for (i = 0; i < nLag_vert; i++) {
                for (j = 0; j < nLag; j++) {
                    if (fscanf(fp, "%lf", g_elm) == 0) {
                        G_fatal_error(_("Nothing to scan..."));
                    }
                    g_elm++;
                }
            }

            if (fscanf(fp, "%lf %lf", &sill_hz, &sill_vert) < 2) {
                G_fatal_error(_("Nothing to scan..."));
            }

            var_par->vertical.nLag = nLag_vert;
            var_par->vertical.lag = lag_vert;
            var_par->vertical.max_dist = max_dist_vert;
            var_par->vertical.sill = sill_vert;

            var_par->horizontal.nLag = nLag;
            var_par->horizontal.lag = lag;
            var_par->horizontal.max_dist = max_dist;
            var_par->horizontal.sill = sill_hz;
            break;

        default:
            if (type == 3) {    // anisotropic variogram:
                if (fscanf(fp, "%lf", &xD->aniso_ratio) == 0) { // anisotropic ratio
                    G_fatal_error(_("Nothing to scan..."));
                }
            }

            if (fscanf(fp, "%d %lf %lf", &nLag, &lag, &max_dist) < 3) {
                G_fatal_error(_("Nothing to scan..."));
            }

            if (type != 1) {
                if (fscanf(fp, "%lf", &td_hz) == 0) {
                    G_fatal_error(_("Nothing to scan..."));
                }
            }

            var_par->h = (double *)G_malloc(nLag * sizeof(double));
            h_elm = &var_par->h[0];

            var_par->gamma = G_matrix_init(nLag, 1, nLag);
            gamma = &var_par->gamma->vals[0];

            for (i = 0; i < nLag; i++) {
                if (fscanf(fp, "%lf %lf", h_elm, gamma) < 2) {
                    G_fatal_error(_("Nothing to scan..."));
                }
                h_elm++;
                gamma++;
            }

            if (fscanf(fp, "%lf", &sill) == 0) {
                G_fatal_error(_("Nothing to scan..."));
            }
            var_par->sill = sill;
            break;
        }

        if (type != 2) {
            var_par->type = type;
            var_par->nLag = nLag;
            var_par->lag = lag;
            var_par->max_dist = max_dist;
            var_par->td = td_hz;
        }
    }
    fclose(fp);

    if (xD->phase == 2) {
        remove(file_name);
    }
}
