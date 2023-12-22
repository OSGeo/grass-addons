#include "local_proto.h"

/* get array of values from attribute column (function based on part of
 * v.buffer2 (Radim Blazek, Rosen Matev)) */
double *get_col_values(struct Map_info *map, int field, const char *column)
{
    int i, nrec, ctype;
    struct field_info *Fi;

    dbCatValArray cvarr;
    dbDriver *Driver;

    double *values, *vals;

    db_CatValArray_init(
        &cvarr); /* array of categories and values initialised */

    Fi = Vect_get_field(map, field); /* info about call of DB */
    if (Fi == NULL)
        G_fatal_error(_("Database connection not defined for layer %d"), field);
    Driver = db_start_driver_open_database(
        Fi->driver, Fi->database); /* started connection to DB */
    if (Driver == NULL)
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);

    /* Note do not check if the column exists in the table because it may be
     * expression */

    /* TODO: only select values we need instead of all in column */

    /* Select pairs key/value to array, values are sorted by key (must be
     * integer) */
    nrec =
        db_select_CatValArray(Driver, Fi->table, Fi->key, column, NULL, &cvarr);
    if (nrec < 0)
        G_fatal_error(_("Unable to select data from table <%s>"), Fi->table);
    G_message(_("Reading elevations from attribute table: %d records selected"),
              nrec);
    ctype = cvarr.ctype;

    db_close_database_shutdown_driver(Driver);

    values = (double *)G_malloc(cvarr.n_values * sizeof(double));
    vals = &values[0];

    for (i = 0; i < cvarr.n_values; i++) {
        if (ctype == DB_C_TYPE_INT) {
            *vals = (double)cvarr.value[i].val.i;
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
                 const char *zcol, struct points *pnts)
{
    int ctrl, n, type, nskipped, pass;

    struct line_pnts *Points; // structures to hold line *Points (map)
    double *rx, *ry, *rz;     // pointers to the coordinates
    double *z_attr, *z;       // pointers to attribute z values

    Points = Vect_new_line_struct();
    n = pnts->n =
        Vect_get_num_primitives(map, GV_POINT); /* topology required */
    pnts->r = (double *)G_malloc(n * 3 * sizeof(double));

    rx = &pnts->r[0];
    ry = &pnts->r[1];
    rz = &pnts->r[2];

    pnts->R_tree = create_spatial_index(xD); // create spatial index (R-tree)

    /* Get 3rd coordinate of 2D points from attribute column -> 3D interpolation
     */
    if (xD->v3 == FALSE &&
        zcol != NULL) { // 2D input layer with z attribute column:
        xD->zcol = (char *)G_malloc(strlen(zcol) * sizeof(char));
        strcpy(xD->zcol, zcol);
        z_attr = get_col_values(map, field, zcol); // read attribute z values
        z = &z_attr[0];
    }
    else {
        xD->zcol = NULL;
    }

    nskipped = ctrl = pass = 0;

    while (TRUE) {
        type = Vect_read_next_line(map, Points, NULL);
        if (type == -1) {
            G_fatal_error(_("Unable to read vector map"));
        }
        if (type == -2) {
            break;
        }

        if (type != GV_POINT) {
            nskipped++;
            continue;
        }

        *rx = Points->x[0];
        *ry = Points->y[0];

        // 3D points or 2D points without attribute column -> 2D interpolation
        if (xD->zcol == NULL) { // z attribute column not available:
            if (xD->v3 == TRUE && xD->i3 == FALSE) { // 2D NNA:
                *rz = 0.;
            }
            else { // 3D NNA:
                *rz = Points->z[0];
            }
        }
        else { // z attribute column available:
            *rz = *z;
            z++;
        }
        insert_rectangle(xD->i3, ctrl,
                         pnts); // insert rectangle into spatial index

        /* Find extends */
        if (ctrl == 0) {
            pnts->r_min = pnts->r_max = triple(*rx, *ry, *rz);
        }
        else {
            pnts->r_min =
                triple(MIN(*pnts->r_min, *rx), MIN(*(pnts->r_min + 1), *ry),
                       MIN(*(pnts->r_min + 2), *rz));
            pnts->r_max =
                triple(MAX(*pnts->r_max, *rx), MAX(*(pnts->r_max + 1), *ry),
                       MAX(*(pnts->r_max + 2), *rz));
        }
        if (ctrl < pnts->n - 1) {
            rx += 3;
            ry += 3;
            rz += 3;
        }
        ctrl++;
    }

    if (nskipped > 0) {
        G_warning(_("%d features skipped, only points are accepted"), nskipped);
    }

    Vect_destroy_line_struct(Points);

    if (ctrl <= 0) {
        G_fatal_error(_("Unable to read coordinates of point layer"));
    }

    // Compute maximum distance of the point sample
    double dx = pnts->r_max[0] - pnts->r_min[0];
    double dy = pnts->r_max[1] - pnts->r_min[1];
    double dz = pnts->r_max[2] - pnts->r_min[2];

    pnts->max_dist = xD->i3 == TRUE ? sqrt(dx * dx + dy * dy + dz * dz)
                                    : sqrt(dx * dx + dy * dy);

    G_message(_("Input coordinates have been read..."));

    return;
}
