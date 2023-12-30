/*****************************************************************************
 *
 * MODULE:     i.points.auto
 * AUTHOR(S):  based on i.points; additions by
 *              Ivan Michelazzi, Luca Miori (MSc theses at ITC-irst)
 *             http://gisws.media.osaka-cu.ac.jp/grass04/viewpaper.php?id=37
 *             Supervisors: Markus Neteler, Stefano Merler, ITC-irst 2003, 2004
 *             Markus Metz: near complete rewrite for GRASS 7
 *
 * PURPOSE:    semi-automated image registration based in FFT correlation
 * COPYRIGHT:  GPL >=2
 *
 *****************************************************************************/

#define GLOBAL
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <grass/gis.h>
#include "globals.h"
#include "local_proto.h"
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

int main(int argc, char *argv[])
{
    struct Option *grp_opt, *order_opt, *src_img_opt, *tgt_img_opt, *detail_opt,
        *n_points_opt, *threshold_opt;
    struct Flag *c_flag;
    struct GModule *module;
    int i, npoints;
    struct Cell_head curr_window_org, tgt_window_org;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("ground control points"));
    module->description =
        _("Generate ground control points for image group to be rectified.");

    grp_opt = G_define_standard_option(G_OPT_I_GROUP);

    src_img_opt = G_define_standard_option(G_OPT_R_INPUT);
    src_img_opt->key = "source_image";
    src_img_opt->required = YES;

    tgt_img_opt = G_define_standard_option(G_OPT_R_INPUT);
    tgt_img_opt->key = "target_image";
    tgt_img_opt->required = YES;

    order_opt = G_define_option();
    order_opt->required = NO;
    order_opt->key = "order";
    order_opt->type = TYPE_INTEGER;
    order_opt->options = ("1,2,3");
    order_opt->answer = ("1");
    order_opt->description = _("Transformation polynom order (1-3)");

    n_points_opt = G_define_option();
    n_points_opt->required = YES;
    n_points_opt->key = "npoints";
    n_points_opt->type = TYPE_INTEGER;
    n_points_opt->description = _("Maximum number of points to generate");

    detail_opt = G_define_option();
    detail_opt->required = NO;
    detail_opt->key = "detail";
    detail_opt->type = TYPE_STRING;
    detail_opt->options = ("coarse,medium,fine");
    detail_opt->answer = "fine";
    detail_opt->description =
        _("How detailed should the information be to be used.");

    threshold_opt = G_define_option();
    threshold_opt->required = NO;
    threshold_opt->key = "threshold";
    threshold_opt->type = TYPE_DOUBLE;
    threshold_opt->answer = "0.0";
    threshold_opt->description = _(
        "RMS error threshold. Recommended: source image resolution or smaller");

    c_flag = G_define_flag();
    c_flag->key = 'c';
    c_flag->description = _("Use current region settings in source location "
                            "instead of source map extends");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    Rast_suppress_masking(); /* need to do this for target location */

    group.name = grp_opt->answer;
    group.img = src_img_opt->answer;
    group.tgt_img = tgt_img_opt->answer;
    transform_order = atoi(order_opt->answer);
    n_new_points = atoi(n_points_opt->answer);
    rms_threshold = atof(threshold_opt->answer);

    if (!detail_opt->answer)
        detail = 128;
    else if (!strcmp(detail_opt->answer, "coarse"))
        detail = 512;
    else if (!strcmp(detail_opt->answer, "medium"))
        detail = 128;
    else if (!strcmp(detail_opt->answer, "fine"))
        detail = 32;

    if (transform_order < 1 || transform_order > 3)
        G_fatal_error(_("Transformation order must be 1, 2 or 3"));

    if (n_new_points < 1)
        G_fatal_error(_("Number of new points must be > 0"));
    if (n_new_points > 100)
        G_warning(_("Generating %d new points will take some time"),
                  n_new_points);

    if (rms_threshold < 0.0)
        G_fatal_error(_("RMS threshold must be >= 0"));

    G_get_window(&curr_window_org);
    G_get_window(&curr_window);

    /* get group */
    get_group();

    /* get target */
    get_target();

    /* check if selected target image exists */
    select_env(TGT_ENV);
    if (!G_find_file2("cell", group.tgt_img, "")) {
        G_message("Location: %s", G_location());
        G_message("Mapset: %s", G_mapset());
        G_fatal_error(_("Target image <%s> does not exist"), group.tgt_img);
    }

    G_get_element_window(&tgt_window_org, "", "WIND", G_mapset());
    G_get_element_window(&tgt_window, "", "WIND", G_mapset());
    G_debug(1, "projection: %s", G_projection_name(G_projection()));
    G_debug(1, "tgt_window projection: %s", G_projection_name(tgt_window.proj));

    /* read group control points, if any */
    select_env(SRC_ENV);
    G_debug(1, "read group control points, if any");
    if (!I_get_control_points(group.name, &group.points))
        group.points.count = 0;

    /* check GCP number for given order */
    npoints = 0;
    for (i = 0; i < group.points.count; i++) {
        npoints += group.points.status[i];
    }
    if (transform_order == 1 && npoints < 3)
        G_fatal_error(_("Fully automated search not yet implemented"));
    if (transform_order == 2 && npoints < 6)
        G_fatal_error(_("Fully automated search not yet implemented"));
    if (transform_order == 3 && npoints < 10)
        G_fatal_error(_("Fully automated search not yet implemented"));

    Rast_get_cellhd(group.img, "", &cellhd1);
    if (c_flag->answer) {
        /* check if source current region is within given source image */
        if (curr_window.north <= cellhd1.south ||
            curr_window.south >= cellhd1.north ||
            curr_window.west >= cellhd1.east ||
            curr_window.east <= cellhd1.west)
            G_fatal_error(
                _("Current region does not overlap with selected image"));

        /* adjust window borders */
        if (curr_window.north > cellhd1.north)
            curr_window.north = cellhd1.north;
        if (curr_window.south < cellhd1.south)
            curr_window.south = cellhd1.south;
        if (curr_window.east > cellhd1.east)
            curr_window.east = cellhd1.east;
        if (curr_window.west < cellhd1.west)
            curr_window.west = cellhd1.west;
    }
    else
        Rast_get_cellhd(group.img, "", &curr_window);

    /* subpixel accuracy */
    curr_window.ew_res = cellhd1.ew_res / 3;
    curr_window.ns_res = cellhd1.ns_res / 3;
    G_adjust_Cell_head(&curr_window, 0, 0);

    /* check if extends are large enough for desired detail */
    if (curr_window.rows < detail || curr_window.cols < detail)
        G_fatal_error(_("Current region is too small for desired detail. "
                        "Decrease detail or increase region."));

    /* compute transformation equation */
    G_debug(1, "starting Compute_equation()");
    Compute_equation();
    if (group.equation_stat < 1) {
        G_fatal_error(
            _("Not enough points, %d are required"),
            (transform_order == 1 ? 3 : (transform_order == 2 ? 6 : 10)));
    }

    /* calculate target extends according to detail, use source image */
    select_env(TGT_ENV);
    set_target_window();
    Rast_get_cellhd(group.tgt_img, "", &cellhd2);

    /* check if source image and target image overlap at all */
    /* use source current region for this check */
    if (tgt_window.north <= cellhd2.south ||
        tgt_window.south >= cellhd2.north || tgt_window.west >= cellhd2.east ||
        tgt_window.east <= cellhd2.west) {
        G_debug(1, "north: %.4G <= %.4G", tgt_window.north, cellhd2.south);
        G_debug(1, "south: %.4G >= %.4G", tgt_window.south, cellhd2.north);
        G_debug(1, "west: %.4G >= %.4G", tgt_window.west, cellhd2.east);
        G_debug(1, "east: %.4G <= %.4G", tgt_window.east, cellhd2.west);
        if (c_flag->answer)
            G_fatal_error(
                _("Source current region and target image do not overlap"));
        else
            G_fatal_error(_("Source image and target image do not overlap"));
    }

    /* shrink regions to overlap */
    select_env(SRC_ENV);
    overlap();

    /* hold thumbs */
    Extract_matrix_auto();

    select_env(SRC_ENV);

    /* bye */
    exit(EXIT_SUCCESS);
}
