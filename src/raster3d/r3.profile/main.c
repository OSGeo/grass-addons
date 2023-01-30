/****************************************************************************
 *
 * MODULE:       r3.profile (based on r.profile)
 *
 * AUTHOR(S):    Bob Covill <bcovill tekmap.ns.ca> (r.profile)
 *               Vaclav Petras <wenzeslaus gmail com> (r3.profile)
 *
 * PURPOSE:      Profiles (slices vertically) 3D raster at 2D coordinates
 *
 * COPYRIGHT:    (C) 2000-2016 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster3d.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#include "local_proto.h"

int clr;
struct Colors colors;

static double dist, e, n;

int main(int argc, char *argv[])
{
    char *name, *outfile;
    const char *unit;
    int unit_id;
    double factor;
    int projection;
    FILE *fp, *coor_fp;
    double res;
    char *null_string;
    char ebuf[256], nbuf[256], label[512], formatbuff[256];
    char b1[100], b2[100];
    int n;
    int havefirst = FALSE;
    int coords = 0, i, k = -1;
    double e1, e2, n1, n2;
    RASTER_MAP_TYPE data_type;
    struct Cell_head window;
    struct {
        struct Option *opt1, *profile, *res, *output, *raster_output, *null_str,
            *coord_file, *units;
        struct Flag *g, *c, *m;
    } parm;
    struct GModule *module;

    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("profile"));
    module->description =
        _("Outputs the raster map layer values lying on user-defined line(s).");

    parm.opt1 = G_define_standard_option(G_OPT_R3_INPUT);

    parm.output = G_define_standard_option(G_OPT_F_OUTPUT);
    parm.output->required = NO;
    parm.output->answer = "-";
    parm.output->description =
        _("Name of file for output (use output=- for stdout)");

    parm.raster_output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.raster_output->key = "raster_output";
    parm.raster_output->required = NO;

    parm.profile = G_define_standard_option(G_OPT_M_COORDS);
    parm.profile->required = NO;
    parm.profile->multiple = YES;
    parm.profile->description = _("Profile coordinate pairs");

    parm.coord_file = G_define_standard_option(G_OPT_F_INPUT);
    parm.coord_file->key = "file";
    parm.coord_file->required = NO;
    parm.coord_file->label =
        _("Name of input file containing coordinate pairs");
    parm.coord_file->description = _("Use instead of the 'coordinates' option. "
                                     "\"-\" reads from stdin.");

    parm.res = G_define_option();
    parm.res->key = "resolution";
    parm.res->type = TYPE_DOUBLE;
    parm.res->required = NO;
    parm.res->description =
        _("Resolution along profile (default = current region resolution)");

    parm.null_str = G_define_standard_option(G_OPT_M_NULL_VALUE);
    parm.null_str->answer = "*";

    parm.g = G_define_flag();
    parm.g->key = 'g';
    parm.g->description = _("Output easting and northing in first two columns "
                            "of four column output");

    parm.c = G_define_flag();
    parm.c->key = 'c';
    parm.c->description =
        _("Output RRR:GGG:BBB color values for each profile point");

    parm.units = G_define_standard_option(G_OPT_M_UNITS);
    parm.units->options = "meters,kilometers,feet,miles";
    parm.units->label = parm.units->description;
    parm.units->description =
        _("If units are not specified, current location units are used. "
          "Meters are used by default in geographic (latlon) locations.");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    clr = 0;
    if (parm.c->answer)
        clr = 1; /* color output */

    null_string = parm.null_str->answer;

    if ((parm.profile->answer && parm.coord_file->answer) ||
        (!parm.profile->answer && !parm.coord_file->answer))
        G_fatal_error(_("Either use profile option or coordinate_file "
                        " option, but not both"));

    G_get_window(&window);
    projection = G_projection();

    /* get conversion factor and units name */
    if (parm.units->answer) {
        unit_id = G_units(parm.units->answer);
        factor = 1. / G_meters_to_units_factor(unit_id);
        unit = G_get_units_name(unit_id, 1, 0);
    }
    /* keep meters in case of latlon */
    else if (projection == PROJECTION_LL) {
        factor = 1;
        unit = "meters";
    }
    else {
        /* get conversion factor to current units */
        unit = G_database_unit_name(1);
        factor = G_database_units_to_meters_factor();
    }

    if (parm.res->answer) {
        res = atof(parm.res->answer);
        /* Catch bad resolution ? */
        if (res <= 0)
            G_fatal_error(_("Illegal resolution %g [%s]"), res / factor, unit);
    }
    else {
        /* Do average of EW and NS res */
        res = (window.ew_res + window.ns_res) / 2;
    }

    G_message(_("Using resolution: %g [%s]"), res / factor, unit);

    G_begin_distance_calculations();

    /* Open Input File for reading */
    /* Get Input Name */
    name = parm.opt1->answer;
    if (parm.g->answer)
        coords = 1;

    RASTER3D_Region region;

    Rast3d_init_defaults();
    Rast3d_get_window(&region);
    G_message("region west=%f ewres=%f north=%f nsres=%f", region.west,
              region.ew_res, region.north, region.ns_res);

    /* Open Raster File */
    int cache = RASTER3D_USE_CACHE_DEFAULT;
    int type = FCELL_TYPE; /* or RASTER3D_TILE_SAME_AS_FILE */
    /* TODO: mapset support correct? */
    RASTER3D_Map *fd =
        Rast3d_open_cell_old(name, "", RASTER3D_DEFAULT_WINDOW, type, cache);
    if (!fd)
        G_fatal_error(_("Unable to open file <%s>"), name);

    /* Open ASCII file for output or stdout */
    outfile = parm.output->answer;

    if ((strcmp("-", outfile)) == 0) {
        fp = stdout;
    }
    else if (NULL == (fp = fopen(outfile, "w")))
        G_fatal_error(_("Unable to open file <%s>"), outfile);

    /* Get Raster Type */
    data_type = TYPE_DOUBLE;
    /* Done with file */

    /* Show message giving output format */
    G_message(_("Output columns:"));
    if (coords == 1)
        sprintf(formatbuff,
                _("Easting, Northing, Along track dist. [%s], Elevation"),
                unit);
    else
        sprintf(formatbuff, _("Along track dist. [%s], Elevation"), unit);

    G_message("%s", formatbuff);

    struct DoubleList values;
    int output_initialized = FALSE;
    int outfd;
    void *output_buff = NULL;
    size_t cell_size = Rast_cell_size(data_type);
    struct Cell_head output_region;

    int depth;

    for (depth = region.depths - 1; depth >= 0; depth--) {
        double_list_init(&values);
        /* Get Profile Start Coords */
        if (parm.coord_file->answer) {
            if (strcmp("-", parm.coord_file->answer) == 0)
                /* coor_fp = stdin; */
                G_fatal_error(_("Standard input is not yet supported"));
            else
                coor_fp = fopen(parm.coord_file->answer, "r");

            if (coor_fp == NULL)
                G_fatal_error(_("Could not open <%s>"),
                              parm.coord_file->answer);

            for (n = 1; input(b1, ebuf, b2, nbuf, label, coor_fp); n++) {
                G_debug(4, "stdin line %d: ebuf=[%s]  nbuf=[%s]", n, ebuf,
                        nbuf);
                if (!G_scan_easting(ebuf, &e2, G_projection()) ||
                    !G_scan_northing(nbuf, &n2, G_projection()))
                    G_fatal_error(_("Invalid coordinates %s %s"), ebuf, nbuf);

                if (havefirst)
                    do_profile(e1, e2, n1, n2, coords, res, fd, data_type, fp,
                               null_string, unit, factor, &region, depth,
                               &values);
                e1 = e2;
                n1 = n2;
                havefirst = TRUE;
            }

            /* TODO: we can't use stdin in loop like this, need to store the
             * coords */
            if (coor_fp != stdin)
                fclose(coor_fp);
        }
        else {
            /* Coords given on the Command Line using the profile= option */
            for (i = 0; parm.profile->answers[i]; i += 2) {
                /* Test for number coordinate pairs */
                k = i;
            }

            if (k == 0) {
                /* Only one coordinate pair supplied */
                G_scan_easting(parm.profile->answers[0], &e1, G_projection());
                G_scan_northing(parm.profile->answers[1], &n1, G_projection());
                e2 = e1;
                n2 = n1;

                /* Get profile info */
                do_profile(e1, e2, n1, n2, coords, res, fd, data_type, fp,
                           null_string, unit, factor, &region, depth, &values);
            }
            else {
                for (i = 0; i <= k - 2; i += 2) {
                    G_scan_easting(parm.profile->answers[i], &e1,
                                   G_projection());
                    G_scan_northing(parm.profile->answers[i + 1], &n1,
                                    G_projection());
                    G_scan_easting(parm.profile->answers[i + 2], &e2,
                                   G_projection());
                    G_scan_northing(parm.profile->answers[i + 3], &n2,
                                    G_projection());

                    /* Get profile info */
                    do_profile(e1, e2, n1, n2, coords, res, fd, data_type, fp,
                               null_string, unit, factor, &region, depth,
                               &values);
                }
            }
        }
        if (!output_initialized) {
            Rast_get_window(&output_region);
            output_region.south = 0;
            output_region.north = res * region.depths;
            output_region.west = 0;
            output_region.east = region.tb_res * values.num_items;
            /* TODO: ew_res is more complex than just res, perhaps mean of
             * distances if we store them */
            output_region.ew_res = res;
            output_region.ns_res = region.tb_res;

            Rast_set_output_window(&output_region);
            outfd = Rast_open_new(parm.raster_output->answer, data_type);
            output_buff = Rast_allocate_output_buf(data_type);
            output_initialized = TRUE;
        }
        void *ptr = output_buff;
        int i;

        for (i = 0; i < values.num_items; i++) {
            Rast_set_d_value(ptr, values.items[i], data_type);
            ptr = G_incr_void_ptr(ptr, cell_size);
        }
        Rast_put_row(outfd, output_buff, data_type);
        double_list_free(&values);
    }
    Rast_close(outfd);

    Rast3d_close(fd);
    fclose(fp);

    struct Colors colors;

    /* with any profile we always get the same colors */
    Rast3d_read_colors(name, "", &colors);
    Rast_write_colors(parm.raster_output->answer, G_mapset(), &colors);

    exit(EXIT_SUCCESS);
} /* Done with main */

