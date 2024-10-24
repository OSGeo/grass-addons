/****************************************************************************
 *
 * MODULE:       r.watersheds
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Delineate a large number of watersheds using the
 *               Memory-Efficient Watershed Delineation (MESHED) OpenMP
 *               parallel algorithm by Cho (2025).
 *
 * COPYRIGHT:    (C) 2024 by Huidae Cho and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#ifdef _MSC_VER
#include <winsock2.h>
#else
#include <sys/time.h>
#endif
#ifdef _OPENMP
#include <omp.h>
#endif
#include <grass/glocale.h>
#include "global.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *dir;
        struct Option *format;
        struct Option *outlets;
        struct Option *layer;
        struct Option *idcol;
        struct Option *wsheds;
        struct Option *nprocs;
    } opt;
    struct {
        struct Flag *use_less_memory;
    } flag;
    char *desc;
    char *dir_name, *format, *outlets_name, *layer, *idcol, *wsheds_name;
#ifdef _OPENMP
    int nprocs;
#endif
    int use_less_memory;
    struct raster_map *dir_map;
    struct outlet_list *outlets_l;
    struct timeval first_time, start_time, end_time;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("watershed delineation"));
    module->description = _("Delineate a large number of watersheds using the "
                            "Memory-Efficient Watershed Delineation (MESHED) "
                            "OpenMP parallel algorithm by Cho (2024).");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
    opt.dir->key = "direction";
    opt.dir->description = _("Name of input direction raster map");

    opt.format = G_define_option();
    opt.format->type = TYPE_STRING;
    opt.format->key = "format";
    opt.format->label = _("Format of input direction raster map");
    opt.format->required = YES;
    opt.format->options = "auto,degree,45degree,power2";
    opt.format->answer = "auto";
    G_asprintf(&desc, "auto;%s;degree;%s;45degree;%s;power2;%s",
               _("auto-detect direction format"), _("degrees CCW from East"),
               _("degrees CCW from East divided by 45 (e.g. r.watershed)"),
               _("powers of 2 CW from East (e.g., r.terraflow, ArcGIS)"));
    opt.format->descriptions = desc;

    opt.outlets = G_define_standard_option(G_OPT_V_INPUT);
    opt.outlets->key = "outlets";
    opt.outlets->required = YES;
    opt.outlets->label = _("Name of input outlets vector map");

    opt.layer = G_define_standard_option(G_OPT_V_FIELD);

    opt.idcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.idcol->description = _("Name of attribute column for watershed IDs");
    opt.idcol->answer = GV_KEY_COLUMN;

    opt.wsheds = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.wsheds->description = _("Name for output watersheds raster map");

#ifdef _OPENMP
    opt.nprocs = G_define_standard_option(G_OPT_M_NPROCS);
#endif

    flag.use_less_memory = G_define_flag();
    flag.use_less_memory->key = 'm';
    flag.use_less_memory->label = _("Use less memory");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    format = opt.format->answer;
    outlets_name = opt.outlets->answer;
    layer = opt.layer->answer;
    idcol = opt.idcol->answer;
    wsheds_name = opt.wsheds->answer;

#ifdef _OPENMP
    nprocs = atoi(opt.nprocs->answer);
    if (nprocs < 1)
        G_fatal_error(_("<%s> must be >= 1"), opt.nprocs->key);

    omp_set_num_threads(nprocs);
#pragma omp parallel
#pragma omp single
    nprocs = omp_get_num_threads();
    G_message(n_("Using %d thread for serial computation",
                 "Using %d threads for parallel computation", nprocs),
              nprocs);
#endif

    use_less_memory = flag.use_less_memory->answer;

    /* read direction raster */
    G_message(_("Reading flow direction raster <%s>..."), dir_name);
    gettimeofday(&start_time, NULL);
    first_time = start_time;

    dir_map = read_direction(dir_name, format);

    gettimeofday(&end_time, NULL);
    G_message(_("Input time for flow direction: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* read outlets vector */
    G_message(_("Reading outlets vector <%s>..."), outlets_name);
    gettimeofday(&start_time, NULL);

    outlets_l = read_outlets(outlets_name, layer, idcol);

    gettimeofday(&end_time, NULL);
    G_message(_("Input time for outlets: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* watershed delineation */
    G_message(_("Delineating watersheds..."));
    gettimeofday(&start_time, NULL);

    delineate(dir_map, outlets_l, use_less_memory);

    free_outlet_list(outlets_l);

    gettimeofday(&end_time, NULL);
    G_message(_("Compute time for watershed delineation: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* write out buffer to watersheds raster */
    G_message(_("Writing watersheds raster <%s>..."), wsheds_name);
    gettimeofday(&start_time, NULL);

    write_watersheds(wsheds_name, dir_map);

    free_raster_map(dir_map);

    gettimeofday(&end_time, NULL);
    G_message(_("Output time for watershed delineation: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    G_message(_("Total elapsed time: %f seconds"),
              timeval_diff(NULL, &end_time, &first_time) / 1e6);

    exit(EXIT_SUCCESS);
}
