/****************************************************************************
 *
 * MODULE:       r.quantile.ref
 * AUTHOR(S):    Markus Metz
 * PURPOSE:      Get quantile of the input value from reference maps
 * COPYRIGHT:    (C) 2015 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

struct input {
    const char *name, *mapset;
    int fd;
    DCELL *buf;
};

struct output {
    const char *name;
    int fd;
    FCELL *buf;
};

static int cmp_dcell(const void *a, const void *b)
{
    DCELL da = *(DCELL *)a;
    DCELL db = *(DCELL *)b;

    return (da < db ? -1 : (da > db));
}

/* return the smallest array index where values[idx] <= v
 * return -1 if v < values[0]
 * return n if v > values[n - 1] */
static int bsearch_refidx(DCELL v, DCELL *values, int n)
{
    int mid, lo, hi;

    /* tests */
    if (n < 1)
        return -1;

    lo = 0;
    hi = n - 1;

    if (values[lo] < v && v < values[hi]) {
        /* bsearch */
        mid = lo;
        while (lo < hi) {
            mid = (lo + hi) / 2;

            if (values[mid] < v) {
                lo = mid + 1;
            }
            else {
                hi = mid;
            }
        }

        if (values[mid] > v) {
            mid--;
        }

        return mid;
    }

    if (values[0] > v)
        return -1;

    if (values[0] == v)
        return 0;

    if (values[n - 1] == v)
        return n - 1;

    if (values[n - 1] < v)
        return n;

    return 0;
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *input, *ref, *file, *output, *range;
    } parm;
    struct {
        struct Flag *lazy;
    } flag;
    int i, n, idx;
    int num_inputs;
    struct input vinput, *refs;
    struct output out;
    struct History history;
    struct Colors colors;
    DCELL *values;
    int dcellsize;
    int nrows, ncols;
    int row, col;
    DCELL lo, hi;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("aggregation"));
    G_add_keyword(_("series"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("quantile"));
    module->description =
        _("Determines quantile for input value from reference "
          "raster map layers.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.ref = G_define_standard_option(G_OPT_R_INPUTS);
    parm.ref->key = "reference";
    parm.ref->description = _("List ofreference raster maps");
    parm.ref->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description =
        _("Input file with one reference raster map name per line");
    parm.file->required = NO;

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.range = G_define_option();
    parm.range->key = "range";
    parm.range->type = TYPE_DOUBLE;
    parm.range->key_desc = "lo,hi";
    parm.range->description = _("Ignore values outside this range");

    flag.lazy = G_define_flag();
    flag.lazy->key = 'z';
    flag.lazy->description = _("Do not keep files open");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    lo = -1.0 / 0.0;
    hi = 1.0 / 0.0;
    if (parm.range->answer) {
        lo = atof(parm.range->answers[0]);
        hi = atof(parm.range->answers[1]);
    }

    /* open input map */
    vinput.name = parm.input->answer;
    vinput.mapset = G_find_raster2(vinput.name, "");
    if (!vinput.mapset)
        G_fatal_error(_("Raster map <%s> not found"), vinput.name);
    vinput.fd = Rast_open_old(vinput.name, vinput.mapset);
    vinput.buf = Rast_allocate_d_buf();

    /* process the reference maps */
    if (parm.file->answer) {
        FILE *in;
        int max_inputs;

        if (strcmp(parm.file->answer, "-") == 0)
            in = stdin;
        else {
            in = fopen(parm.file->answer, "r");
            if (!in)
                G_fatal_error(_("Unable to open input file <%s>"),
                              parm.file->answer);
        }

        num_inputs = 0;
        max_inputs = 0;
        refs = NULL;

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
                refs = G_realloc(refs, max_inputs * sizeof(struct input));
            }
            p = &refs[num_inputs++];

            p->name = G_store(name);
            p->mapset = G_find_raster2(p->name, "");
            p->buf = Rast_allocate_d_buf();
            if (!flag.lazy->answer)
                p->fd = Rast_open_old(p->name, p->mapset);
        }

        fclose(in);

        if (num_inputs < 2)
            G_fatal_error(_("At least two reference raster maps are required"));
    }
    else {
        for (i = 0; parm.ref->answers[i]; i++)
            ;
        num_inputs = i;

        if (num_inputs < 2)
            G_fatal_error(_("At least two reference raster maps are required"));

        refs = G_malloc(num_inputs * sizeof(struct input));

        /* open reference maps */
        for (i = 0; i < num_inputs; i++) {
            struct input *p = &refs[i];

            p->name = parm.ref->answers[i];
            p->mapset = G_find_raster2(p->name, "");
            if (!p->mapset)
                G_fatal_error(_("Raster map <%s> not found"), p->name);
            if (!flag.lazy->answer)
                p->fd = Rast_open_old(p->name, p->mapset);
            p->buf = Rast_allocate_d_buf();
        }
    }

    dcellsize = sizeof(DCELL);

    /* open output */
    out.name = parm.output->answer;
    out.buf = Rast_allocate_f_buf();
    out.fd = Rast_open_new(out.name, FCELL_TYPE);
    if (out.fd < 0)
        G_fatal_error(_("Unable to create raster map <%s>"), out.name);

    /* initialise variables */
    values = G_malloc(num_inputs * sizeof(DCELL));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* process the data */
    G_verbose_message(_("Percent complete..."));

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        if (flag.lazy->answer) {
            /* Open the raster maps only one at a time */
            for (i = 0; i < num_inputs; i++) {
                refs[i].fd = Rast_open_old(refs[i].name, refs[i].mapset);
                Rast_get_d_row(refs[i].fd, refs[i].buf, row);
            }
        }
        else {
            for (i = 0; i < num_inputs; i++)
                Rast_get_d_row(refs[i].fd, refs[i].buf, row);
        }

        Rast_get_d_row(vinput.fd, vinput.buf, row);

        for (col = 0; col < ncols; col++) {
            DCELL v;
            int null = 0;

            n = 0;
            for (i = 0; i < num_inputs; i++) {
                v = refs[i].buf[col];

                if (Rast_is_d_null_value(&v))
                    null = 1;
                else if (parm.range->answer && (v < lo || v > hi)) {
                    null = 1;
                }
                else
                    values[n++] = v;
            }

            v = vinput.buf[col];

            if (Rast_is_d_null_value(&v) || null)
                Rast_set_f_null_value(&out.buf[col], 1);
            else if (n == 0)
                Rast_set_f_null_value(&out.buf[col], 1);
            else if (n == 1) {
                out.buf[col] = 0.5;
                if (v < values[0])
                    out.buf[col] = -1;
                else if (v > values[n - 1])
                    out.buf[col] = 2;
            }
            else { /* n > 1 */
                qsort(values, n, dcellsize, cmp_dcell);

                if (v < values[0])
                    out.buf[col] = -1;
                else if (v > values[n - 1])
                    out.buf[col] = 2;
                else {
                    idx = bsearch_refidx(v, values, n);

                    if (v == values[idx]) {
                        int idx1 = idx;

                        while (idx1 < n - 1 && values[idx1 + 1] == v) {
                            idx1++;
                        }

                        out.buf[col] = ((FCELL)(idx + idx1)) / (2 * (n - 1));
                    }
                    else { /* values[idx] < v < values[idx + 1] */
                        double w = v - values[idx];
                        double wtot = values[idx + 1] - values[idx];

                        out.buf[col] = (idx + w / wtot) / (n - 1);
                    }
                }
            }
        }

        Rast_put_f_row(out.fd, out.buf);
    }

    G_percent(row, nrows, 2);

    /* close maps */
    Rast_close(vinput.fd);
    for (i = 0; i < num_inputs; i++)
        Rast_close(refs[i].fd);

    Rast_close(out.fd);

    Rast_short_history(out.name, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out.name, &history);

    Rast_init_colors(&colors);
    lo = -1;
    hi = 0;
    Rast_add_d_color_rule(&lo, 255, 0, 0, &hi, 255, 0, 0, &colors);
    lo = 0;
    hi = 0.3;
    Rast_add_d_color_rule(&lo, 255, 0, 0, &hi, 220, 220, 0, &colors);
    lo = 0.3;
    hi = 0.5;
    Rast_add_d_color_rule(&lo, 220, 220, 0, &hi, 180, 180, 180, &colors);
    lo = 0.5;
    hi = 0.7;
    Rast_add_d_color_rule(&lo, 180, 180, 180, &hi, 0, 220, 220, &colors);
    lo = 0.7;
    hi = 1;
    Rast_add_d_color_rule(&lo, 0, 220, 220, &hi, 0, 0, 255, &colors);
    lo = 1;
    hi = 2;
    Rast_add_d_color_rule(&lo, 0, 0, 255, &hi, 0, 0, 255, &colors);
    Rast_write_colors(out.name, G_mapset(), &colors);

    exit(EXIT_SUCCESS);
}
