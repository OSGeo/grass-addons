/****************************************************************************
 *
 * MODULE:       r.series
 *
 * AUTHOR(S):    Markus Metz
 *               based on r.series by
 *               Glynn Clements <glynn gclements.plus.com> (original
 *               contributor)
 *               Hamish Bowman <hamish_b yahoo.com>,
 *               Jachym Cepicky <jachym les-ejk.cz>,
 *               Martin Wegmann <wegmann biozentrum.uni-wuerzburg.de>
 *
 * PURPOSE:      regression between two time series
 *
 * COPYRIGHT:    (C) 2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

/* TODO: use more stable two pass algorithm */

#define SLOPE       0
#define OFFSET      1
#define CORCOEFF    2
#define RSQUARE     3
#define RSQUARE_ADJ 4
#define F_VALUE     5
#define T_VALUE     6

struct reg_stats {
    DCELL sumX, sumY, sumsqX, sumsqY, sumXY;
    DCELL meanX, meanY;
    DCELL A, B, R, R2;
    int count;
};

static void reg(DCELL *result, struct reg_stats rs, int which)
{
    switch (which) {
    case SLOPE:
        *result = rs.B;
        break;
    case OFFSET:
        *result = rs.meanY - rs.B * rs.meanX;
        break;
    case CORCOEFF:
        *result = rs.R;
        break;
    case RSQUARE:
        *result = rs.R2;
        break;
    case RSQUARE_ADJ:
        *result = 1 - (1 - rs.R2) * ((rs.count - 1) / (rs.count - 2));
        break;
    case F_VALUE:
        /* *result = rs.R2 / ((1 - rs.R2) / (rs.count - 2)); */
        *result = rs.R2 * (rs.count - 2) / (1 - rs.R2);
        break;
    case T_VALUE:
        *result = fabs(rs.R) * sqrt((rs.count - 2) / (1 - rs.R2));
        break;
    default:
        Rast_set_d_null_value(result, 1);
        break;
    }

    /* Check for NaN */
    if (*result != *result)
        Rast_set_d_null_value(result, 1);
}

struct menu {
    int method; /* routine to compute new value */
    char *name; /* method name */
    char *text; /* menu display - full description */
} menu[] = {{SLOPE, "slope", "Linear regression slope"},
            {OFFSET, "offset", "Linear regression offset"},
            {CORCOEFF, "corcoef", "Correlation coefficient R"},
            {RSQUARE, "rsq", "R squared (coefficient of determination)"},
            {RSQUARE_ADJ, "adjrsq", "Adjusted R squared"},
            {F_VALUE, "f", "F statistic"},
            {T_VALUE, "t", "T statistic"},
            {-1, NULL, NULL}};

struct input {
    const char *name;
    int fd;
    DCELL *buf;
};

struct output {
    const char *name;
    int fd;
    DCELL *buf;
    int method;
};

static char *build_method_list(void)
{
    char *buf = G_malloc(1024);
    char *p = buf;
    int i;

    for (i = 0; menu[i].name; i++) {
        char *q;

        if (i)
            *p++ = ',';
        for (q = menu[i].name; *q; p++, q++)
            *p = *q;
    }
    *p = '\0';

    return buf;
}

