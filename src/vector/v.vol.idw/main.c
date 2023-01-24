/****************************************************************************
 *
 * MODULE:       v.to.rast3
 * AUTHOR(S):    Original s.to.rast3: Jaro Hofierka, Geomodel s.r.o. (original
 *               contributor) 3/2015 Upgrade to GRASS GIS 7 by Noortheen Raja J
 * PURPOSE:      Converts vector points to 3D raster
 * COPYRIGHT:    (C) 1999-2015 by the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster3d.h>
#include <grass/vector.h>
#include <grass/dbmi.h>

int npts = 0, npoints_alloc = 0, search_points = 12, nsearch;
void newpoint(double, double, double, double);

struct Point {
    double w, z, east, north;
    double dist;
};
struct Point *points = NULL;
struct Point *list;

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *input, *output, *field, *column, *npoints;
    int nfield;
    RASTER3D_Region region;

    struct Map_info InMap; /*input map*/
    struct line_pnts *Points;
    struct line_cats *Cats;
    RASTER3D_Map *map3d = NULL;
    float *data, value;
    int lev, col, row, Nc, Nr, Nl, sz, i, n, max, cnt, current_row,
        current_depth;
    double x, y, z, w, lev_res, dx, dy, dz, dist, maxdist, sum1, sum2;

    int nrec, ctype, cat;

    struct field_info *Fi;
    dbDriver *Driver;
    dbCatValArray cvarr;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("Volume"));
    G_add_keyword(_("voxel"));
    G_add_keyword(_("interpolation"));
    G_add_keyword(_("IDW"));
    module->description = _("Interpolates point data to a 3D raster map using "
                            "Inverse Distance Weighting (IDW) algorithm.");

    input = G_define_standard_option(G_OPT_V_INPUT);
    input->required = YES;
    input->label = _("Name of input 3D vector points map");
    input->description = NULL;

    field = G_define_standard_option(G_OPT_V_FIELD);
    field->required = NO;
    field->label =
        _("Number of vector layer field attribute to use for calculation");
    field->description = NULL;

    output = G_define_standard_option(G_OPT_R3_OUTPUT);
    output->key = "output";
    output->required = YES;
    output->description = _("Name for output 3D raster map");

    column = G_define_standard_option(G_OPT_DB_COLUMN);
    column->required = YES;
    column->description =
        _("Name of attribute column (data type must be numeric)");

    npoints = G_define_option();
    npoints->key = "npoints";
    npoints->key_desc = "count";
    npoints->type = TYPE_INTEGER;
    npoints->required = YES;
    npoints->description = "Number of interpolation points";
    npoints->answer = "12";

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (G_legal_filename(output->answer) < 0)
        G_fatal_error(_("%s=%s - illegal name\n"), output->key, output->answer);

    if (sscanf(npoints->answer, "%d", &search_points) != 1 ||
        search_points < 1) {
        G_usage();
        G_fatal_error(_("Illegal number (%s) of interpolation points"),
                      npoints->answer);
    }

    list = (struct Point *)G_calloc(search_points, sizeof(struct Point));

    Vect_set_open_level(1);
    if (Vect_open_old2(&InMap, input->answer, "", field->answer) < 0)
        G_fatal_error(_("Unable to open vector map <%s>"), input->answer);

    if (!Vect_is_3d(&InMap))
        G_fatal_error(_("Vector is not 3D"));

    nfield = Vect_get_field_number(&InMap,
                                   field->answer); /*layer number;mostly one*/

    db_CatValArray_init(&cvarr);
    Fi = Vect_get_field(&InMap, nfield); /*The particular level of layer*/

    if (Fi == NULL)
        G_fatal_error(_("Database connection not defined for layer <%s>"),
                      field->answer);

    Driver = db_start_driver_open_database(Fi->driver, Fi->database);
    if (Driver == NULL)
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);
    db_set_error_handler_driver(Driver);

    /* Note: do not check if the column exists in the table because it may be
     * expression */

    nrec = db_select_CatValArray(Driver, Fi->table, Fi->key, column->answer,
                                 NULL, &cvarr); /*Number of selected records*/
    G_debug(2, "nrec = %d", nrec);
    if (nrec < 0)
        G_fatal_error(_("Unable to select data from table"));

    ctype = cvarr.ctype;
    if (ctype == -1)
        G_fatal_error(_("Cannot read column type of smooth column"));
    if (ctype == DB_C_TYPE_DATETIME)
        G_fatal_error(
            _("Column type of smooth column (datetime) is not supported"));
    if (ctype != DB_C_TYPE_INT && ctype != DB_C_TYPE_DOUBLE)
        G_fatal_error(_("Column type not supported"));

    db_close_database_shutdown_driver(Driver);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    Vect_rewind(&InMap);
    while (1) {
        int ival, type, ret;
        if (-1 == (type = Vect_read_next_line(&InMap, Points, Cats)))
            G_fatal_error(_("Unable to read vector map"));

        if (type == -2)
            break; /* EOF */

        if (!(type & GV_POINTS))
            continue;

        Vect_cat_get(Cats, 1, &cat);
        if (cat < 0) {
            G_warning(_("Point without category"));
            continue;
        }

        x = Points->x[0];
        y = Points->y[0];
        z = Points->z[0];
        if (ctype == DB_C_TYPE_INT) {
            ret = db_CatValArray_get_value_int(&cvarr, cat, &ival);
            w = ival;
        }
        else {
            ret = db_CatValArray_get_value_double(&cvarr, cat, &w);
        }                     /*ret will be 0 if completed successfully*/
        newpoint(w, z, x, y); /*adding the each point to the points array*/
    }
    Vect_close(&InMap);
    /*Terminate if the vector map is empty*/
    if (npts == 0)
        G_fatal_error(_("%s: no data points found\n"), argv[0]);

    Rast3d_get_window(&region);
    Rast3d_read_window(&region, NULL);

    G_debug(1, "Region from getWindow: %d %d %d", region.rows, region.cols,
            region.depths);
    map3d = Rast3d_open_new_opt_tile_size(
        output->answer, RASTER3D_USE_CACHE_DEFAULT, &region, FCELL_TYPE, 32);
    if (map3d == NULL)
        G_fatal_error(_("Unable to create output map"));

    /*output 3d raster variables declaration*/
    Nc = region.cols;
    Nr = region.rows;
    Nl = region.depths;
    lev_res = region.tb_res;
    sz = Nr * Nc * Nl;
    /*start the interpolation*/
    data = (float *)G_malloc(sz * sizeof(float));
    if (!data)
        G_fatal_error(_("Error: out of memory\n"));

    nsearch =
        npts < search_points
            ? npts
            : search_points; /*nsearch will get the value one of the minimum */
    G_message(_("Interpolating raster map <%s> ... %d levels ... "),
              output->answer, Nl);

    cnt = 0;
    z = region.top + lev_res / 2.0;
    for (lev = 0; lev < Nl; lev++) {
        G_message(_("Processing level %d"), lev + 1);
        z -= lev_res;
        y = region.north + region.ns_res / 2.0;
        for (row = 0; row < Nr; row++) {
            G_percent(row, Nr, 2);
            y -= region.ns_res;
            x = region.west - region.ew_res / 2.0;
            for (col = 0; col < Nc; col++) {
                x += region.ew_res;
                /*Filling the list upto nsearch*/
                for (i = 0; i < nsearch; i++) {
                    dy = points[i].north - y;
                    dx = points[i].east - x;
                    dz = points[i].z - z;
                    list[i].dist = dy * dy + dx * dx + dz * dz;
                    list[i].w = points[i].w;
                }
                /* find the maximum distance */
                maxdist = list[max = 0].dist;
                for (n = 1; n < nsearch; n++) {
                    if (maxdist < list[n].dist)
                        maxdist = list[max = n].dist;
                }
                /* go thru rest of the points now */
                for (; i < npts; i++) {
                    dy = points[i].north - y;
                    dx = points[i].east - x;
                    dz = points[i].z - z;
                    dist = dy * dy + dx * dx + dz * dz;

                    if (dist < maxdist) {
                        /* replace the largest dist */
                        list[max].w = points[i].w;
                        list[max].dist = dist;
                        maxdist = list[max = 0].dist;
                        for (n = 1; n < nsearch; n++) {
                            if (maxdist < list[n].dist)
                                maxdist = list[max = n].dist;
                        }
                    }
                }
                /* interpolate */
                sum1 = 0.0;
                sum2 = 0.0;
                for (n = 0; n < nsearch; n++) {
                    if (dist = list[n].dist) {
                        sum1 += list[n].w / dist;
                        sum2 += 1.0 / dist;
                    }
                    else {
                        sum1 = list[n].w;
                        sum2 = 1.0;
                        break;
                    }
                }
                data[cnt] = (sum1 / sum2);
                value = data[cnt];
                cnt++;
                Rast3d_put_float(map3d, col, row, lev, value);
            } /*cols*/
        }     /*rows*/
    }         /*levels*/
    G_free(data);

    if (!Rast3d_close(map3d))
        G_fatal_error(_("Unable to close new 3d raster map"));
    G_done_msg(" ");
    exit(EXIT_SUCCESS);
}

void newpoint(double w, double z, double east, double north)
{
    if (npoints_alloc <= npts) {
        npoints_alloc += 128;
        points = (struct Point *)G_realloc(points, npoints_alloc *
                                                       sizeof(struct Point));
    }
    points[npts].north = north;
    points[npts].east = east;
    points[npts].z = z;
    points[npts].w = w;
    npts++;
}
