/****************************************************************************
 *
 * MODULE:       r.lfp
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Calculates the longest flow paths from a flow direction raster
 *               map and a outlets vector map using the Memory-Efficient
 *               Longest Flow Path (MELFP) OpenMP parallel algorithm by Cho
 *               (2025).
 *
 * COPYRIGHT:    (C) 2025 by Huidae Cho and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#define _MAIN_C_

#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef _OPENMP
#include <omp.h>
#endif
#ifdef _MSC_VER
#include <winsock2.h>
#else
#include <sys/time.h>
#endif
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"
#include "lfp_funcs.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *dir;
        struct Option *format;
        struct Option *encoding;
        struct Option *outlets;
        struct Option *layer;
        struct Option *idcol;
        struct Option *lfp;
        struct Option *heads;
        struct Option *coors;
        struct Option *oidcol;
#ifdef _OPENMP
#ifdef LOOP_THEN_TASK
        struct Option *tss;
#endif
        struct Option *nprocs;
#endif
    } opt;
    struct {
        struct Flag *find_full;
    } flag;
    char *desc;
    char *dir_name, *format, *encoding, *outlets_name, *layer, *idcol,
        *lfp_name, *heads_name, *coors_path, *oidcol;
#ifdef _OPENMP
    int num_threads;
#endif
    int find_full;
    struct raster_map *dir_map;
    struct outlet_list *outlet_l;
    int i;
    int num_lfp;
    struct timeval first_time, start_time, end_time;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("longest flow path"));
    module->description =
        _("Calculates the longest flow paths from a flow direction raster map "
          "and a outlets vector map using the Memory-Efficient Longest Flow "
          "Path (MELFP) OpenMP parallel algorithm by Cho (2025).");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
    opt.dir->key = "direction";
    opt.dir->description = _("Name of input flow direction raster map");

    opt.format = G_define_option();
    opt.format->type = TYPE_STRING;
    opt.format->key = "format";
    opt.format->label = _("Format of input flow direction raster map");
    opt.format->required = YES;
    opt.format->options = "auto,degree,45degree,power2,taudem,custom";
    opt.format->answer = "auto";
    G_asprintf(
        &desc, "auto;%s;degree;%s;45degree;%s;power2;%s;taudem;%s;custom;%s",
        _("auto-detect direction format except taudem"),
        _("degrees CCW from East"),
        _("degrees CCW from East divided by 45 (e.g. r.watershed)"),
        _("powers of 2 CW from East (e.g., r.terraflow, ArcGIS)"),
        _("1-8 for E-SE CCW, not auto-detected (e.g., TauDEM D8FlowDir)"),
        _("use encoding"));
    opt.format->descriptions = desc;

    opt.encoding = G_define_option();
    opt.encoding->type = TYPE_STRING;
    opt.encoding->key = "encoding";
    opt.encoding->label = _("Flow direction encoding for custom format");
    opt.encoding->required = NO;
    opt.encoding->description = _("Eight integers for E,SE,S,SW,W,NW,N,NE");

    opt.outlets = G_define_standard_option(G_OPT_V_INPUT);
    opt.outlets->key = "outlets";
    opt.outlets->label = _("Name of input outlets vector map");
    opt.outlets->required = YES;

    opt.layer = G_define_standard_option(G_OPT_V_FIELD);

    opt.idcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.idcol->label = _("Name of input attribute column for outlet IDs");
    opt.idcol->answer = GV_KEY_COLUMN;
    G_asprintf(&desc,
               _("Using a non-%s column is slower because of database access"),
               GV_KEY_COLUMN);
    opt.idcol->description = desc;

    opt.lfp = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.lfp->key = "lfp";
    opt.lfp->required = NO;
    opt.lfp->description = _("Name for output longest flow paths vector map");

    opt.heads = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.heads->key = "heads";
    opt.heads->required = NO;
    opt.heads->description =
        _("Name for output longest flow path heads vector map");

    opt.coors = G_define_standard_option(G_OPT_F_OUTPUT);
    opt.coors->key = "coordinates";
    opt.coors->required = NO;
    opt.coors->description =
        _("Name for output longest flow path head coordinates file");

    opt.oidcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.oidcol->key = "output_column";
    opt.oidcol->description =
        _("Name for output attribute column for outlet IDs");

#ifdef _OPENMP
#ifdef LOOP_THEN_TASK
    opt.tss = G_define_option();
    opt.tss->type = TYPE_INTEGER;
    opt.tss->key = "tss";
    opt.tss->label =
        _("Threshold size of tracing stack for switching to tasking");
    opt.tss->options = "0-";
    opt.tss->answer = "3072";
    opt.tss->description = _("0: guess using sqrt(cells) / threads");
#endif

    opt.nprocs = G_define_standard_option(G_OPT_M_NPROCS);
#endif

    flag.find_full = G_define_flag();
    flag.find_full->key = 'f';
    flag.find_full->label = _("Find full longest flow paths");

    G_option_required(opt.lfp, opt.heads, opt.coors, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    format = opt.format->answer;
    encoding = opt.encoding->answer;
    outlets_name = opt.outlets->answer;
    layer = opt.layer->answer;
    idcol = opt.idcol->answer;
    lfp_name = opt.lfp->answer;
    heads_name = opt.heads->answer;
    coors_path = opt.coors->answer;
    oidcol = opt.oidcol->answer;

    find_full = flag.find_full->answer;

    if (strcmp(format, "custom") == 0 && !encoding)
        G_fatal_error(_("Custom format requires <%s>"), opt.encoding->key);

#ifdef _OPENMP
    num_threads = G_set_omp_num_threads(opt.nprocs);
    if (num_threads > 1) {
        G_message(_("Parallel computing using %d threads..."), num_threads);
#ifdef LOOP_THEN_TASK
        tracing_stack_size = atoi(opt.tss->answer);
        if (tracing_stack_size <= 0) {
            G_message(_(
                "Guessing tracing stack size using sqrt(cells) / threads..."));
            tracing_stack_size =
                sqrt((size_t)Rast_window_rows() * Rast_window_cols()) /
                num_threads;
        }
        G_message(_("Tracing stack size for loop-then-task: %d"),
                  tracing_stack_size);
#endif
    }
    else
#endif
        G_message(_("Sequential computing..."));

    /* read flow direction raster */
    G_message(_("Reading flow direction raster <%s>..."), dir_name);
    gettimeofday(&start_time, NULL);
    first_time = start_time;
    dir_map = read_direction(dir_name, format, encoding);
    gettimeofday(&end_time, NULL);
    G_message(_("Input time for flow direction: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    G_message(_("Number of cells: %zu"),
              (size_t)dir_map->nrows * dir_map->ncols);

    /* read outlets vector */
    G_message(_("Reading outlets vector <%s>..."), outlets_name);
    gettimeofday(&start_time, NULL);
    outlet_l = read_outlets(outlets_name, layer, idcol, dir_map, find_full);
    gettimeofday(&end_time, NULL);
    G_message(_("Input time for outlets: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    G_message(_("Number of outlets: %d"), outlet_l->n);

    /* find longest flow paths */
    G_message(_("Finding longest flow paths..."));
    gettimeofday(&start_time, NULL);
    /* preserve direction only for lfp_name */
    lfp_lessmem(dir_map, outlet_l, find_full, lfp_name != NULL);
    gettimeofday(&end_time, NULL);
    G_message(_("Computation time for longest flow paths: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    num_lfp = 0;
    for (i = 0; i < outlet_l->n; i++)
        num_lfp += outlet_l->head_pl[i].n;
    G_message(_("Number of longest flow paths found: %d"), num_lfp);

    if (lfp_name) {
        G_message(_("Writing longest flow path vector <%s>..."), lfp_name);
        gettimeofday(&start_time, NULL);
        write_lfp(lfp_name, oidcol, outlet_l, dir_map);
        gettimeofday(&end_time, NULL);
        G_message(_("Output time for longest flow path lines: %f seconds"),
                  timeval_diff(NULL, &end_time, &start_time) / 1e6);
    }

    if (heads_name) {
        G_message(_("Writing longest flow path heads vector <%s>..."),
                  heads_name);
        gettimeofday(&start_time, NULL);
        write_head_points(heads_name, oidcol, outlet_l);
        gettimeofday(&end_time, NULL);
        G_message(
            _("Output time for longest flow path headwater points: %f seconds"),
            timeval_diff(NULL, &end_time, &start_time) / 1e6);
    }

    if (coors_path) {
        G_message(_("Writing longest flow path head coordinates file <%s>..."),
                  coors_path);
        gettimeofday(&start_time, NULL);
        write_head_coors(coors_path, oidcol, outlet_l);
        gettimeofday(&end_time, NULL);
        G_message(_("Output time for longest flow path head coordinates file: "
                    "%f seconds"),
                  timeval_diff(NULL, &end_time, &start_time) / 1e6);
    }

    free_raster_map(dir_map);
    free_outlet_list(outlet_l);

    gettimeofday(&end_time, NULL);

    G_message(_("Total elapsed time: %f seconds"),
              timeval_diff(NULL, &end_time, &first_time) / 1e6);

    exit(EXIT_SUCCESS);
}
