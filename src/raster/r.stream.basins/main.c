/****************************************************************************
 *
 * MODULE:       r.stream.basins
 * AUTHOR(S):    Jarek Jasiewicz jarekj amu.edu.pl
 *
 * PURPOSE:      Calculate basins according user' input data.
 *               It uses multiple type of inputs:
 *                  r.stream.order, r.stream.extract or r.watershed stream  map
 *               list of categories to create basins (require stream map);
 *               vector file containing outputs;
 *               list of coordinates;
 *               with analogous  direction map;
 *
 * COPYRIGHT:    (C) 2002,2010-2014 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#define MAIN

#include <grass/glocale.h>
#include "local_proto.h"

int nextr[9] = {0, -1, -1, -1, 0, 1, 1, 1, 0};
int nextc[9] = {0, 1, 0, -1, -1, -1, 0, 1, 1};

int main(int argc, char *argv[])
{

    struct GModule *module;
    struct Option *in_dir_opt, *in_coor_opt, *in_stm_opt, *in_stm_cat_opt,
        *in_point_opt, *opt_basins, *opt_swapsize;

    struct Flag *flag_zerofill, *flag_cats, *flag_lasts, *flag_segmentation;

    int b_test = 0; /* test which option has been chosen: like chmod */
    int segmentation, zerofill, lasts, cats;
    int number_of_segs, number_of_segs_total;
    double seg_size;
    int i, outlets_num = 0;
    int max_number_of_streams;
    struct Range range;
    CELL min, max;
    struct Colors colors;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->label = _("Delineates basins according stream network.");
    module->description = _("Input can be stream network, vector point map "
                            "with outlets or outlet coordinates.");
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("stream network"));
    G_add_keyword(_("basin creation"));

    in_dir_opt =
        G_define_standard_option(G_OPT_R_INPUT); /* input direction file */
    in_dir_opt->key = "direction";
    in_dir_opt->description = _("Name of input flow direction raster map");

    in_coor_opt = G_define_standard_option(
        G_OPT_M_COORDS); /* input coordinates of outlet */
    in_coor_opt->required = NO;
    in_coor_opt->multiple = YES;
    in_coor_opt->description = _("Basin's outlet's coordinates");

    in_stm_opt =
        G_define_standard_option(G_OPT_R_INPUT); /* input stream file file */
    in_stm_opt->key = "stream_rast";
    in_stm_opt->required = NO;
    in_stm_opt->description = _("Name of input stream mask raster map");
    in_stm_opt->guisection = _("Input maps");

    in_stm_cat_opt = G_define_standard_option(
        G_OPT_V_CATS); /* input stream category - optional */
    in_stm_cat_opt->required = NO;
    in_stm_cat_opt->description = _("Create basins only for these categories");

    in_point_opt = G_define_standard_option(
        G_OPT_V_INPUT); /* input point outputs - optional */
    in_point_opt->key = "points";
    in_point_opt->required = NO;
    in_point_opt->description = _("Name of input vector points map");
    in_point_opt->guisection = _("Input maps");

    opt_swapsize = G_define_option();
    opt_swapsize->key = "memory";
    opt_swapsize->type = TYPE_INTEGER;
    opt_swapsize->answer = "300";
    opt_swapsize->description =
        _("Maximum memory used in memory swap mode (MB)");
    opt_swapsize->guisection = _("Memory settings");

    opt_basins = G_define_standard_option(G_OPT_R_OUTPUT);
    opt_basins->key = "basins";
    opt_basins->description = _("Name for output basin raster map");
    opt_basins->guisection = _("Output maps");

    /*flags */
    flag_zerofill = G_define_flag();
    flag_zerofill->key = 'z';
    flag_zerofill->description =
        _("Create zero-value background instead of NULL");

    flag_cats = G_define_flag();
    flag_cats->key = 'c';
    flag_cats->description =
        _("Use unique category sequence instead of input streams");

    flag_lasts = G_define_flag();
    flag_lasts->key = 'l';
    flag_lasts->description = _("Create basins only for last stream links");

    flag_segmentation = G_define_flag();
    flag_segmentation->key = 'm';
    flag_segmentation->description = _("Use memory swap (operation is slow)");
    flag_segmentation->guisection = _("Memory settings");

    if (G_parser(argc, argv)) /* parser */
        exit(EXIT_FAILURE);

    zerofill = (flag_zerofill->answer == 0);
    cats = (flag_cats->answer != 0);
    lasts = (flag_lasts->answer != 0);
    segmentation = (flag_segmentation->answer != 0);

    if (!in_coor_opt->answers && !in_stm_opt->answer && !in_point_opt->answer)
        G_fatal_error(_("One basin's outlet definition is required"));

    if (in_stm_cat_opt->answers && !in_stm_opt->answer)
        G_fatal_error(_("Option <%s> required"), in_stm_opt->key);

    if (in_coor_opt->answers)
        b_test += 1;
    if (in_stm_opt->answer)
        b_test += 2;
    if (in_point_opt->answer)
        b_test += 4;

    if (b_test != 1 && b_test != 2 && b_test != 4)
        G_fatal_error("Only one outlet definition is allowed");

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    number_of_segs = atoi(opt_swapsize->answer);
    if (number_of_segs < 3)
        number_of_segs = 3;

    /* segment size in MB */
    seg_size = sizeof(CELL) * 2.0 * SROWS * SCOLS / (1 << 20);

    number_of_segs = (int)(number_of_segs / seg_size);

    number_of_segs_total =
        (nrows / SROWS + nrows % SROWS) * (ncols / SCOLS + ncols % SCOLS);

    if (!segmentation) {
        /* force use of the segment version
         * if not all segments can be kept in memory */
        if (number_of_segs_total > number_of_segs)
            segmentation = 1;
    }

    /* ALL IN RAM VERSION */
    if (!segmentation) {
        MAP map_dirs, map_streams, map_basins;
        CELL **streams = NULL, **dirs, **basins;

        G_message(_("All in RAM calculation..."));

        ram_create_map(&map_dirs, CELL_TYPE);
        ram_read_map(&map_dirs, in_dir_opt->answer, 1, CELL_TYPE, 0);
        dirs = (CELL **)map_dirs.map;

        switch (b_test) {
        case 1:
            G_message(_("Calculating basins using coordinates..."));
            outlets_num = process_coors(in_coor_opt->answers);
            break;

        case 2:
            G_message(_("Calculating basins using streams..."));
            ram_create_map(&map_streams, CELL_TYPE);
            ram_read_map(&map_streams, in_stm_opt->answer, 1, CELL_TYPE, 0);
            streams = (CELL **)map_streams.map;
            max_number_of_streams = (int)map_streams.max + 1;
            outlets_num =
                ram_process_streams(in_stm_cat_opt->answers, streams,
                                    max_number_of_streams, dirs, lasts, cats);
            ram_release_map(&map_streams);
            break;

        case 4:
            G_message(_("Calculating basins using vector point map..."));
            outlets_num = process_vector(in_point_opt->answer);
            break;
        }

        ram_create_map(&map_basins, CELL_TYPE);
        ram_reset_map(&map_basins, 0);
        basins = (CELL **)map_basins.map;
        ram_add_outlets(basins, outlets_num);
        fifo_max = 4 * (nrows + ncols);
        fifo_points = (POINT *)G_malloc((fifo_max + 1) * sizeof(POINT));

        G_message(_("Delineating basins for %d outlets..."), outlets_num);
        for (i = 0; i < outlets_num; ++i) {
            G_percent(i, outlets_num, 4);
            ram_fill_basins(outlets[i], basins, dirs);
        }
        G_percent(i, outlets_num, 4);

        G_free(fifo_points);
        ram_write_map(&map_basins, opt_basins->answer, CELL_TYPE, zerofill, 0);
        ram_release_map(&map_dirs);
        ram_release_map(&map_basins);

    } /* end ram */
    /* SEGMENT VERSION */
    else {
        SEG map_dirs, map_streams, map_basins;
        SEGMENT *streams = NULL, *dirs, *basins;

        G_message(_("Memory swap calculation (may take some time)..."));

        if (number_of_segs < 10)
            number_of_segs = 10;

        seg_create_map(&map_dirs, SROWS, SCOLS, number_of_segs, CELL_TYPE);
        seg_read_map(&map_dirs, in_dir_opt->answer, 1, CELL_TYPE, 0);
        dirs = &map_dirs.seg;

        switch (b_test) {
        case 1:
            G_message(_("Calculating basins using coordinates..."));
            outlets_num = process_coors(in_coor_opt->answers);
            break;

        case 2:
            G_message(_("Calculating basins using streams..."));
            seg_create_map(&map_streams, SROWS, SCOLS, number_of_segs,
                           CELL_TYPE);
            seg_read_map(&map_streams, in_stm_opt->answer, 1, CELL_TYPE, 0);
            streams = &map_streams.seg;
            max_number_of_streams = (int)map_streams.max + 1;
            outlets_num =
                seg_process_streams(in_stm_cat_opt->answers, streams,
                                    max_number_of_streams, dirs, lasts, cats);
            seg_release_map(&map_streams);
            break;

        case 4:
            G_message(_("Calculating basins using vector point map..."));
            outlets_num = process_vector(in_point_opt->answer);
            break;
        }

        seg_create_map(&map_basins, SROWS, SCOLS, number_of_segs, CELL_TYPE);
        seg_reset_map(&map_basins, 0);
        basins = &map_basins.seg;
        seg_add_outlets(basins, outlets_num);
        fifo_max = 4 * (nrows + ncols);
        fifo_points = (POINT *)G_malloc((fifo_max + 1) * sizeof(POINT));

        G_message(_("Delineating basins for %d outlets..."), outlets_num);
        for (i = 0; i < outlets_num; ++i) {
            G_percent(i, outlets_num, 4);
            seg_fill_basins(outlets[i], basins, dirs);
        }
        G_percent(i, outlets_num, 4);
        G_free(fifo_points);
        seg_write_map(&map_basins, opt_basins->answer, CELL_TYPE, zerofill, 0);
        seg_release_map(&map_dirs);
        seg_release_map(&map_basins);
    }

    Rast_read_range(opt_basins->answer, G_mapset(), &range);
    Rast_get_range_min_max(&range, &min, &max);
    Rast_make_random_colors(&colors, min, max);
    Rast_write_colors(opt_basins->answer, G_mapset(), &colors);

    exit(EXIT_SUCCESS);
}
