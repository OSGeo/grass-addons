/****************************************************************************
 *
 * MODULE:       r.hydrodem
 * AUTHOR(S):    Markus Metz <markus.metz.giswork gmail.com>
 * PURPOSE:      Hydrological analysis
 *               DEM hydrological conditioning based on A* Search
 * COPYRIGHT:    (C) 1999-2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

struct snode *stream_node;
int nrows, ncols;
GW_LARGE_INT n_search_points, n_points, nxt_avail_pt;
GW_LARGE_INT heap_size;
int n_sinks;
int n_mod_max, size_max;
int do_all, force_filling, force_carving, keep_nat, nat_thresh;
GW_LARGE_INT n_stream_nodes, n_alloc_nodes;
struct point *outlets;
struct sink_list *sinks, *first_sink;
GW_LARGE_INT n_outlets, n_alloc_outlets;

char drain[3][3] = {{7, 6, 5}, {8, 0, 4}, {1, 2, 3}};

GW_LARGE_INT first_cum;
char sides;
int c_fac;
int ele_scale;
struct RB_TREE *draintree;

SSEG search_heap;
SSEG dirflag;
/*
BSEG bitflags;
BSEG draindir;
*/
CSEG ele;
CSEG stream;

int main(int argc, char *argv[])
{
    struct {
        struct Option *ele, *depr, *memory;
    } input;
    struct {
        struct Option *ele_hydro;
        struct Option *mod_max;
        struct Option *size_max;
        struct Flag *do_all;
        struct Flag *force_filling;
        struct Flag *force_carving;
    } output;
    struct GModule *module;
    int ele_fd, ele_map_type, depr_fd;
    int memory;
    int seg_cols, seg_rows;
    double seg2kb;
    int num_open_segs, num_open_array_segs, num_seg_total;
    double memory_divisor, heap_mem, disk_space;
    const char *mapset;
    struct Colors colors;

    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    module->description = _("Hydrological conditioning, sink removal");

    input.ele = G_define_standard_option(G_OPT_R_INPUT);
    input.ele->key = "input";
    input.ele->label = _("Elevation map");
    input.ele->description = _("Elevation map to be hydrologically corrected");

    input.depr = G_define_standard_option(G_OPT_R_INPUT);
    input.depr->key = "depression";
    input.depr->required = NO;
    input.depr->label = _("Depression map");
    input.depr->description =
        _("Map indicating real depressions that must not be modified");

    input.memory = G_define_option();
    input.memory->key = "memory";
    input.memory->type = TYPE_INTEGER;
    input.memory->required = NO;
    input.memory->answer = "300";
    input.memory->description = _("Maximum memory to be used in MB");

    output.ele_hydro = G_define_standard_option(G_OPT_R_OUTPUT);
    output.ele_hydro->key = "output";
    output.ele_hydro->description =
        _("Name of hydrologically conditioned raster map");
    output.ele_hydro->required = YES;

    output.mod_max = G_define_option();
    output.mod_max->key = "mod";
    output.mod_max->description = (_(
        "Only remove sinks requiring not more than <mod> cell modifications."));
    output.mod_max->type = TYPE_INTEGER;
    output.mod_max->answer = "4";
    output.mod_max->required = YES;

    output.size_max = G_define_option();
    output.size_max->key = "size";
    output.size_max->description =
        (_("Only remove sinks not larger than <size> cells."));
    output.size_max->type = TYPE_INTEGER;
    output.size_max->answer = "4";
    output.size_max->required = YES;

    output.do_all = G_define_flag();
    output.do_all->key = 'a';
    output.do_all->label = (_("Remove all sinks."));
    output.do_all->description =
        (_("By default only minor corrections are done to the DEM and "
           "the result will not be 100% hydrologically correct."
           "Use this flag to override default."));

    output.force_filling = G_define_flag();
    output.force_filling->key = 'f';
    output.force_filling->label = (_("Fill sinks."));
    output.force_filling->description =
        (_("By default a least impact approach is used to modify the DEM."
           "Use this flag to force filling of sinks."));

    output.force_carving = G_define_flag();
    output.force_carving->key = 'c';
    output.force_carving->label = (_("Carve out of sinks."));
    output.force_carving->description =
        (_("By default a least impact approach is used to modify the DEM."
           "Use this flag to force carving out of sinks."));

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /***********************/
    /*    check options    */
    /***********************/

    /* input maps exist ? */
    if (!G_find_raster(input.ele->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"), input.ele->answer);

    if (input.depr->answer) {
        if (!G_find_raster(input.depr->answer, ""))
            G_fatal_error(_("Raster map <%s> not found"), input.depr->answer);
    }

    if ((n_mod_max = atoi(output.mod_max->answer)) <= 0)
        G_fatal_error(_("'%s' must be a positive integer"),
                      output.mod_max->key);

    if ((size_max = atoi(output.size_max->answer)) <= 0)
        G_fatal_error(_("'%s' must be a positive integer"),
                      output.size_max->key);

    if (input.memory->answer) {
        memory = atoi(input.memory->answer);
        if (memory <= 0)
            G_fatal_error(_("Memory must be positive but is %d"), memory);
    }
    else
        memory = 300;

    do_all = output.do_all->answer;

    if (!do_all) {
        G_verbose_message(
            _("All sinks with max %d cells to be modified will be removed"),
            n_mod_max);
        G_verbose_message(
            _("All sinks not larger than %d cells will be removed."), size_max);
    }

    force_filling = output.force_filling->answer;

    if (force_filling) {
        G_verbose_message(
            _("Least impact approach is disabled, sinks will be filled."));
    }

    force_carving = output.force_carving->answer;

    if (force_carving) {
        G_verbose_message(_("Least impact approach is disabled, sinks will be "
                            "removed by carving."));
    }

    /*********************/
    /*    preparation    */
    /*********************/

    /* open input maps */
    mapset = G_find_raster2(input.ele->answer, "");
    ele_fd = Rast_open_old(input.ele->answer, mapset);
    if (ele_fd < 0)
        G_fatal_error(_("Could not open input map %s"), input.ele->answer);

    if (input.depr->answer) {
        mapset = G_find_raster2(input.depr->answer, "");
        depr_fd = Rast_open_old(input.depr->answer, mapset);
        if (depr_fd < 0)
            G_fatal_error(_("Could not open input map %s"), input.depr->answer);
    }
    else
        depr_fd = -1;

    /* set global variables */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    sides = 8; /* not a user option */

    ele_map_type = Rast_get_map_type(ele_fd);

    /* segment structures */
    seg_rows = seg_cols = 64;
    seg2kb = seg_rows * seg_cols / 1024.;

    /* balance segment files */
    /* elevation: * 2 */
    memory_divisor = seg2kb * sizeof(CELL) * 2;
    /* flags + directions: * 2 */
    memory_divisor += seg2kb * sizeof(struct dir_flag) * 2;
    /* heap points: / 4 */
    memory_divisor += seg2kb * sizeof(struct heap_point) / 4.;

    /* KB -> MB */
    memory_divisor /= 1024.;

    num_open_segs = memory / memory_divisor;
    /* heap_mem is in MB */
    heap_mem =
        num_open_segs * seg2kb * sizeof(struct heap_point) / (4. * 1024.);
    num_seg_total = (ncols / seg_cols + 1) * (nrows / seg_rows + 1);
    if (num_open_segs > num_seg_total) {
        heap_mem += (num_open_segs - num_seg_total) * memory_divisor;
        heap_mem -= (num_open_segs - num_seg_total) * seg2kb *
                    sizeof(struct heap_point) / (4. * 1024.);
        num_open_segs = num_seg_total;
    }
    if (num_open_segs < 16) {
        num_open_segs = 16;
        heap_mem =
            num_open_segs * seg2kb * sizeof(struct heap_point) / (4. * 1024.);
    }
    disk_space = (1. * sizeof(CELL) + sizeof(struct dir_flag) +
                  sizeof(struct heap_point));
    disk_space *= (num_seg_total * seg2kb / 1024.); /* KB -> MB */

    G_verbose_message(_("%.2f%% of data are kept in memory"),
                      100. * num_open_segs / num_seg_total);
    G_verbose_message(_("Will need up to %.2f MB of disk space"), disk_space);

    /* open segment files */
    G_verbose_message(_("Create temporary files..."));

    if (cseg_open(&ele, seg_rows, seg_cols, num_open_segs * 2) != 0) {
        G_fatal_error(_("Could not create cache for elevation"));
    }
    if (num_open_segs * 2 > num_seg_total)
        heap_mem +=
            (num_open_segs * 2 - num_seg_total) * seg2kb * sizeof(CELL) / 1024.;

    if (seg_open(&dirflag, nrows, ncols, seg_rows, seg_cols, num_open_segs * 2,
                 sizeof(struct dir_flag)) != 0) {
        G_fatal_error(_("Could not create cache for directions"));
    }

    if (num_open_segs * 4 > num_seg_total)
        heap_mem += (num_open_segs * 4 - num_seg_total) * seg2kb / 1024.;

    /* load map */
    if (load_map(ele_fd) < 0) {
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("Could not load input map"));
    }

    if (n_points == 0) {
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("No non-NULL cells loaded from input map"));
    }

    /* one-based d-ary search_heap */
    G_debug(1, "open segments for A* search heap");

    /* allowed memory for search heap in MB */
    G_debug(1, "heap memory %.2f MB", heap_mem);
    /* columns per segment */
    /* larger is faster */
    seg_cols = seg_rows * seg_rows * seg_rows;
    num_seg_total = n_points / seg_cols;
    if (n_points % seg_cols > 0)
        num_seg_total++;
    /* no need to have more segments open than exist */
    num_open_array_segs =
        (1 << 20) * heap_mem / (seg_cols * sizeof(struct heap_point));
    if (num_open_array_segs > num_seg_total)
        num_open_array_segs = num_seg_total;
    if (num_open_array_segs < 2)
        num_open_array_segs = 2;

    G_debug(1, "A* search heap open segments %d, total %d", num_open_array_segs,
            num_seg_total);
    G_debug(1, "segment size for heap points: %d", seg_cols);
    /* the search heap will not hold more than 5% of all points at any given
     * time ? */
    /* chances are good that the heap will fit into one large segment */
    if (seg_open(&search_heap, 1, n_points + 1, 1, seg_cols,
                 num_open_array_segs, sizeof(struct heap_point)) != 0) {
        G_fatal_error(_("Could not create cache for the A* search heap"));
    }

    /********************/
    /*    processing    */
    /********************/

    /* remove one cell extrema */
    one_cell_extrema(1, 1, 0);

    /* initialize A* search */
    if (init_search(depr_fd) < 0) {
        seg_close(&search_heap);
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("Could not initialize search"));
    }

    if (depr_fd >= 0) {
        Rast_close(depr_fd);
    }

    /* sort elevation and get initial stream direction */
    if (do_astar() < 0) {
        seg_close(&search_heap);
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("Could not sort elevation map"));
    }
    seg_close(&search_heap);

    /* hydrological corrections */
    if (hydro_con() < 0) {
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("Could not apply hydrological conditioning"));
    }

    /* write output maps */
    if (close_map(output.ele_hydro->answer, ele_map_type) < 0) {
        cseg_close(&ele);
        seg_close(&dirflag);
        G_fatal_error(_("Could not write output map"));
    }

    cseg_close(&ele);
    seg_close(&dirflag);

    Rast_read_colors(input.ele->answer, mapset, &colors);
    Rast_write_colors(output.ele_hydro->answer, G_mapset(), &colors);

    exit(EXIT_SUCCESS);
}
