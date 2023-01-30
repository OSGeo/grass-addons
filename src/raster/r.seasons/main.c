/****************************************************************************
 *
 * MODULE:       r.seasons
 * AUTHOR(S):    Markus Metz
 * PURPOSE:      season extraction from a time series
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

struct input {
    const char *name;
    int fd;
    DCELL *buf;
};

struct output {
    const char *name;
    int fd;
    DCELL *buf;
};

static int (*cmp_dbl)(double a, double b);

static int cmp_dbl_lo(double a, double b)
{
    if (a > b)
        return -1;

    return (a < b);
}

static int cmp_dbl_hi(double a, double b)
{
    if (a < b)
        return -1;

    return (a > b);
}

static int get_season(double *val, char *isnull, double *ts, int i0, int n,
                      double threshold, double minlen, double maxgap,
                      int *start1, int *start2, int *end1, int *end2)
{
    int i, startin, startout, endout;
    double blenin, blenout;

    if (i0 >= n)
        return 0;

    /* get first in-season block of at least minlen */
    blenin = blenout = 0;
    *start1 = *end1 = i0;
    *start2 = *end2 = i0;
    for (i = i0; i < n; i++) {
        if (isnull[i] == 0 && cmp_dbl(val[i], threshold) >= 0) {
            if (blenin == 0) {
                *start1 = i;
            }
            *end1 = i;
            if (i < n - 1)
                blenin = (ts[i] + ts[i + 1]) / 2.0;
            else
                blenin = ts[i] + (ts[i] - ts[i - 1]) / 2.0;

            if (*start1 > 0)
                blenin -= (ts[*start1 - 1] + ts[*start1]) / 2.0;
            else
                blenin -= ts[*start1] - (ts[*start1 + 1] - ts[*start1]) / 2.0;
        }
        else {
            if (blenin >= minlen)
                break;
            else
                blenin = 0;
        }
    }
    if (blenin < minlen)
        return 0;

    /* go back from start1, find start2 */
    blenout = 0;
    *start2 = *start1;
    endout = *start1 - 1;
    for (i = *start1 - 1; i >= i0; i--) {
        if (isnull[i] == 0 && cmp_dbl(val[i], threshold) >= 0) {
            blenout = 0;
            *start2 = i;
        }
        else {
            if (blenout == 0)
                endout = i;

            if (endout < n - 1)
                blenout = (ts[endout] + ts[endout + 1]) / 2.0;
            else
                blenout = ts[endout] + (ts[endout] - ts[endout - 1]) / 2.0;

            if (i > 0)
                blenout -= (ts[i - 1] + ts[i]) / 2.0;
            else
                blenout -= ts[i] - (ts[i + 1] - ts[i]) / 2.0;

            if (blenout >= maxgap)
                break;
        }
    }

    /* go forward from end1, find end2 */
    /* shift end1 if there is another in-season block of at least minlen */
    blenin = blenout = 0;
    *end2 = *end1;
    startout = *end1;
    startin = *end1;
    for (i = *end1 + 1; i < n; i++) {
        if (isnull[i] == 0 && cmp_dbl(val[i], threshold) >= 0) {
            blenout = 0;
            if (blenin == 0)
                startin = i;
            *end2 = i;

            if (i < n - 1)
                blenin = (ts[i] + ts[i + 1]) / 2.0;
            else
                blenin = ts[i] + (ts[i] - ts[i - 1]) / 2.0;

            if (startin > 0)
                blenin -= (ts[startin - 1] + ts[startin]) / 2.0;
            else
                blenin -= ts[startin] - (ts[startin + 1] - ts[startin]) / 2.0;

            if (blenin >= minlen)
                *end1 = i;
        }
        else {
            blenin = 0;
            if (blenout == 0)
                startout = i;

            if (i < n - 1)
                blenout = (ts[i] + ts[i + 1]) / 2.0;
            else
                blenout = ts[i] + (ts[i] - ts[i - 1]) / 2.0;

            if (startout > 0)
                blenout -= (ts[startout - 1] + ts[startout]) / 2.0;
            else
                blenout -=
                    ts[startout] - (ts[startout + 1] - ts[startout]) / 2.0;

            if (blenout >= maxgap)
                break;
        }
    }

    return 1;
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *input, *file, *prefix, *ts, /* time steps*/
            *ns,                                   /* number of seasons */
            *nsout, /* output map for number of seasons */
            *maxl1, /* output map with maximum season length (core season) */
            *maxl2, /* output map with maximum season length (full season) */
            *tval,  /* constant threshold to start/stop a season */
            *tmap,  /* map with threshold values to start/stop a season */
            *min,   /* minimum length in time to recognize a season */
            *max;   /* maximum gap length within one season */
    } parm;
    struct {
        struct Flag *lo, *lazy;
    } flag;
    int i;
    int num_inputs;
    struct input *inputs = NULL;
    struct input tin;
    int num_outputs;
    struct output *outputs = NULL;
    int nsout_fd;
    CELL *nsoutbuf;
    int maxl1_fd, maxl2_fd;
    DCELL *maxl1_buf, *maxl2_buf, maxl1, maxl2, l;
    char *prefix;
    struct History history;
    DCELL *values = NULL;
    int nrows, ncols;
    int row, col;
    double minlen, maxgap;
    int ns, nsmax, nfound;
    double threshold;
    double *ts;
    char *isnull;
    int n_nulls;
    int start1, start2, end1, end2;
    int i0;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    G_add_keyword(_("filtering"));
    module->description = _("Extracts seasons from a time series.");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);
    parm.input->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description =
        _("Input file with raster map names, one per line");
    parm.file->required = NO;

    parm.prefix = G_define_option();
    parm.prefix->key = "prefix";
    parm.prefix->type = TYPE_STRING;
    parm.prefix->required = NO;
    parm.prefix->label = _("Prefix for output maps");
    parm.prefix->description =
        _("The prefix will be prepended to input map names");

    parm.ts = G_define_option();
    parm.ts->key = "time_steps";
    parm.ts->type = TYPE_DOUBLE;
    parm.ts->multiple = YES;
    parm.ts->description = _("Time steps of the input maps");

    parm.ns = G_define_option();
    parm.ns->key = "n";
    parm.ns->type = TYPE_INTEGER;
    parm.ns->required = YES;
    parm.ns->description = _("Number of seasons to detect");

    parm.nsout = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.nsout->key = "nout";
    parm.nsout->required = NO;
    parm.nsout->description =
        _("Name of output map with detected number of seasons");

    parm.maxl1 = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.maxl1->key = "max_length_core";
    parm.maxl1->required = NO;
    parm.maxl1->description =
        _("Name of output map with maximum core season length");

    parm.maxl2 = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.maxl2->key = "max_length_full";
    parm.maxl2->required = NO;
    parm.maxl2->description =
        _("Name of output map with maximum full season length");

    parm.tval = G_define_option();
    parm.tval->key = "threshold_value";
    parm.tval->type = TYPE_DOUBLE;
    parm.tval->required = NO;
    parm.tval->description = _("Constant threshold to start/stop a season");

    parm.tmap = G_define_standard_option(G_OPT_R_INPUT);
    parm.tmap->key = "threshold_map";
    parm.tmap->required = NO;
    parm.tmap->description = _("Constant threshold to start/stop a season");

    parm.min = G_define_option();
    parm.min->key = "min_length";
    parm.min->type = TYPE_DOUBLE;
    parm.min->required = YES;
    parm.min->label = _("Minimum season length");
    parm.min->description = _("A season must be at least min long, otherwise "
                              "the data are considered as noise");

    parm.max = G_define_option();
    parm.max->key = "max_gap";
    parm.max->type = TYPE_DOUBLE;
    parm.max->required = NO;
    parm.max->label = _("Maximum gap length (default: min_length)");
    parm.max->description = _("A gap must not be longer than max, otherwise "
                              "the season is terminated");

    flag.lo = G_define_flag();
    flag.lo->key = 'l';
    flag.lo->description = _("Stop a season when a value is above threshold "
                             "(default: below threshold)");

    flag.lazy = G_define_flag();
    flag.lazy->key = 'z';
    flag.lazy->description = _("Don't keep files open");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (parm.input->answer && parm.file->answer)
        G_fatal_error(_("input= and file= are mutually exclusive"));

    if (!parm.input->answer && !parm.file->answer)
        G_fatal_error(_("Please specify input= or file="));

    if (!parm.prefix->answer && !parm.nsout->answer && !parm.maxl1->answer &&
        !parm.maxl2->answer)
        G_fatal_error(_("No output requested"));

    ns = atoi(parm.ns->answer);
    if (ns < 1)
        G_fatal_error(_("Number of seasons must be positive integer"));

    minlen = atof(parm.min->answer);
    if (minlen <= 0)
        G_fatal_error(_("Minimum season length must be positive"));

    maxgap = minlen;
    if (parm.max->answer) {
        maxgap = atof(parm.max->answer);
        if (maxgap <= 0)
            G_fatal_error(_("Maximum gap length must be positive"));
    }

    if (parm.tmap->answer) {
        tin.name = G_store(parm.tmap->answer);
        tin.fd = Rast_open_old(tin.name, "");
        tin.buf = Rast_allocate_d_buf();
    }
    else {
        if (!parm.tval->answer)
            G_fatal_error(_("No threshold, please provide either <%s> or <%s>"),
                          parm.tval->key, parm.tmap->key);

        threshold = atof(parm.tval->answer);
        tin.name = NULL;
        tin.fd = -1;
        tin.buf = NULL;
    }

    if (flag.lo->answer)
        cmp_dbl = cmp_dbl_lo;
    else
        cmp_dbl = cmp_dbl_hi;

    /* process the input maps from the file */
    if (parm.file->answer) {
        FILE *in;
        int max_inputs;

        in = fopen(parm.file->answer, "r");
        if (!in)
            G_fatal_error(_("Unable to open input file <%s>"),
                          parm.file->answer);

        num_inputs = 0;
        max_inputs = 0;

        for (;;) {
            char buf[GNAME_MAX];
            char *name;
            struct input *p;

            if (!G_getl2(buf, sizeof(buf), in))
                break;

            name = G_chop(buf);

            /* Ignore empty lines */
            if (!*name)
                continue;

            if (num_inputs >= max_inputs) {
                max_inputs += 100;
                inputs = G_realloc(inputs, max_inputs * sizeof(struct input));
            }
            p = &inputs[num_inputs++];

            p->name = G_store(name);
            G_verbose_message(_("Reading raster map <%s>..."), p->name);
            p->buf = Rast_allocate_d_buf();
            p->fd = Rast_open_old(p->name, "");
            if (flag.lazy->answer)
                Rast_close(p->fd);
        }

        if (num_inputs < 1)
            G_fatal_error(_("No raster map name found in input file"));

        fclose(in);
    }
    else {
        for (i = 0; parm.input->answers[i]; i++)
            ;
        num_inputs = i;

        if (num_inputs < 1)
            G_fatal_error(_("Raster map not found"));

        inputs = G_malloc(num_inputs * sizeof(struct input));

        for (i = 0; i < num_inputs; i++) {
            struct input *p = &inputs[i];

            p->name = parm.input->answers[i];
            G_verbose_message(_("Reading raster map <%s>..."), p->name);
            p->buf = Rast_allocate_d_buf();
            p->fd = Rast_open_old(p->name, "");
            if (flag.lazy->answer)
                Rast_close(p->fd);
        }
    }
    if (num_inputs < 3)
        G_fatal_error(_("At least 3 input maps are required"));

    ts = G_malloc(num_inputs * sizeof(double));

    if (parm.ts->answer) {
        for (i = 0; parm.ts->answers[i]; i++)
            ;
        if (i != num_inputs)
            G_fatal_error(
                _("Number of time steps does not match number of input maps"));
        for (i = 0; parm.ts->answers[i]; i++) {
            ts[i] = atof(parm.ts->answers[i]);
            if (i > 0 && ts[i - 1] >= ts[i])
                G_fatal_error(_("Time steps must increase"));
        }
    }
    else {
        for (i = 0; i < num_inputs; i++) {
            ts[i] = i;
        }
    }

    /* open output maps */
    num_outputs = 0;
    prefix = parm.prefix->answer;
    if (prefix) {
        num_outputs = ns * 4;

        outputs = G_calloc(num_outputs, sizeof(struct output));

        for (i = 0; i < ns; i++) {
            struct output *out;
            char output_name[GNAME_MAX];

            out = &outputs[i * 4];
            sprintf(output_name, "%s%d_%s", prefix, i + 1, "start1");
            out->name = G_store(output_name);
            out->buf = Rast_allocate_d_buf();
            out->fd = Rast_open_new(out->name, DCELL_TYPE);

            out = &outputs[i * 4 + 1];
            sprintf(output_name, "%s%d_%s", prefix, i + 1, "start2");
            out->name = G_store(output_name);
            out->buf = Rast_allocate_d_buf();
            out->fd = Rast_open_new(out->name, DCELL_TYPE);

            out = &outputs[i * 4 + 2];
            sprintf(output_name, "%s%d_%s", prefix, i + 1, "end1");
            out->name = G_store(output_name);
            out->buf = Rast_allocate_d_buf();
            out->fd = Rast_open_new(out->name, DCELL_TYPE);

            out = &outputs[i * 4 + 3];
            sprintf(output_name, "%s%d_%s", prefix, i + 1, "end2");
            out->name = G_store(output_name);
            out->buf = Rast_allocate_d_buf();
            out->fd = Rast_open_new(out->name, DCELL_TYPE);
        }
    }

    /* number of seasons */
    nsout_fd = -1;
    nsoutbuf = NULL;
    if (parm.nsout->answer) {
        nsout_fd = Rast_open_new(parm.nsout->answer, CELL_TYPE);
        nsoutbuf = Rast_allocate_c_buf();
    }
    /* maximum core season length */
    maxl1_fd = -1;
    maxl1_buf = NULL;
    if (parm.maxl1->answer) {
        maxl1_fd = Rast_open_new(parm.maxl1->answer, DCELL_TYPE);
        maxl1_buf = Rast_allocate_d_buf();
    }
    /* maximum full season length */
    maxl2_fd = -1;
    maxl2_buf = NULL;
    if (parm.maxl2->answer) {
        maxl2_fd = Rast_open_new(parm.maxl2->answer, DCELL_TYPE);
        maxl2_buf = Rast_allocate_d_buf();
    }

    /* initialise variables */
    values = G_malloc(num_inputs * sizeof(DCELL));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    isnull = G_malloc(num_inputs * sizeof(char));

    /* process the data */
    G_message(_("Detecting seasons for %d input maps..."), num_inputs);

    nsmax = 0;
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 4);

        if (flag.lazy->answer) {
            /* Open the files only on run time */
            for (i = 0; i < num_inputs; i++) {
                inputs[i].fd = Rast_open_old(inputs[i].name, "");
                Rast_get_d_row(inputs[i].fd, inputs[i].buf, row);
                Rast_close(inputs[i].fd);
            }
        }
        else {
            for (i = 0; i < num_inputs; i++)
                Rast_get_d_row(inputs[i].fd, inputs[i].buf, row);
        }

        if (tin.buf)
            Rast_get_d_row(tin.fd, tin.buf, row);

        for (col = 0; col < ncols; col++) {

            if (tin.buf)
                threshold = tin.buf[col];

            n_nulls = 0;
            for (i = 0; i < num_inputs; i++) {
                DCELL v = inputs[i].buf[col];

                isnull[i] = 0;
                if (Rast_is_d_null_value(&v)) {
                    isnull[i] = 1;
                    n_nulls++;
                }
                values[i] = v;
            }

            nfound = 0;
            i0 = 0;
            maxl1 = maxl2 = 0;
            while (get_season(values, isnull, ts, i0, num_inputs, threshold,
                              minlen, maxgap, &start1, &start2, &end1, &end2)) {

                i0 = end2 + 1;

                if (prefix && nfound < ns) {
                    i = nfound * 4;
                    outputs[i].buf[col] = ts[start1];
                    outputs[i + 1].buf[col] = ts[start2];
                    outputs[i + 2].buf[col] = ts[end1];
                    outputs[i + 3].buf[col] = ts[end2];
                }
                nfound++;

                if (maxl1_buf) {
                    if (end1 < num_inputs - 1)
                        l = (ts[end1] + ts[end1 + 1]) / 2.0;
                    else
                        l = ts[end1] + (ts[end1] - ts[end1 - 1]) / 2.0;

                    if (start1 > 0)
                        l -= (ts[start1 - 1] + ts[start1]) / 2.0;
                    else
                        l -= ts[start1] - (ts[start1 + 1] - ts[start1]) / 2.0;
                    if (maxl1 < l)
                        maxl1 = l;
                }
                if (maxl2_buf) {
                    if (end2 < num_inputs - 1)
                        l = (ts[end2] + ts[end2 + 1]) / 2.0;
                    else
                        l = ts[end2] + (ts[end2] - ts[end2 - 1]) / 2.0;

                    if (start2 > 0)
                        l -= (ts[start2 - 1] + ts[start2]) / 2.0;
                    else
                        l -= ts[start2] - (ts[start2 + 1] - ts[start2]) / 2.0;
                    if (maxl2 < l)
                        maxl2 = l;
                }
            }
            if (nsmax < nfound)
                nsmax = nfound;

            if (prefix) {
                for (i = nfound * 4; i < num_outputs; i++) {
                    Rast_set_d_null_value(&outputs[i].buf[col], 1);
                }
            }

            if (nsoutbuf) {
                if (n_nulls == num_inputs)
                    Rast_set_c_null_value(&nsoutbuf[col], 1);
                else
                    nsoutbuf[col] = nfound;
            }
            if (maxl1_buf) {
                if (n_nulls == num_inputs || maxl1 == 0)
                    Rast_set_d_null_value(&maxl1_buf[col], 1);
                else
                    maxl1_buf[col] = maxl1;
            }
            if (maxl2_buf) {
                if (n_nulls == num_inputs || maxl2 == 0)
                    Rast_set_d_null_value(&maxl2_buf[col], 1);
                else
                    maxl2_buf[col] = maxl2;
            }
        }

        if (prefix) {
            for (i = 0; i < num_outputs; i++) {
                Rast_put_d_row(outputs[i].fd, outputs[i].buf);
            }
        }
        if (nsoutbuf)
            Rast_put_c_row(nsout_fd, nsoutbuf);
        if (maxl1_buf)
            Rast_put_d_row(maxl1_fd, maxl1_buf);
        if (maxl2_buf)
            Rast_put_d_row(maxl2_fd, maxl2_buf);
    }

    G_percent(row, nrows, 2);

    G_message(_("A maximum of %d seasons have been detected."), nsmax);
    if (nsmax > ns)
        G_important_message(
            _("The number of output seasons (%d) is smaller than the maximum "
              "number of detected seasons (%d)."),
            ns, nsmax);

    if (!flag.lazy->answer) {
        /* close input maps */
        for (i = 0; i < num_inputs; i++)
            Rast_close(inputs[i].fd);
    }
    if (tin.fd >= 0)
        Rast_close(tin.fd);

    /* close output maps */
    for (i = 0; i < num_outputs; i++) {
        struct output *out = &outputs[i];

        Rast_close(out->fd);

        Rast_short_history(out->name, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(out->name, &history);
    }
    if (nsout_fd >= 0) {
        Rast_close(nsout_fd);

        Rast_short_history(parm.nsout->answer, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(parm.nsout->answer, &history);
    }
    if (maxl1_fd >= 0) {
        Rast_close(maxl1_fd);

        Rast_short_history(parm.maxl1->answer, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(parm.maxl1->answer, &history);
    }
    if (maxl2_fd >= 0) {
        Rast_close(maxl2_fd);

        Rast_short_history(parm.maxl2->answer, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(parm.maxl2->answer, &history);
    }

    exit(EXIT_SUCCESS);
}
