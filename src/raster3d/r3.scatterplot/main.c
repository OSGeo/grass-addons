/****************************************************************************
 *
 * MODULE:       r3.scatterplot
 *
 * AUTHOR(S):    Vaclav Petras <wenzeslaus gmail com>
 *
 * PURPOSE:      Creates a scatter plot of two or more 3D maps
 *
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

/*
TODO: attribute table with backlink coordinates
TODO: store color of the original cell for each raster in attr table
TODO: additional attributes from additional maps? (may be too much)
TODO: decimate every nth point
TODO: set resolution internally to a lower one (resolution option)
TODO: auto offset flag would benefit from coordinates in attribute table
TODO: -r for placing into the region: i.e. it needs scale based on rast max,
spacing and num of scatter plots
TODO: flag to set color table so that each layer has separate color (like
d.correlate or d.vect layer=-1 -c), good without -f
TODO: flag or option to output real coordinates - useful for debugging and to
see what is sampled
TODO: layers and cats with RGB as in v.in.lidar ('std layer numbers' conflicting
with multiple scatter plots)
TODO: flag(s) to use depth (-d, always positive?) or z (-z, actual sign) as the
3rd (z) coordinate (to avoid need for r.mapcalc when correlation with z is
needed as 3rd dimension)
TODO: layout: add max num per row so that a row is broken
TODO: optimize for case z_raster == color_raster or even if one of inputs is z
or color
*/

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster3d.h>
#include <grass/vector.h>

#include "vector_mask.h"

struct ScatterOptions {
    struct Option *input, *output;
    struct Option *z_raster, *color_raster;
    struct Option *xscale, *yscale, *zscale;
    struct Option *spacing;
    struct Option *position;
    struct Option *vector_mask, *vector_mask_field;
    struct Option *vector_mask_cats, *vector_mask_where;
};

struct ScatterFlags {
    struct Flag *auto_offset;
    struct Flag *one_layer;
    struct Flag *region_position;
    struct Flag *invert_mask;
    struct Flag *notopo;
};

static void define_parameters(struct ScatterOptions *opt,
                              struct ScatterFlags *flg)
{
    struct GModule *module;

