/****************************************************************************
 *
 * MODULE:       r.flowaccumulation
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Calculates flow accumulation from a flow direction raster map
 *               using the Memory-Efficient Flow Accumulation (MEFA) parallel
 *               algorithm by Cho (2023).
 *
 * COPYRIGHT:    (C) 2023 by Huidae Cho and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <math.h>
#ifdef _MSC_VER
#include <winsock2.h>
#else
#include <sys/time.h>
#endif
#ifdef _OPENMP
#include <omp.h>
#endif
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

#define DIR_UNKNOWN 0
#define DIR_DEG     1
#define DIR_DEG45   2
#define DIR_POW2    3

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *dir;
        struct Option *format;
        struct Option *accum;
        struct Option *type;
        struct Option *nprocs;
    } opt;
    struct {
        struct Flag *check_overflow;
        struct Flag *use_less_memory;
        struct Flag *use_zero;
        struct Flag *leave_zero;
    } flag;
    char *desc;
    char *dir_name, *format, *accum_name, *type;
#ifdef _OPENMP
    int nprocs;
#endif
    int check_overflow, use_less_memory, use_zero;
    int dir_fd, accum_fd;
    unsigned char dir_format;
    struct Range dir_range;
    CELL dir_min, dir_max, *dir_buf;
    struct raster_map *dir_map, *accum_map;
    int nrows, ncols, row, col;
    struct History hist;
    struct timeval first_time, start_time, end_time;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("accumulation"));
    module->description =
        _("Calculates flow accumulation from a flow direction raster map using "
          "the Memory-Efficient Flow Accumulation (MEFA) parallel algorithm by "
          "Cho (2023).");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
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

    opt.accum = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.accum->description = _("Name for output flow accumulation raster map");

    opt.type = G_define_standard_option(G_OPT_R_TYPE);
    opt.type->answer = "CELL";

#ifdef _OPENMP
    opt.nprocs = G_define_standard_option(G_OPT_M_NPROCS);
#endif

    flag.check_overflow = G_define_flag();
    flag.check_overflow->key = 'o';
    flag.check_overflow->label = _("Check overflow and exit if it occurs");

    flag.use_less_memory = G_define_flag();
    flag.use_less_memory->key = 'm';
    flag.use_less_memory->label = _("Use less memory");

    flag.use_zero = G_define_flag();
    flag.use_zero->key = 'z';
    flag.use_zero->label = _("Initialize to zero and nullify it later");

    flag.leave_zero = G_define_flag();
    flag.leave_zero->key = 'Z';
    flag.leave_zero->label =
        _("Initialize to and leave zero instead of nullifying it");

    G_option_exclusive(flag.use_zero, flag.leave_zero, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    format = opt.format->answer;
    accum_name = opt.accum->answer;
    type = opt.type->answer;

#ifdef _OPENMP
    nprocs = atoi(opt.nprocs->answer);
    if (nprocs < 1)
        G_fatal_error(_("<%s> must be >= 1"), opt.nprocs->key);

    omp_set_num_threads(nprocs);
    nprocs = omp_get_max_threads();
    G_message(n_("Using %d thread for serial computation",
                 "Using %d threads for parallel computation", nprocs),
              nprocs);
#endif

    check_overflow = flag.check_overflow->answer;
    use_less_memory = flag.use_less_memory->answer;
    use_zero = flag.use_zero->answer ? 1 : 2 * flag.leave_zero->answer;

    /* read direction raster */
    G_message(_("Reading flow direction raster <%s>..."), dir_name);
    gettimeofday(&start_time, NULL);
    first_time = start_time;

    dir_fd = Rast_open_old(dir_name, "");
    if (Rast_get_map_type(dir_fd) != CELL_TYPE)
        G_fatal_error(_("Invalid direction map <%s>"), dir_name);

    /* adapted from r.path */
    if (Rast_read_range(dir_name, "", &dir_range) < 0)
        G_fatal_error(_("Unable to read range file"));
    Rast_get_range_min_max(&dir_range, &dir_min, &dir_max);
    if (dir_max <= 0)
        G_fatal_error(_("Invalid direction map <%s>"), dir_name);

    dir_format = DIR_UNKNOWN;
    if (strcmp(format, "degree") == 0) {
        if (dir_max > 360)
            G_fatal_error(_("Directional degrees cannot be > 360"));
        dir_format = DIR_DEG;
    }
    else if (strcmp(format, "45degree") == 0) {
        if (dir_max > 8)
            G_fatal_error(_("Directional degrees divided by 45 cannot be > 8"));
        dir_format = DIR_DEG45;
    }
    else if (strcmp(format, "power2") == 0) {
        if (dir_max > 128)
            G_fatal_error(_("Powers of 2 cannot be > 128"));
        dir_format = DIR_POW2;
    }
    else if (strcmp(format, "auto") == 0) {
        if (dir_max <= 8) {
            dir_format = DIR_DEG45;
            G_important_message(_("Flow direction format assumed to be "
                                  "degrees CCW from East divided by 45"));
        }
        else if (dir_max <= 128) {
            dir_format = DIR_POW2;
            G_important_message(_("Flow direction format assumed to be "
                                  "powers of 2 CW from East"));
        }
        else if (dir_max <= 360) {
            dir_format = DIR_DEG;
            G_important_message(
                _("Flow direction format assumed to be degrees CCW from East"));
        }
        else
            G_fatal_error(
                _("Unable to detect format of input direction map <%s>"),
                dir_name);
    }
    if (dir_format == DIR_UNKNOWN)
        G_fatal_error(_("Invalid direction format '%s'"), format);
    /* end of r.path */

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    dir_map = G_malloc(sizeof *dir_map);
    dir_map->nrows = nrows;
    dir_map->ncols = ncols;
    dir_map->cells.v = G_calloc((size_t)nrows * ncols, 1);
    dir_buf = G_malloc(sizeof(CELL) * ncols);

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        Rast_get_c_row(dir_fd, dir_buf, row);
        if (dir_format == DIR_DEG) {
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, abs(dir_buf[col] / 45.));
        }
        else if (dir_format == DIR_DEG45) {
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = pow(2, 8 - abs(dir_buf[col]));
        }
        else {
            for (col = 0; col < ncols; col++)
                if (!Rast_is_c_null_value(&dir_buf[col]))
                    DIR(row, col) = abs(dir_buf[col]);
        }
    }
    G_percent(1, 1, 1);
    G_free(dir_buf);
    Rast_close(dir_fd);

    gettimeofday(&end_time, NULL);
    G_message(_("Input time for flow direction: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* accumulate flow */
    G_message(_("Accumulating flows..."));
    gettimeofday(&start_time, NULL);

    accum_map = G_malloc(sizeof *accum_map);
    accum_map->nrows = nrows;
    accum_map->ncols = ncols;

    if (strcmp(type, "CELL") == 0) {
        accum_map->type = CELL_TYPE;
        accum_map->cell_size = sizeof(CELL);
    }
    else if (strcmp(type, "FCELL") == 0) {
        accum_map->type = FCELL_TYPE;
        accum_map->cell_size = sizeof(FCELL);
    }
    else {
        accum_map->type = DCELL_TYPE;
        accum_map->cell_size = sizeof(DCELL);
    }

    if (use_zero)
        accum_map->cells.v =
            G_calloc((size_t)nrows * ncols, accum_map->cell_size);
    else
        accum_map->cells.v = G_malloc(accum_map->cell_size * nrows * ncols);

    accumulate(dir_map, accum_map, check_overflow, use_less_memory, use_zero);

    G_free(dir_map->cells.v);
    G_free(dir_map);

    if (use_zero == 1)
        nullify_zero(accum_map);

    gettimeofday(&end_time, NULL);
    G_message(_("Compute time for flow accumulation: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    /* write out buffer to accumulation raster */
    G_message(_("Writing flow accumulation raster <%s>..."), accum_name);
    gettimeofday(&start_time, NULL);

    accum_fd = Rast_open_new(accum_name, accum_map->type);
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        Rast_put_row(accum_fd,
                     accum_map->cells.v + accum_map->cell_size * ncols * row,
                     accum_map->type);
    }
    G_percent(1, 1, 1);
    Rast_close(accum_fd);

    G_free(accum_map->cells.v);
    G_free(accum_map);

    /* write history */
    Rast_put_cell_title(accum_name, _("Flow accumulation"));
    Rast_short_history(accum_name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(accum_name, &hist);

    gettimeofday(&end_time, NULL);
    G_message(_("Output time for flow accumulation: %f seconds"),
              timeval_diff(NULL, &end_time, &start_time) / 1e6);

    G_message(_("Total elapsed time: %f seconds"),
              timeval_diff(NULL, &end_time, &first_time) / 1e6);

    exit(EXIT_SUCCESS);
}