/* Calculate the Profile Now */
/* Establish parameters */
int do_profile(double e1, double e2, double n1, double n2, int coords,
               double res, RASTER3D_Map *fd, int data_type, FILE *fp,
               char *null_string, const char *unit, double factor,
               RASTER3D_Region *region, int depth, struct DoubleList *values)
{
    double rows, cols, LEN;
    double Y, X, k;

    cols = e1 - e2;
    rows = n1 - n2;

    LEN = G_distance(e1, n1, e2, n2);
    G_message(_("Approx. transect length: %f [%s]"), LEN / factor, unit);

    if (!G_point_in_region(e2, n2))
        G_warning(
            _("Endpoint coordinates are outside of current region settings"));

    /* Calculate Azimuth of Line */
    if (rows == 0 && cols == 0) {
        /* Special case for no movement */
        e = e1;
        n = n1;
        read_rast(e, n, dist / factor, fd, coords, data_type, fp, null_string,
                  region, depth, values);
    }

    k = res / hypot(rows, cols);
    Y = k * rows;
    X = k * cols;
    if (Y < 0)
        Y = Y * -1.;
    if (X < 0)
        X = X * -1.;

    if (e != 0.0 && (e != e1 || n != n1)) {
        dist -= G_distance(e, n, e1, n1);
    }

    if (rows >= 0 && cols < 0) {
        /* SE Quad or due east */
        for (e = e1, n = n1; e < e2 || n > n2; e += X, n -= Y) {
            read_rast(e, n, dist / factor, fd, coords, data_type, fp,
                      null_string, region, depth, values);
            /* d+=res; */
            dist += G_distance(e - X, n + Y, e, n);
        }
    }

    if (rows < 0 && cols <= 0) {
        /* NE Quad  or due north */
        for (e = e1, n = n1; e < e2 || n < n2; e += X, n += Y) {
            read_rast(e, n, dist / factor, fd, coords, data_type, fp,
                      null_string, region, depth, values);
            /* d+=res; */
            dist += G_distance(e - X, n - Y, e, n);
        }
    }

    if (rows > 0 && cols >= 0) {
        /* SW Quad or due south */
        for (e = e1, n = n1; e > e2 || n > n2; e -= X, n -= Y) {
            read_rast(e, n, dist / factor, fd, coords, data_type, fp,
                      null_string, region, depth, values);
            /* d+=res; */
            dist += G_distance(e + X, n + Y, e, n);
        }
    }

    if (rows <= 0 && cols > 0) {
        /* NW Quad  or due west */
        for (e = e1, n = n1; e > e2 || n < n2; e -= X, n += Y) {
            read_rast(e, n, dist / factor, fd, coords, data_type, fp,
                      null_string, region, depth, values);
            /* d+=res; */
            dist += G_distance(e + X, n - Y, e, n);
        }
    }
    /*
     * return dist;
     */
    return 0;
} /* done with do_profile */