    module = G_define_module();
    G_add_keyword(_("raster3d"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("diagram"));
    G_add_keyword(_("correlation"));
    G_add_keyword(_("scatter plot"));
    G_add_keyword(_("vector"));
    G_add_keyword(_("voxel"));
    module->label = _("Creates a scatter plot of 3D raster maps");
    module->description = _(
        "Creates a scatter plot of two or more 3D raster maps as a vector map");

    opt->input = G_define_standard_option(G_OPT_R3_INPUTS);

    opt->output = G_define_standard_option(G_OPT_V_OUTPUT);

    opt->z_raster = G_define_standard_option(G_OPT_R3_INPUT);
    opt->z_raster->key = "z_raster";
    opt->z_raster->description =
        _("Name of input 3D raster map to define Z coordinates");
    opt->z_raster->required = NO;

    opt->color_raster = G_define_standard_option(G_OPT_R3_INPUT);
    opt->color_raster->key = "color_raster";
    opt->color_raster->description =
        _("Name of input 3D raster map to define category and color");
    opt->color_raster->required = NO;

    opt->xscale = G_define_option();
    opt->xscale->key = "xscale";
    opt->xscale->type = TYPE_DOUBLE;
    opt->xscale->required = NO;
    opt->xscale->answer = "1.0";
    opt->xscale->description = _("Scale to apply to X axis");
    opt->xscale->guisection = _("Transform");

    opt->yscale = G_define_option();
    opt->yscale->key = "yscale";
    opt->yscale->type = TYPE_DOUBLE;
    opt->yscale->required = NO;
    opt->yscale->answer = "1.0";
    opt->yscale->description = _("Scale to apply to Y axis");
    opt->yscale->guisection = _("Transform");

    opt->zscale = G_define_option();
    opt->zscale->key = "zscale";
    opt->zscale->type = TYPE_DOUBLE;
    opt->zscale->required = NO;
    opt->zscale->answer = "1.0";
    opt->zscale->description = _("Scale to apply to Z axis");
    opt->zscale->guisection = _("Transform");

    flg->region_position = G_define_flag();
    flg->region_position->key = 'w';
    flg->region_position->label =
        _("Place into the current region south-west corner");
    flg->region_position->description =
        _("The output coordinates will not represent the original values");
    flg->region_position->guisection = _("Layout");

    opt->position = G_define_standard_option(G_OPT_M_COORDS);
    opt->position->key = "position";
    opt->position->label = _("Place to the given coordinates");
    opt->position->description =
        _("The output coordinates will not represent the original values");
    opt->position->guisection = _("Layout");

    flg->auto_offset = G_define_flag();
    flg->auto_offset->key = 'f';
    flg->auto_offset->label = _("Automatically offset each scatter plot");
    flg->auto_offset->description =
        _("The output coordinates will not represent the original values");
    flg->auto_offset->guisection = _("Layout");

    opt->spacing = G_define_option();
    opt->spacing->key = "spacing";
    opt->spacing->type = TYPE_DOUBLE;
    opt->spacing->required = NO;
    opt->spacing->label = _("Spacing between scatter plots");
    opt->spacing->description = _("Applied when automatic offset is used");
    opt->spacing->guisection = _("Layout");

    flg->one_layer = G_define_flag();
    flg->one_layer->key = 's';
    flg->one_layer->label = _("Put points into a single layer");
    flg->one_layer->description =
        _("Even with multiple rasters, put all points into a single layer");
    flg->one_layer->guisection = _("Layout");

    opt->vector_mask = G_define_standard_option(G_OPT_V_INPUT);
    opt->vector_mask->key = "vector_mask";
    opt->vector_mask->required = NO;
    opt->vector_mask->label = _("Areas to use in the scatter plots");
    opt->vector_mask->description =
        _("Name of vector map with areas from where the scatter plot should be "
          "generated");
    opt->vector_mask->guisection = _("Mask");

    opt->vector_mask_field = G_define_standard_option(G_OPT_V_FIELD);
    opt->vector_mask_field->key = "mask_layer";
    opt->vector_mask_field->label = _("Layer number or name for vector mask");
    opt->vector_mask_field->guisection = _("Mask");

    opt->vector_mask_cats = G_define_standard_option(G_OPT_V_CATS);
    opt->vector_mask_cats->key = "mask_cats";
    opt->vector_mask_cats->label = _("Category values for vector mask");
    opt->vector_mask_cats->guisection = _("Mask");

    opt->vector_mask_where = G_define_standard_option(G_OPT_DB_WHERE);
    opt->vector_mask_where->key = "mask_where";
    opt->vector_mask_where->label = _("WHERE conditions for the vector mask");
    opt->vector_mask_where->guisection = _("Mask");

    flg->invert_mask = G_define_flag();
    flg->invert_mask->key = 'u';
    flg->invert_mask->description = _("Invert mask");
    flg->invert_mask->guisection = _("Mask");

    flg->notopo = G_define_standard_flag(G_FLG_V_TOPO);

    G_option_requires(opt->spacing, flg->auto_offset, NULL);
    G_option_exclusive(opt->position, flg->region_position, NULL);
    G_option_requires(opt->vector_mask_field, opt->vector_mask, NULL);
    G_option_requires(opt->vector_mask_cats, opt->vector_mask, NULL);
    G_option_requires(opt->vector_mask_where, opt->vector_mask, NULL);
    G_option_requires(flg->invert_mask, opt->vector_mask, NULL);
}

static void option_to_en(struct Option *option, double *easting,
                         double *northing, struct Cell_head *region)
{
    if (!G_scan_easting(option->answers[0], easting, region->proj))
        G_fatal_error(_("Invalid easting: %s"), option->answers[0]);
    if (!G_scan_northing(option->answers[1], northing, region->proj))
        G_fatal_error(_("Invalid northing: %s"), option->answers[1]);
}

static RASTER3D_Map *open_raster3d(char *name, RASTER3D_Region *region)
{
    RASTER3D_Map *map;

    map = Rast3d_open_cell_old(name, G_find_raster3d(name, ""), region,
                               RASTER3D_TILE_SAME_AS_FILE,
                               RASTER3D_USE_CACHE_DEFAULT);
    if (map == NULL)
        Rast3d_fatal_error(_("Unable to open 3D raster map <%s>"), name);
    return map;
}

int main(int argc, char *argv[])
{
    struct ScatterOptions opt;
    struct ScatterFlags flg;

    G_gisinit(argv[0]);

    define_parameters(&opt, &flg);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    double xscale = 1.0;
    double yscale = 1.0;
    double zscale = 1.0;

    if (opt.xscale->answer)
        xscale = atof(opt.xscale->answer);
    if (opt.yscale->answer)
        yscale = atof(opt.yscale->answer);
    if (opt.zscale->answer)
        zscale = atof(opt.zscale->answer);

    double spacing = 0;

    if (opt.spacing->answer)
        spacing = atof(opt.spacing->answer);

    double start_x = 0;
    double start_y = 0;
    struct Cell_head region_2d;

    G_get_window(&region_2d);

    if (flg.region_position->answer) {
        start_x = region_2d.west;
        start_y = region_2d.south;
    }

    if (opt.position->answer)
        option_to_en(opt.position, &start_x, &start_y, &region_2d);

    RASTER3D_Region region;

    Rast3d_init_defaults();
    Rast3d_get_window(&region);

    struct Map_info output;
    struct line_pnts *points;
    struct line_cats *cats;

    /* TODO: clean up the following code */
    /* open output vector */
    char buf[2000];
    sprintf(buf, "%s", opt.output->answer);
    /* strip any @mapset from vector output name */
    G_find_vector(buf, G_mapset());
    if (Vect_open_new(&output, opt.output->answer, 1) < 0)
        G_fatal_error(_("Unable to create vector map <%s>"),
                      opt.output->answer);
    Vect_hist_command(&output);

    points = Vect_new_line_struct();
    cats = Vect_new_cats_struct();

    int rows, cols, depths;
    int col, row, depth;
    char **name1, **name2;
    DCELL x, y, z;
    FCELL fcat;
    int cat;
    int layer;
    /* actual geographical coordinates */
    double xcoor, ycoor, unused;

    double current_max_x = -HUGE_VAL;
    double layer_x_offset = start_x;
    double layer_y_offset = start_y;

    z = 0;
    cat = 1;
    layer = 1;
    rows = region.rows;
    cols = region.cols;
    depths = region.depths;
    G_debug(1, "limits: r=%d c=%d d=%d", rows, cols, depths);

    RASTER3D_Map *z_raster = NULL;
    RASTER3D_Map *color_raster = NULL;

    int n_inputs = 0;

    for (name1 = opt.input->answers; *name1 != NULL; name1++) {
        n_inputs++;
        if (!G_find_raster3d(*name1, ""))
            Rast3d_fatal_error(_("3D raster map <%s> not found"), *name1);
    }

    if (opt.color_raster->answer)
        color_raster = open_raster3d(opt.color_raster->answer, &region);
    if (opt.z_raster->answer)
        z_raster = open_raster3d(opt.z_raster->answer, &region);

    struct VectorMask vector_mask;
    int use_vector_mask = FALSE;
    if (opt.vector_mask->answer) {
        VectorMask_init(&vector_mask, opt.vector_mask->answer,
                        opt.vector_mask_field->answer,
                        opt.vector_mask_cats->answer,
                        opt.vector_mask_where->answer, flg.invert_mask->answer);
        use_vector_mask = TRUE;
    }

    for (name1 = opt.input->answers; *name1 != NULL; name1++) {
        for (name2 = opt.input->answers; *name2 != NULL; name2++) {
            /* same name or used combination */
            if (name1 >= name2)
                continue;
            /* report when relevant */
            if (n_inputs > 2 && !flg.one_layer->answer)
                G_message(_("Putting values from <%s> and <%s> into layer %d "
                            "of <%s>"),
                          *name1, *name2, layer, opt.output->answer);
            G_debug(3, "save %s + %s to %d (%s)", *name1, *name2, layer,
                    opt.output->answer);
            RASTER3D_Map *map1 = open_raster3d(*name1, &region);
            RASTER3D_Map *map2 = open_raster3d(*name2, &region);

            for (row = 0; row < rows; row++) {
                G_percent(row, rows, 1);
                for (col = 0; col < cols; col++) {
                    /* vector mask is expensive, so we first do 2D loops */
                    if (use_vector_mask) {
                        Rast3d_coord2location(&region, row + 0.5, col + 0.5, 0,
                                              &ycoor, &xcoor, &unused);
                        if (!VectorMask_point_in(&vector_mask, xcoor, ycoor))
                            continue;
                    }
                    for (depth = 0; depth < depths; depth++) {
                        x = Rast3d_get_double(map1, col, row, depth);
                        if (Rast_is_d_null_value(&x))
                            continue;
                        y = Rast3d_get_double(map2, col, row, depth);
                        if (Rast_is_d_null_value(&y))
                            continue;
                        if (z_raster) {
                            z = Rast3d_get_double(z_raster, col, row, depth);
                            if (Rast_is_d_null_value(&z))
                                continue;
                        }
                        if (color_raster) {
                            fcat =
                                Rast3d_get_float(color_raster, col, row, depth);
                            if (Rast_is_d_null_value(&fcat))
                                continue;
                            cat = (int)fcat;
                            /* TODO: what to do when value cannot be cat */
                        }
                        x *= xscale;
                        y *= yscale;
                        z *= zscale;
                        x += layer_x_offset;
                        y += layer_y_offset;
                        if (current_max_x < x)
                            current_max_x = x;
                        Vect_cat_set(cats, layer, cat);
                        Vect_append_point(points, x, y, z);
                        // Vect_append_point(points, xcoor, ycoor, z);
                        Vect_write_line(&output, GV_POINT, points, cats);
                        Vect_reset_line(points);
                        Vect_reset_cats(cats);
                        /* TODO: we can determine cat == GV_CAT_MAX ahead and
                         * tell user what to do */
                        cat++;
                    }
                }
            }
            G_percent(1, 1, 1);
            if (!Rast3d_close(map1))
                Rast3d_fatal_error(_("Unable to close 3D raster map"));
            if (!Rast3d_close(map2))
                Rast3d_fatal_error(_("Unable to close 3D raster map"));
            if (!flg.one_layer->answer)
                layer++;
            if (flg.auto_offset->answer)
                layer_x_offset = current_max_x + spacing;
        }
    }

    Vect_destroy_line_struct(points);
    Vect_destroy_cats_struct(cats);

    if (color_raster) {
        struct Colors colors;

        Rast3d_read_colors(opt.color_raster->answer,
                           G_find_raster3d(opt.color_raster->answer, ""),
                           &colors);
        Vect_write_colors(opt.output->answer, G_mapset(), &colors);
    }

    if (z_raster && !Rast3d_close(z_raster))
        Rast3d_fatal_error(_("Unable to close 3D raster map"));
    if (color_raster && !Rast3d_close(color_raster))
        Rast3d_fatal_error(_("Unable to close 3D raster map"));

    if (opt.vector_mask->answer) {
        VectorMask_destroy(&vector_mask);
    }

    if (!flg.notopo->answer)
        Vect_build(&output);
    Vect_close(&output);

    exit(EXIT_SUCCESS);
}