static int find_method(const char *method_name)
{
    int i;

    for (i = 0; menu[i].name; i++)
        if (strcmp(menu[i].name, method_name) == 0)
            return i;

    G_fatal_error(_("Unknown method <%s>"), method_name);

    return -1;
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *xinput, *yinput, *output, *method;
    } parm;
    struct {
        struct Flag *nulls;
    } flag;
    int i;
    int num_inputs;
    struct input *xinputs, *yinputs;
    int num_outputs;
    struct output *outputs;
    struct reg_stats rs;
    struct History history;
    int nrows, ncols;
    int row, col;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("series"));
    G_add_keyword(_("regression"));
    module->description =
        _("Makes each output cell value a "
          "function of the values assigned to the corresponding cells "
          "in the input raster map layers.");

    parm.xinput = G_define_standard_option(G_OPT_R_INPUTS);
    parm.xinput->key = "xseries";

    parm.yinput = G_define_standard_option(G_OPT_R_INPUTS);
    parm.yinput->key = "yseries";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->multiple = YES;

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    parm.method->options = build_method_list();
    parm.method->description = _("Regression parameters");
    parm.method->multiple = YES;

    flag.nulls = G_define_flag();
    flag.nulls->key = 'n';
    flag.nulls->description = _("Propagate NULLs");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* process the input maps */
    for (i = 0; parm.xinput->answers[i]; i++)
        ;
    num_inputs = i;

    for (i = 0; parm.yinput->answers[i]; i++)
        ;
    if (num_inputs != i)
        G_fatal_error(_("The number of '%s' and '%s' maps must be identical"),
                      parm.xinput->key, parm.yinput->key);

    if (num_inputs < 3)
        G_fatal_error(_("Regression parameters can not be calculated for less "
                        "than 3 maps per series"));

    if (num_inputs < 7)
        G_warning(_("Regression parameters are dubious for less than 7 maps "
                    "per series"));

    xinputs = G_malloc(num_inputs * sizeof(struct input));
    yinputs = G_malloc(num_inputs * sizeof(struct input));

    for (i = 0; i < num_inputs; i++) {
        struct input *px = &xinputs[i];
        struct input *py = &yinputs[i];

        px->name = parm.xinput->answers[i];
        G_message(_("Reading raster map <%s>..."), px->name);
        px->fd = Rast_open_old(px->name, "");
        px->buf = Rast_allocate_d_buf();

        py->name = parm.yinput->answers[i];
        G_message(_("Reading raster map <%s>..."), py->name);
        py->fd = Rast_open_old(py->name, "");
        py->buf = Rast_allocate_d_buf();
    }

    /* process the output maps */
    for (i = 0; parm.output->answers[i]; i++)
        ;
    num_outputs = i;

    for (i = 0; parm.method->answers[i]; i++)
        ;
    if (num_outputs != i)
        G_fatal_error(
            _("output= and method= must have the same number of values"));

    outputs = G_calloc(num_outputs, sizeof(struct output));

    for (i = 0; i < num_outputs; i++) {
        struct output *out = &outputs[i];
        const char *output_name = parm.output->answers[i];
        const char *method_name = parm.method->answers[i];
        int method = find_method(method_name);

        out->name = output_name;
        out->method = menu[method].method;
        out->buf = Rast_allocate_d_buf();
        out->fd = Rast_open_new(output_name, DCELL_TYPE);
    }

    /* initialise variables */

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* process the data */
    G_verbose_message(_("Percent complete..."));

    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        for (i = 0; i < num_inputs; i++) {
            Rast_get_d_row(xinputs[i].fd, xinputs[i].buf, row);
            Rast_get_d_row(yinputs[i].fd, yinputs[i].buf, row);
        }

        for (col = 0; col < ncols; col++) {
            int null = 0;

            rs.sumX = rs.sumY = rs.sumsqX = rs.sumsqY = rs.sumXY = 0.0;
            rs.meanX = rs.meanY = 0.0;
            rs.count = 0;

            for (i = 0; i < num_inputs; i++) {
                DCELL x = xinputs[i].buf[col];
                DCELL y = yinputs[i].buf[col];

                if (Rast_is_d_null_value(&x) || Rast_is_d_null_value(&y))
                    null = 1;
                else {
                    rs.sumX += x;
                    rs.sumY += y;
                    rs.sumsqX += x * x;
                    rs.sumsqY += y * y;
                    rs.sumXY += x * y;
                    rs.count++;
                }
            }
            if (rs.count > 1) {
                DCELL tmp1 = rs.count * rs.sumXY - rs.sumX * rs.sumY;
                DCELL tmp2 = rs.count * rs.sumsqX - rs.sumX * rs.sumX;

                /* slope */
                rs.B = tmp1 / tmp2;
                /* correlation coefficient */
                rs.R = tmp1 / sqrt((tmp2) *
                                   (rs.count * rs.sumsqY - rs.sumY * rs.sumY));
                /* coefficient of determination aka R squared */
                rs.R2 = rs.R * rs.R;

                rs.meanX = rs.sumX / rs.count;

                rs.meanY = rs.sumY / rs.count;
            }
            else {
                rs.R = rs.R2 = rs.B = 0;
            }

            for (i = 0; i < num_outputs; i++) {
                struct output *out = &outputs[i];

                if (rs.count < 2 || (null && flag.nulls->answer))
                    Rast_set_d_null_value(&out->buf[col], 1);
                else {
                    reg(&out->buf[col], rs, out->method);
                }
            }
        }

        for (i = 0; i < num_outputs; i++)
            Rast_put_d_row(outputs[i].fd, outputs[i].buf);
    }

    G_percent(row, nrows, 2);

    /* close maps */
    for (i = 0; i < num_outputs; i++) {
        struct output *out = &outputs[i];

        Rast_close(out->fd);

        Rast_short_history(out->name, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(out->name, &history);
    }

    for (i = 0; i < num_inputs; i++) {
        Rast_close(xinputs[i].fd);
        Rast_close(yinputs[i].fd);
    }

    exit(EXIT_SUCCESS);
}
