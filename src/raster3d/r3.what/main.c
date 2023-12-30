/****************************************************************************
 *
 * MODULE:       r3.what
 *
 * AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
 *
 * PURPOSE:      Queries 3D raster at specified 2D or 3D coordinates
 *
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <grass/gis.h>
#include <grass/raster3d.h>
#include <grass/vector.h>
#include <grass/glocale.h>

FILE *openAscii(char *file)
{
    FILE *fp;

    if (file && file[0] != '-') {
        fp = fopen(file, "w");
        if (fp == NULL) {
            perror(file);
            G_usage();
            exit(EXIT_FAILURE);
        }
    }
    else
        fp = stdout;

    return fp;
}

void query(RASTER3D_Map *input_map, double east, double north, FILE *fp,
           char *fs, RASTER3D_Region *region, int type, char *null_val)
{

    int x, y, depth;
    DCELL dvalue;
    FCELL fvalue;

    Rast3d_location2coord(region, north, east, region->top, &x, &y, &depth);
    fprintf(fp, "%f%s%f", east, fs, north);
    for (depth = 0; depth < region->depths; depth++) {
        if (type == FCELL_TYPE) {
            Rast3d_get_value(input_map, x, y, depth, &fvalue, FCELL_TYPE);
            if (Rast3d_is_null_value_num(&fvalue, FCELL_TYPE))
                fprintf(fp, "%s%s", fs, null_val);
            else
                fprintf(fp, "%s%f", fs, fvalue);
        }
        else {
            Rast3d_get_value(input_map, x, y, depth, &dvalue, DCELL_TYPE);
            if (Rast3d_is_null_value_num(&dvalue, DCELL_TYPE))
                fprintf(fp, "%s%s", fs, null_val);
            else
                fprintf(fp, "%s%f", fs, dvalue);
        }
    }
    fprintf(fp, "\n");
}

void query3D(RASTER3D_Map *input_map, double east, double north, double top,
             FILE *fp, char *fs, RASTER3D_Region *region, int type,
             char *null_val)
{

    int x, y, depth;
    DCELL dvalue;
    FCELL fvalue;

    Rast3d_location2coord(region, north, east, top, &x, &y, &depth);
    fprintf(fp, "%f%s%f%s%f", east, fs, north, fs, top);
    if (type == FCELL_TYPE) {
        Rast3d_get_value(input_map, x, y, depth, &fvalue, FCELL_TYPE);
        if (Rast3d_is_null_value_num(&fvalue, FCELL_TYPE))
            fprintf(fp, "%s%s", fs, null_val);
        else
            fprintf(fp, "%s%f", fs, fvalue);
    }
    else {
        Rast3d_get_value(input_map, x, y, depth, &dvalue, DCELL_TYPE);
        if (Rast3d_is_null_value_num(&dvalue, DCELL_TYPE))
            fprintf(fp, "%s%s", fs, null_val);
        else
            fprintf(fp, "%s%f", fs, dvalue);
    }
    fprintf(fp, "\n");
}

int main(int argc, char *argv[])
{
    struct Option *input, *output, *points_opt, *coords_opt, *coords3d_opt,
        *fs_opt, *null_val;
    struct Flag *mask, *z_flag;
    struct GModule *module;
    FILE *fp;
    RASTER3D_Region region;
    RASTER3D_Map *input_map;
    struct Map_info Map;
    struct line_pnts *Points;
    int changemask;
    int i;
    double east, north, top;
    int type, ltype;
    char *fs;
    int z;

    /* Initialize GRASS */
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("raster3d"));
    G_add_keyword(_("query"));
    G_add_keyword(_("voxel"));
    module->description =
        _("Queries 3D raster in specified 2D or 3D coordinates.");

    input = G_define_standard_option(G_OPT_R3_INPUT);
    input->key = "input";
    input->description = _("Input 3D raster map");
    input->guisection = _("Query");

    coords_opt = G_define_standard_option(G_OPT_M_COORDS);
    coords_opt->required = NO;
    coords_opt->multiple = YES;
    coords_opt->description = _("Query with 2D coordinates");
    coords_opt->guisection = _("Query");

    coords3d_opt = G_define_option();
    coords3d_opt->key = "coordinates_3d";
    coords3d_opt->type = TYPE_DOUBLE;
    coords3d_opt->required = NO;
    coords3d_opt->multiple = YES;
    coords3d_opt->key_desc = "east,north,top";
    coords3d_opt->gisprompt = "old,coords,coords";
    coords3d_opt->description = _("Query with 3D coordinates");
    coords3d_opt->guisection = _("Query");

    points_opt = G_define_standard_option(G_OPT_V_MAP);
    points_opt->key = "points";
    points_opt->label = _("Name of vector points map for query");
    points_opt->required = NO;
    points_opt->guisection = _("Query");

    output = G_define_standard_option(G_OPT_F_OUTPUT);
    output->required = NO;
    output->description = _("Name for output file");
    output->guisection = _("Print");

    fs_opt = G_define_standard_option(G_OPT_F_SEP);
    fs_opt->guisection = _("Print");

    null_val = G_define_standard_option(G_OPT_M_NULL_VALUE);
    null_val->answer = "*";
    null_val->guisection = _("Print");

    mask = G_define_flag();
    mask->key = 'm';
    mask->description = _("Use 3D raster mask (if exists) with input map");

    z_flag = G_define_flag();
    z_flag->key = 'z';
    z_flag->description = _("Ignore points Z values");

    G_option_required(coords_opt, coords3d_opt, points_opt, NULL);
    G_option_exclusive(coords_opt, points_opt, NULL);
    G_option_exclusive(coords3d_opt, coords_opt, NULL);

    /* Have GRASS get inputs */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (!G_find_raster3d(input->answer, ""))
        Rast3d_fatal_error(_("3D raster map <%s> not found"), input->answer);

    /* Initiate the default settings */
    Rast3d_init_defaults();

    /* Figure out the current region settings */
    Rast3d_get_window(&region);

    /* Open the map and use XY cache mode */
    input_map = Rast3d_open_cell_old(
        input->answer, G_find_raster3d(input->answer, ""), &region,
        RASTER3D_TILE_SAME_AS_FILE, RASTER3D_USE_CACHE_DEFAULT);

    if (!input_map)
        Rast3d_fatal_error(_("Unable to open 3D raster map <%s>"),
                           input->answer);

    type = Rast3d_tile_type_map(input_map);

    /* Open the output ascii file */
    fp = openAscii(output->answer);

    fs = G_option_to_separator(fs_opt);

    z = z_flag->answer;

    /*if requested set the mask on */
    if (mask->answer) {
        if (Rast3d_mask_file_exists()) {
            changemask = 0;
            if (Rast3d_mask_is_off(input_map)) {
                Rast3d_mask_on(input_map);
                changemask = 1;
            }
        }
    }
    /* open vector points map */
    if (points_opt->answer) {
        Vect_set_open_level(1); /* topology not required */
        if (Vect_open_old(&Map, points_opt->answer, "") < 0)
            G_fatal_error(_("Unable to open vector map <%s>"),
                          points_opt->answer);
        Points = Vect_new_line_struct();
        while (1) {
            ltype = Vect_read_next_line(&Map, Points, NULL);
            if (ltype == -1)
                G_fatal_error(_("Unable to read vector map <%s>"),
                              Vect_get_full_name(&Map));
            else if (ltype == -2)
                break;
            else if (!(ltype & GV_POINTS)) {
                G_warning(_("Line is not point or centroid, skipped"));
            }
            else {
                east = Points->x[0];
                north = Points->y[0];
                if (Vect_is_3d(&Map) && !z) {
                    top = Points->z[0];
                    query3D(input_map, east, north, top, fp, fs, &region, type,
                            null_val->answer);
                }
                else
                    query(input_map, east, north, fp, fs, &region, type,
                          null_val->answer);
            }
        }
    }
    else {
        /* loop through coordinates */
        if (coords3d_opt->answer) {
            for (i = 0; coords3d_opt->answers[i] != NULL; i += 3) {
                G_scan_easting(coords3d_opt->answers[i], &east, G_projection());
                G_scan_northing(coords3d_opt->answers[i + 1], &north,
                                G_projection());
                top = atof(coords3d_opt->answers[i + 2]);
                query3D(input_map, east, north, top, fp, fs, &region, type,
                        null_val->answer);
            }
        }
        else {
            for (i = 0; coords_opt->answers[i] != NULL; i += 2) {
                G_scan_easting(coords_opt->answers[i], &east, G_projection());
                G_scan_northing(coords_opt->answers[i + 1], &north,
                                G_projection());
                query(input_map, east, north, fp, fs, &region, type,
                      null_val->answer);
            }
        }
    }

    /* We set the mask off, if it was off before */
    if (mask->answer) {
        if (Rast3d_mask_file_exists())
            if (Rast3d_mask_is_on(input_map) && changemask)
                Rast3d_mask_off(input_map);
    }

    /* Close files and exit */
    if (!Rast3d_close(input_map))
        Rast3d_fatal_error(_("Unable to close 3D raster map"));

    if (output)
        if (fclose(fp))
            Rast3d_fatal_error(_("Unable to close new ASCII file"));

    return 0;
}
