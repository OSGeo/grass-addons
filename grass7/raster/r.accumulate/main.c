
/****************************************************************************
 *
 * MODULE:       r.accumulate
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Calculates weighted flow accumulation using a flow direction
 *               map.
 *
 * COPYRIGHT:    (C) 2018 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

#define DIR_UNKNOWN 0
#define DIR_DEG 1
#define DIR_DEG45 2

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct
    {
        struct Option *dir, *format, *weight, *acc;
    } opt;
    struct
    {
        struct Flag *neg;
    } flag;
    char *desc;
    char *dir_name, *weight_name, *acc_name;
    int dir_fd, weight_fd, acc_fd;
    double dir_format;
    struct Range dir_range;
    CELL dir_min, dir_max;
    char neg;
    char **done;
    CELL **dir_buf;
    RASTER_MAP weight_buf, acc_buf;
    int rows, cols, row, col;
    struct History hist;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    module->description =
        _("Calculates weighted flow accumulation using a flow direction map.");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
    opt.dir->description = _("Name of input direction map");

    opt.format = G_define_option();
    opt.format->type = TYPE_STRING;
    opt.format->key = "format";
    opt.format->label = _("Format of input direction map");
    opt.format->required = YES;
    opt.format->options = "auto,degree,45degree";
    opt.format->answer = "auto";
    G_asprintf(&desc, "auto;%s;degree;%s;45degree;%s",
               _("auto-detect direction format"),
               _("degrees CCW from East"),
               _("degrees CCW from East divided by 45 (e.g. r.watershed directions)"));
    opt.format->descriptions = desc;

    opt.weight = G_define_standard_option(G_OPT_R_INPUT);
    opt.weight->key = "weight";
    opt.weight->required = NO;
    opt.weight->description = _("Name of input flow weight map");

    opt.acc = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.acc->type = TYPE_STRING;
    opt.acc->description =
        _("Name for output weighted flow accumulation map");

    flag.neg = G_define_flag();
    flag.neg->key = 'n';
    flag.neg->label =
        _("Use negative flow accumulation for likely underestimates");

    G_option_exclusive(opt.weight, flag.neg, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    weight_name = opt.weight->answer;
    acc_name = opt.acc->answer;

    dir_fd = Rast_open_old(dir_name, "");
    if (Rast_get_map_type(dir_fd) != CELL_TYPE)
        G_fatal_error(_("Invalid directions map <%s>"), dir_name);

    /* adapted from r.path */
    if (Rast_read_range(dir_name, "", &dir_range) < 0)
        G_fatal_error(_("Unable to read range file"));
    Rast_get_range_min_max(&dir_range, &dir_min, &dir_max);
    if (dir_max <= 0)
        G_fatal_error(_("Invalid directions map <%s>"), dir_name);

    dir_format = DIR_UNKNOWN;
    if (strcmp(opt.format->answer, "degree") == 0) {
        if (dir_max > 360)
            G_fatal_error(_("Directional degrees can not be > 360"));
        dir_format = DIR_DEG;
    }
    else if (strcmp(opt.format->answer, "45degree") == 0) {
        if (dir_max > 8)
            G_fatal_error(_("Directional degrees divided by 45 can not be > 8"));
        dir_format = DIR_DEG45;
    }
    else if (strcmp(opt.format->answer, "auto") == 0) {
        if (dir_max <= 8) {
            dir_format = DIR_DEG45;
            G_important_message(_("Input direction format assumed to be degrees CCW from East divided by 45"));
        }
        else if (dir_max <= 360) {
            dir_format = DIR_DEG;
            G_important_message(_("Input direction format assumed to be degrees CCW from East"));
        }
        else
            G_fatal_error(_("Unable to detect format of input direction map <%s>"),
                          dir_name);
    }
    if (dir_format == DIR_UNKNOWN)
        G_fatal_error(_("Invalid directions format '%s'"),
                      opt.format->answer);
    /* end of r.path */

    if (weight_name) {
        weight_fd = Rast_open_old(weight_name, "");
        weight_buf.type = Rast_get_map_type(weight_fd);
    }
    else {
        weight_fd = -1;
        weight_buf.type = CELL_TYPE;
    }

    acc_buf.type = weight_buf.type;
    acc_fd = Rast_open_new(acc_name, acc_buf.type);

    neg = flag.neg->answer;

    rows = Rast_window_rows();
    cols = Rast_window_cols();

    done = G_malloc(rows * sizeof(char *));
    dir_buf = G_malloc(rows * sizeof(CELL *));
    for (row = 0; row < rows; row++) {
        done[row] = G_calloc(cols, 1);
        dir_buf[row] = Rast_allocate_c_buf();
        Rast_get_c_row(dir_fd, dir_buf[row], row);
        if (dir_format == DIR_DEG45) {
            for (col = 0; col < cols; col++)
                dir_buf[row][col] *= 45;
        }
    }

    if (weight_fd >= 0) {
        weight_buf.map.v = (void **)G_malloc(rows * sizeof(void *));
        for (row = 0; row < rows; row++) {
            weight_buf.map.v[row] =
                (void *)Rast_allocate_buf(weight_buf.type);
            Rast_get_row(weight_fd, weight_buf.map.v[row], row,
                         weight_buf.type);
        }
    }
    else
        weight_buf.map.v = NULL;
    weight_buf.rows = rows;
    weight_buf.cols = cols;

    acc_buf.map.v = (void **)G_malloc(rows * sizeof(void *));
    for (row = 0; row < rows; row++)
        acc_buf.map.v[row] = (void *)Rast_allocate_buf(acc_buf.type);
    acc_buf.rows = rows;
    acc_buf.cols = cols;

    for (row = 0; row < rows; row++) {
        for (col = 0; col < cols; col++)
            accumulate(dir_buf, weight_buf, acc_buf, done, neg, row, col);
    }

    for (row = 0; row < rows; row++)
        Rast_put_row(acc_fd, acc_buf.map.v[row], acc_buf.type);

    G_free(done);
    for (row = 0; row < rows; row++) {
        G_free(dir_buf[row]);
        if (weight_fd >= 0)
            G_free(weight_buf.map.v[row]);
        G_free(acc_buf.map.v[row]);
    }
    G_free(dir_buf);
    if (weight_fd >= 0)
        G_free(weight_buf.map.v);
    G_free(acc_buf.map.v);

    Rast_close(dir_fd);
    if (weight_fd >= 0)
        Rast_close(weight_fd);
    Rast_close(acc_fd);

    Rast_put_cell_title(acc_name,
                        weight_name ? "Weighted flow accumulation" :
                        (neg ? "Flow accumulation with likely underestimates"
                         : "Flow accumulation"));
    Rast_short_history(acc_name, "raster", &hist);
    Rast_command_history(&hist);
    Rast_write_history(acc_name, &hist);

    exit(EXIT_SUCCESS);
}
