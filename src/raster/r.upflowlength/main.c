/****************************************************************************
 *
 * MODULE:       r.upflowlength
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Calculates upstream flow length from a flow direction raster
 *               map using the Memory-Efficient Upstream Flow Length (MEUFL)
 *               OpenMP parallel algorithm by Cho (2026).
 *
 * SPDX-FileCopyrightText: 2026 Huidae Cho
 * SPDX-FileCopyrightText: Other GRASS authors
 * SPDX-License-Identifier: GPL-2.0-or-later
 *****************************************************************************/
#include <stdlib.h>
#include <string.h>
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
#define USE_LEAST_MEMORY
#include "uflen_funcs.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *dir;
        struct Option *format;
        struct Option *encoding;
        struct Option *uflen;
#ifdef _OPENMP
        struct Option *nprocs;
#endif
    } opt;
    char *desc;
    char *dir_name, *format, *encoding, *uflen_name;
    int num_threads = 0;
    struct raster_map *dir_map;
    struct History hist;
    struct timeval first_time, start_time, end_time;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("upstream flow length"));
    module->description =
        _("Calculates upstream flow length from a flow direction raster map "
          "using the Memory-Efficient Upstream Flow Length (MEUFL) OpenMP "
          "parallel algorithm by Cho (2026).");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
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

    opt.uflen = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.uflen->description = _("Name for output longest flow paths vector map");

#ifdef _OPENMP
    opt.nprocs = G_define_standard_option(G_OPT_M_NPROCS);
#endif

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    format = opt.format->answer;
    encoding = opt.encoding->answer;
    uflen_name = opt.uflen->answer;

    if (strcmp(format, "custom") == 0 && !encoding)
        G_fatal_error(_("Custom format requires <%s>"), opt.encoding->key);

#ifdef _OPENMP
#if GRASS_VERSION_MAJOR >= 8 && GRASS_VERSION_MINOR >= 5
    num_threads = G_set_omp_num_threads(opt.nprocs);
#else
    if ((num_threads = atoi(opt.nprocs->answer)) == 0)
        num_threads = omp_get_max_threads();
    else {
        if (num_threads < 1) {
            num_threads += omp_get_num_procs();
            num_threads = num_threads < 1 ? 1 : num_threads;
        }
        omp_set_num_threads(num_threads);
    }
#endif
    if (num_threads > 1)
        G_message(_("Parallel computing using %d threads..."), num_threads);
    else
#endif
        G_message(_("Serial computing..."));

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

    /* calculate upstream flow length */
    G_message(_("Calculating upstream flow length..."));
    gettimeofday(&start_time, NULL);

    uflen_leastmem(dir_map, 0);
    nullify_raster_map(dir_map);

    gettimeofday(&end_time, NULL);
    G_message(_("Computation time for upstream flow length: %lf seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* write upstream flow length raster */
    G_message(_("Writing upstream flow length raster <%s>..."), uflen_name);
    gettimeofday(&start_time, NULL);

    write_raster_map(dir_map, uflen_name);
    free_raster_map(dir_map);

    /* write history */
    Rast_put_cell_title(uflen_name, _("Upstream flow length"));
    Rast_short_history(uflen_name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(uflen_name, &hist);

    gettimeofday(&end_time, NULL);
    G_message(_("Output time for upstream flow length: %lf seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    gettimeofday(&end_time, NULL);
    G_message(_("Total elapsed time: %lf seconds"),
              timeval_diff(NULL, &end_time, &first_time) / 1e6);

    exit(EXIT_SUCCESS);
}
