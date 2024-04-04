/****************************************************************************
 *
 * MODULE:       r.accumulate
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Calculates weighted flow accumulation, subwatersheds, stream
 *               networks, and longest flow paths using a flow direction map.
 *
 * COPYRIGHT:    (C) 2018, 2020 by Huidae Cho and the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define _MAIN_C_

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
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
        struct Option *weight;
        struct Option *input_accum;
        struct Option *input_subaccum;
        struct Option *accum;
        struct Option *subaccum;
        struct Option *accum_type;
        struct Option *subwshed;
        struct Option *stream;
        struct Option *thresh;
        struct Option *coords;
        struct Option *id;
        struct Option *outlet;
        struct Option *outlet_layer;
        struct Option *outlet_idcol;
        struct Option *idcol;
        struct Option *lfp;
    } opt;
    struct {
        struct Flag *neg_accum;
        struct Flag *zero_accum;
        struct Flag *accum_lfp;
        struct Flag *conf_stream;
        struct Flag *recur;
    } flag;
    char *desc;
    char *dir_name, *weight_name, *input_accum_name, *input_subaccum_name,
        *accum_name, *subaccum_name, *accum_type, *subwshed_name, *stream_name,
        *outlet_name, *lfp_name;
    int dir_fd;
    unsigned char dir_format;
    double thresh;
    struct Range dir_range;
    CELL dir_min, dir_max;
    char neg_accum, zero_accum, accum_lfp, conf_stream, recur;
    struct cell_map dir_buf;
    struct raster_map accum_buf;
    int nrows, ncols, row, col;
    struct Map_info Map;
    struct point_list outlet_pl;
    int *id;
    char *outlet_layer, *outlet_idcol, *idcol;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("accumulation"));
    G_add_keyword(_("watershed"));
    G_add_keyword(_("subwatershed"));
    G_add_keyword(_("stream network"));
    G_add_keyword(_("longest flow path"));
    module->description =
        _("Calculates weighted flow accumulation, subwatersheds, stream "
          "networks, and longest flow paths using a flow direction map.");

    opt.dir = G_define_standard_option(G_OPT_R_INPUT);
    opt.dir->key = "direction";
    opt.dir->description = _("Name of input direction map");

    opt.format = G_define_option();
    opt.format->type = TYPE_STRING;
    opt.format->key = "format";
    opt.format->label = _("Format of input direction map");
    opt.format->required = YES;
    opt.format->options = "auto,degree,45degree";
    opt.format->answer = "auto";
    G_asprintf(
        &desc, "auto;%s;degree;%s;45degree;%s",
        _("auto-detect direction format"), _("degrees CCW from East"),
        _("degrees CCW from East divided by 45 (e.g. r.watershed directions)"));
    opt.format->descriptions = desc;

    opt.weight = G_define_standard_option(G_OPT_R_INPUT);
    opt.weight->key = "weight";
    opt.weight->required = NO;
    opt.weight->description = _("Name of input flow weight map");

    opt.input_accum = G_define_standard_option(G_OPT_R_INPUT);
    opt.input_accum->key = "input_accumulation";
    opt.input_accum->required = NO;
    opt.input_accum->type = TYPE_STRING;
    opt.input_accum->description =
        _("Name of input weighted flow accumulation map");

    opt.input_subaccum = G_define_standard_option(G_OPT_R_INPUT);
    opt.input_subaccum->key = "input_subaccumulation";
    opt.input_subaccum->required = NO;
    opt.input_subaccum->type = TYPE_STRING;
    opt.input_subaccum->description =
        _("Name of input flow subaccumulation map");

    opt.accum = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.accum->key = "accumulation";
    opt.accum->required = NO;
    opt.accum->type = TYPE_STRING;
    opt.accum->description =
        _("Name for output weighted flow accumulation map");

    opt.subaccum = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.subaccum->key = "subaccumulation";
    opt.subaccum->required = NO;
    opt.subaccum->type = TYPE_STRING;
    opt.subaccum->description =
        _("Name for output weighted flow subaccumulation map");

    opt.accum_type = G_define_standard_option(G_OPT_R_TYPE);
    opt.accum_type->key = "accumulation_type";
    opt.accum_type->required = NO;
    opt.accum_type->description =
        _("Type of accumulation raster map to be created");

    opt.subwshed = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.subwshed->key = "subwatershed";
    opt.subwshed->required = NO;
    opt.subwshed->type = TYPE_STRING;
    opt.subwshed->description = _("Name for output subwatershed map");

    opt.stream = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.stream->key = "stream";
    opt.stream->required = NO;
    opt.stream->description = _("Name for output stream vector map");

    opt.thresh = G_define_option();
    opt.thresh->key = "threshold";
    opt.thresh->type = TYPE_DOUBLE;
    opt.thresh->label = _("Minimum flow accumulation for streams");

    opt.coords = G_define_standard_option(G_OPT_M_COORDS);
    opt.coords->multiple = YES;
    opt.coords->description =
        _("Coordinates of longest flow path outlet point");

    opt.id = G_define_option();
    opt.id->key = "id";
    opt.id->type = TYPE_INTEGER;
    opt.id->multiple = YES;
    opt.id->description = _("ID for longest flow path");

    opt.outlet = G_define_standard_option(G_OPT_V_INPUT);
    opt.outlet->key = "outlet";
    opt.outlet->required = NO;
    opt.outlet->label =
        _("Name of input outlet vector map for longest flow path");

    opt.outlet_layer = G_define_standard_option(G_OPT_V_FIELD);
    opt.outlet_layer->key = "outlet_layer";
    opt.outlet_layer->label = _("Layer number or name for outlet points");

    opt.outlet_idcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.outlet_idcol->key = "outlet_id_column";
    opt.outlet_idcol->description =
        _("Name of longest flow path ID column in outlet vector map");

    opt.idcol = G_define_standard_option(G_OPT_DB_COLUMN);
    opt.idcol->key = "id_column";
    opt.idcol->description = _("Name for output longest flow path ID column");

    opt.lfp = G_define_standard_option(G_OPT_V_OUTPUT);
    opt.lfp->key = "longest_flow_path";
    opt.lfp->required = NO;
    opt.lfp->description = _("Name for output longest flow path vector map");

    flag.neg_accum = G_define_flag();
    flag.neg_accum->key = 'n';
    flag.neg_accum->label =
        _("Use negative flow accumulation for likely underestimates");

    flag.zero_accum = G_define_flag();
    flag.zero_accum->key = '0';
    flag.zero_accum->label =
        _("Use 0s instead of nulls for no flow accumulation (faster)");

    flag.accum_lfp = G_define_flag();
    flag.accum_lfp->key = 'a';
    flag.accum_lfp->label = _("Calculate accumulated longest flow paths");

    flag.conf_stream = G_define_flag();
    flag.conf_stream->key = 'c';
    flag.conf_stream->label = _("Delineate streams across confluences");

    flag.recur = G_define_flag();
    flag.recur->key = 'r';
    flag.recur->label = _("Use recursive algorithms");

    /* weighting doesn't support negative accumulation because weights
     * themselves can be negative; the longest flow path requires positive
     * non-weighted accumulation */
    G_option_exclusive(opt.weight, opt.lfp, flag.neg_accum, NULL);
    /* straight input to output is not useful */
    G_option_exclusive(opt.input_accum, opt.accum, NULL);
    G_option_exclusive(opt.input_subaccum, opt.subaccum, NULL);
    /* currently, back-calculating accumulation from subaccumulation is not
     * supported; also, accumulated longest flow paths cannot be calculated
     * from subaccumulation */
    G_option_excludes(opt.input_subaccum, opt.accum, flag.accum_lfp, NULL);
    /* these three inputs are mutually exclusive because one is an output of
     * another */
    G_option_exclusive(opt.weight, opt.input_accum, opt.input_subaccum, NULL);
    /* one of these outputs is always required; otherwise, why run this module?
     */
    G_option_required(opt.accum, opt.subaccum, opt.subwshed, opt.stream,
                      opt.lfp, NULL);
    /* stream output and threshold always go together */
    G_option_collective(opt.stream, opt.thresh, NULL);
    /* calculating subaccumulatoin requires coordinates or outlets because
     * accumulation at those points need to be subtracted in the downstream
     * direction */
    G_option_requires(opt.subaccum, opt.coords, opt.outlet, NULL);
    /* delineating subwatersheds requires coordinates or outlets */
    G_option_requires(opt.subwshed, opt.coords, opt.outlet, NULL);
    /* longest flow path requires coordinates or outlets; otherwise, there is
     * no way to know where to start */
    G_option_requires(opt.lfp, opt.coords, opt.outlet, NULL);
    /* if given an output id column name, either an id value or outlet id column
     * is required to populate idcol */
    G_option_requires(opt.idcol, opt.id, opt.outlet_idcol, NULL);
    /* if given an id value, idcol and the same number of coordinates are
     * required */
    G_option_requires_all(opt.id, opt.idcol, opt.coords, NULL);
    /* if given an outlet id column, the outlets layer that contains this
     * column and an output id column are required to populate the id column
     * with outlet ids */
    G_option_requires_all(opt.outlet_idcol, opt.outlet, opt.idcol, NULL);
    /* negative (or positive) accumulation is needed only to calculate one of
     * these outputs */
    G_option_requires(flag.neg_accum, opt.accum, opt.subaccum, opt.stream,
                      opt.lfp, NULL);
    /* zero accumulation is needed only to calculate one of these outputs */
    G_option_requires(flag.zero_accum, opt.accum, opt.subaccum, opt.stream,
                      opt.lfp, NULL);
    /* negative accumulation cannot be done when either accumulation or
     * subaccumulation is given as input */
    G_option_excludes(flag.neg_accum, opt.input_accum, opt.input_subaccum,
                      NULL);
    /* zero accumulation cannot be done when either accumulation or
     * subaccumulation is given as input */
    G_option_excludes(flag.zero_accum, opt.input_accum, opt.input_subaccum,
                      NULL);
    /* accumulated lfp requires longest flow paths */
    G_option_requires(flag.accum_lfp, opt.lfp, NULL);
    /* recursive algorithm requires accumulation, subwatersheds, or longest flow
     * paths */
    G_option_requires(flag.recur, opt.accum, opt.subwshed, opt.lfp, NULL);
    /* confluence delineation requires output streams */
    G_option_requires(flag.conf_stream, opt.stream, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    dir_name = opt.dir->answer;
    weight_name = opt.weight->answer;
    input_accum_name = opt.input_accum->answer;
    input_subaccum_name = opt.input_subaccum->answer;
    accum_name = opt.accum->answer;
    subaccum_name = opt.subaccum->answer;
    accum_type = opt.accum_type->answer;
    subwshed_name = opt.subwshed->answer;
    stream_name = opt.stream->answer;
    outlet_name = opt.outlet->answer;
    lfp_name = opt.lfp->answer;

    outlet_layer = opt.outlet_layer->answer;
    outlet_idcol = opt.outlet_idcol->answer;
    idcol = opt.idcol->answer;

    if (opt.id->answers && outlet_name && !outlet_idcol)
        G_fatal_error(
            _("Option <%s> must be specified when <%s> and <%s> are present"),
            opt.outlet_idcol->key, opt.id->key, opt.outlet->key);

    if (outlet_idcol && opt.coords->answers && !opt.id->answers)
        G_fatal_error(
            _("Option <%s> must be specified when <%s> and <%s> are present"),
            opt.id->key, opt.outlet_idcol->key, opt.coords->key);

    dir_fd = Rast_open_old(dir_name, "");
    if (Rast_get_map_type(dir_fd) != CELL_TYPE)
        G_fatal_error(_("Invalid directions map <%s>"), dir_name);

    /* adapted from r.path */
    if (Rast_read_range(dir_name, "", &dir_range) < 0)
        G_fatal_error(_("Unable to read range file"));
    Rast_get_range_min_max(&dir_range, &dir_min, &dir_max);
    if (dir_max <= 0)
        G_fatal_error(_("Invalid direction map <%s>"), dir_name);

    dir_format = DIR_UNKNOWN;
    if (strcmp(opt.format->answer, "degree") == 0) {
        if (dir_max > 360)
            G_fatal_error(_("Directional degrees cannot be > 360"));
        dir_format = DIR_DEG;
    }
    else if (strcmp(opt.format->answer, "45degree") == 0) {
        if (dir_max > 8)
            G_fatal_error(_("Directional degrees divided by 45 cannot be > 8"));
        dir_format = DIR_DEG45;
    }
    else if (strcmp(opt.format->answer, "power2") == 0) {
        if (dir_max > 128)
            G_fatal_error(_("Powers of 2 cannot be > 128"));
        dir_format = DIR_POW2;
    }
    else if (strcmp(opt.format->answer, "auto") == 0) {
        if (dir_max <= 8) {
            dir_format = DIR_DEG45;
            G_important_message(_("Input direction format assumed to be "
                                  "degrees CCW from East divided by 45"));
        }
        else if (dir_max <= 128) {
            dir_format = DIR_POW2;
            G_important_message(_("Input direction format assumed to be "
                                  "powers of 2 CW from East"));
        }
        else if (dir_max <= 360) {
            dir_format = DIR_DEG;
            G_important_message(_(
                "Input direction format assumed to be degrees CCW from East"));
        }
        else
            G_fatal_error(
                _("Unable to detect format of input direction map <%s>"),
                dir_name);
    }
    if (dir_format == DIR_UNKNOWN)
        G_fatal_error(_("Invalid direction format '%s'"), opt.format->answer);
    /* end of r.path */

    /* read outlet coordinates and IDs */
    id = NULL;
    init_point_list(&outlet_pl);
    if (opt.coords->answers) {
        int i = 0;

        while (opt.coords->answers[i]) {
            add_point(&outlet_pl, atof(opt.coords->answers[i]),
                      atof(opt.coords->answers[i + 1]));
            i += 2;
        }
        if (opt.id->answers) {
            i = 0;
            while (opt.id->answers[i])
                i++;
            if (i < outlet_pl.n)
                G_fatal_error(_("Too few longest flow path IDs specified"));
            if (i > outlet_pl.n)
                G_fatal_error(_("Too many longest flow path IDs specified"));
            id = (int *)G_malloc(outlet_pl.n * sizeof(int));
            i = 0;
            while (opt.id->answers[i]) {
                id[i] = atoi(opt.id->answers[i]);
                i++;
            }
        }
    }

    /* read outlet points and IDs */
    if (outlet_name) {
        dbDriver *driver = NULL;
        struct field_info *Fi;
        struct line_pnts *Points;
        struct line_cats *Cats;
        int field;
        int nlines, line, n;

        if (Vect_open_old2(&Map, outlet_name, "", outlet_layer) < 0)
            G_fatal_error(_("Unable to open vector map <%s>"), outlet_name);

        field = Vect_get_field_number(&Map, outlet_layer);

        if (outlet_idcol) {
            Fi = Vect_get_field(&Map, field);
            driver = db_start_driver_open_database(
                Fi->driver, Vect_subst_var(Fi->database, &Map));
            if (db_column_Ctype(driver, Fi->table, outlet_idcol) !=
                DB_C_TYPE_INT)
                G_fatal_error(
                    _("Column <%s> in vector map <%s> must be of integer type"),
                    outlet_idcol, outlet_name);
        }

        Points = Vect_new_line_struct();
        Cats = Vect_new_cats_struct();

        nlines = Vect_get_num_lines(&Map);
        id = (int *)G_realloc(id, (outlet_pl.n + nlines) * sizeof(int));
        n = outlet_pl.n;

        for (line = 1; line <= nlines; line++) {
            int ltype, cat;

            ltype = Vect_read_line(&Map, Points, Cats, line);
            Vect_cat_get(Cats, field, &cat);

            if (ltype != GV_POINT || cat < 0)
                continue;

            add_point(&outlet_pl, Points->x[0], Points->y[0]);

            if (driver) {
                dbValue val;

                if (db_select_value(driver, Fi->table, Fi->key, cat,
                                    outlet_idcol, &val) < 0)
                    G_fatal_error(
                        _("Unable to read column <%s> in vector map <%s>"),
                        outlet_idcol, outlet_name);

                id[n++] = db_get_value_int(&val);
            }
            else
                id[n++] = cat;
        }

        if (driver)
            db_close_database_shutdown_driver(driver);

        Vect_close(&Map);

        if (n < outlet_pl.n)
            G_fatal_error(_("Too few longest flow path IDs specified"));
        if (n > outlet_pl.n)
            G_fatal_error(_("Too many longest flow path IDs specified"));
    }

    if (outlet_pl.n)
        G_message(
            n_("%d outlet specified", "%d outlets specified", outlet_pl.n),
            outlet_pl.n);

    thresh = opt.thresh->answer ? atof(opt.thresh->answer) : 0.0;
    neg_accum = flag.neg_accum->answer;
    zero_accum = flag.zero_accum->answer;
    accum_lfp = flag.accum_lfp->answer;
    conf_stream = flag.conf_stream->answer;
    recur = flag.recur->answer;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* read the direction map */
    dir_buf.nrows = nrows;
    dir_buf.ncols = ncols;
    dir_buf.c = (CELL **)G_malloc(nrows * sizeof(CELL *));
    G_message(_("Reading direction map..."));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 1);
        dir_buf.c[row] = Rast_allocate_c_buf();
        Rast_get_c_row(dir_fd, dir_buf.c[row], row);
        switch (dir_format) {
        case DIR_DEG:
            for (col = 0; col < ncols; col++) {
                CELL dir = abs(dir_buf.c[row][col] / 45.0);

                dir_buf.c[row][col] = dir >= NE && dir <= E ? dir : 0;
            }
            break;
        case DIR_DEG45:
            for (col = 0; col < ncols; col++) {
                CELL dir = abs(dir_buf.c[row][col]);

                dir_buf.c[row][col] = dir >= NE && dir <= E ? dir : 0;
            }
            break;
        default:
            for (col = 0; col < ncols; col++) {
                CELL dir = abs(8 - log2(dir_buf.c[row][col]));

                dir_buf.c[row][col] = dir >= NE && dir <= E ? dir : 0;
            }
        }
    }
    G_percent(1, 1, 1);
    Rast_close(dir_fd);

    /* prepare to create accumulation buffer only when needed */
    if (accum_name || subaccum_name || stream_name || lfp_name) {
        struct raster_map weight_buf;

        accum_buf.nrows = nrows;
        accum_buf.ncols = ncols;
        accum_buf.cells.v = (void **)G_malloc(nrows * sizeof(void *));

        /* optionally, read a weight map */
        weight_buf.cells.v = NULL;
        if (weight_name) {
            int weight_fd = Rast_open_old(weight_name, "");

            accum_buf.type = weight_buf.type = Rast_get_map_type(weight_fd);
            weight_buf.nrows = nrows;
            weight_buf.ncols = ncols;
            weight_buf.cells.v = (void **)G_malloc(nrows * sizeof(void *));
            G_message(_("Reading weight map..."));
            for (row = 0; row < nrows; row++) {
                G_percent(row, nrows, 1);
                weight_buf.cells.v[row] =
                    (void *)Rast_allocate_buf(weight_buf.type);
                Rast_get_row(weight_fd, weight_buf.cells.v[row], row,
                             weight_buf.type);
            }
            G_percent(1, 1, 1);
            Rast_close(weight_fd);
        }
        /* create non-weighted accumulation if input accumulation is not given
         */
        else if (!input_accum_name && !input_subaccum_name)
            accum_buf.type = CELL_TYPE;

        /* optionally, read an accumulation or subaccumulation map */
        if (input_accum_name || input_subaccum_name) {
            int accum_fd = Rast_open_old(
                input_accum_name ? input_accum_name : input_subaccum_name, "");

            accum_buf.type = Rast_get_map_type(accum_fd);
            G_message(input_accum_name ? _("Reading accumulation map...")
                                       : _("Reading subaccumulation map..."));
            for (row = 0; row < nrows; row++) {
                G_percent(row, nrows, 1);
                accum_buf.cells.v[row] =
                    (void *)Rast_allocate_buf(accum_buf.type);
                Rast_get_row(accum_fd, accum_buf.cells.v[row], row,
                             accum_buf.type);
            }
            G_percent(1, 1, 1);
            Rast_close(accum_fd);
        }
        /* accumulate flows if input accumulation is not given */
        else {
            char **done = (char **)G_malloc(nrows * sizeof(char *));

            /* only for output accumulation */
            if (strcmp(accum_type, "CELL") == 0) {
                if (accum_buf.type != CELL_TYPE)
                    G_warning(_("Accumulation type promoted to %s"),
                              accum_buf.type == FCELL_TYPE ? "FCELL" : "DCELL");
            }
            else if (strcmp(accum_type, "FCELL") == 0) {
                if (accum_buf.type != FCELL_TYPE) {
                    if (weight_buf.type == DCELL_TYPE)
                        G_warning(_("Accumulation type promoted to %s"),
                                  accum_buf.type == FCELL_TYPE ? "FCELL"
                                                               : "DCELL");
                    else
                        accum_buf.type = FCELL_TYPE;
                }
            }
            else if (accum_buf.type != DCELL_TYPE)
                accum_buf.type = DCELL_TYPE;

            G_message(_("Allocating buffers..."));
            for (row = 0; row < nrows; row++) {
                G_percent(row, nrows, 1);
                done[row] = (char *)G_calloc(ncols, 1);
                accum_buf.cells.v[row] =
                    (void *)Rast_allocate_buf(accum_buf.type);
            }
            G_percent(1, 1, 1);

            if (recur)
                accumulate_recursive(&dir_buf, &weight_buf, &accum_buf, done,
                                     neg_accum, zero_accum);
            else
                accumulate_iterative(&dir_buf, &weight_buf, &accum_buf, done,
                                     neg_accum, zero_accum);

            for (row = 0; row < nrows; row++)
                G_free(done[row]);
            G_free(done);
        }

        /* free buffer memory */
        if (weight_buf.cells.v) {
            for (row = 0; row < nrows; row++)
                G_free(weight_buf.cells.v[row]);
            G_free(weight_buf.cells.v);
        }

        /* write out buffer to the accumulation map if requested */
        if (accum_name) {
            int accum_fd = Rast_open_new(accum_name, accum_buf.type);
            struct History hist;

            G_message(_("Writing accumulation map..."));
            for (row = 0; row < nrows; row++) {
                G_percent(row, nrows, 1);
                Rast_put_row(accum_fd, accum_buf.cells.v[row], accum_buf.type);
            }
            G_percent(1, 1, 1);
            Rast_close(accum_fd);

            /* write history */
            Rast_put_cell_title(
                accum_name,
                weight_name
                    ? _("Weighted flow accumulation")
                    : (neg_accum
                           ? _("Flow accumulation with likely underestimates")
                           : _("Flow accumulation")));
            Rast_short_history(accum_name, "raster", &hist);
            Rast_command_history(&hist);
            Rast_write_history(accum_name, &hist);
        }
    }
    else
        accum_buf.cells.v = NULL;

    /* delineate stream networks */
    if (stream_name) {
        if (Vect_open_new(&Map, stream_name, 0) < 0)
            G_fatal_error(_("Unable to create vector map <%s>"), stream_name);
        Vect_set_map_name(&Map, _("Stream network"));
        Vect_hist_command(&Map);

        delineate_streams(&Map, &dir_buf, &accum_buf, thresh, conf_stream);

        if (!Vect_build(&Map))
            G_warning(_("Unable to build topology for vector map <%s>"),
                      stream_name);
        Vect_close(&Map);
    }

    /* calculate subaccumulation if needed; this process overwrite accum_buf to
     * save memory */
    if (subaccum_name || (lfp_name && !input_subaccum_name && !accum_lfp)) {
        subaccumulate(&Map, &dir_buf, &accum_buf, &outlet_pl);

        /* write out buffer to the subaccumulation map if requested */
        if (subaccum_name) {
            int subaccum_fd = Rast_open_new(subaccum_name, accum_buf.type);
            struct History hist;

            G_message(_("Writing subaccumulation map..."));
            for (row = 0; row < nrows; row++) {
                G_percent(row, nrows, 1);
                Rast_put_row(subaccum_fd, accum_buf.cells.v[row],
                             accum_buf.type);
            }
            G_percent(1, 1, 1);
            Rast_close(subaccum_fd);

            /* write history */
            Rast_put_cell_title(
                subaccum_name, weight_name
                                   ? _("Weighted flow subaccumulation")
                                   : (neg_accum ? _("Flow subaccumulation with "
                                                    "likely underestimates")
                                                : _("Flow subaccumulation")));
            Rast_short_history(subaccum_name, "raster", &hist);
            Rast_command_history(&hist);
            Rast_write_history(subaccum_name, &hist);
        }
    }

    /* calculate the longest flow path */
    if (lfp_name) {
        if (Vect_open_new(&Map, lfp_name, 0) < 0)
            G_fatal_error(_("Unable to create vector map <%s>"), lfp_name);
        Vect_set_map_name(&Map, _("Longest flow paths"));
        Vect_hist_command(&Map);

        if (recur)
            calculate_lfp_recursive(&Map, &dir_buf, &accum_buf, id, idcol,
                                    &outlet_pl);
        else
            calculate_lfp_iterative(&Map, &dir_buf, &accum_buf, id, idcol,
                                    &outlet_pl);

        if (!Vect_build(&Map))
            G_warning(_("Unable to build topology for vector map <%s>"),
                      lfp_name);
        Vect_close(&Map);
    }

    /* free buffer memory */
    if (accum_buf.cells.v) {
        for (row = 0; row < nrows; row++)
            G_free(accum_buf.cells.v[row]);
        G_free(accum_buf.cells.v);
    }

    /* delineate subwatersheds; this process overwrites dir_buf to save memory
     */
    if (subwshed_name) {
        char **done = (char **)G_malloc(nrows * sizeof(char *));
        int subwshed_fd;
        const char *mapset = G_mapset();
        struct Range range;
        CELL min, max;
        struct Colors colors;
        struct History hist;

        for (row = 0; row < nrows; row++)
            done[row] = (char *)G_calloc(ncols, 1);

        if (recur)
            delineate_subwatersheds_recursive(&dir_buf, done, id, &outlet_pl);
        else
            delineate_subwatersheds_iterative(&dir_buf, done, id, &outlet_pl);

        for (row = 0; row < nrows; row++)
            G_free(done[row]);
        G_free(done);

        subwshed_fd = Rast_open_c_new(subwshed_name);
        G_message(_("Writing subwatershed map..."));
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 1);
            Rast_put_c_row(subwshed_fd, dir_buf.c[row]);
        }
        G_percent(1, 1, 1);
        Rast_close(subwshed_fd);

        /* assign random colors */
        Rast_read_range(subwshed_name, mapset, &range);
        Rast_get_range_min_max(&range, &min, &max);
        Rast_make_random_colors(&colors, min, max);
        Rast_write_colors(subwshed_name, mapset, &colors);

        /* write history */
        Rast_put_cell_title(subwshed_name, _("Subwatersheds"));
        Rast_short_history(subwshed_name, "raster", &hist);
        Rast_command_history(&hist);
        Rast_write_history(subwshed_name, &hist);
    }

    /* free buffer memory */
    for (row = 0; row < nrows; row++)
        G_free(dir_buf.c[row]);
    G_free(dir_buf.c);

    exit(EXIT_SUCCESS);
}
