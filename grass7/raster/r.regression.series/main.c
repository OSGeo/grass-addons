
/****************************************************************************
 *
 * MODULE:       r.series
 * 
 * AUTHOR(S):    Markus Metz
 *               based on r.series by
 *               Glynn Clements <glynn gclements.plus.com> (original contributor)
 *               Hamish Bowman <hamish_b yahoo.com>, Jachym Cepicky <jachym les-ejk.cz>,
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

#define REGRESSION_SLOPE		0
#define REGRESSION_OFFSET		1
#define REGRESSION_COEFF_DET		2
#define REGRESSION_COEFF_DET_ADJ	3
#define REGRESSION_F_VALUE		4
#define REGRESSION_T_VALUE		5

static void reg(DCELL *result, DCELL (*values)[2], int n, int which)
{
    DCELL sumX, sumY, sumsqX, sumsqY, sumXY;
    DCELL meanX, meanY;
    DCELL A, B, R, F, T;
    int count;
    int i;

    sumX = sumY = sumsqX = sumsqY = sumXY = 0.0;
    meanX = meanY = 0.0;
    count = 0;

    for (i = 0; i < n; i++) {
	if (Rast_is_d_null_value(&values[i][0]) ||
	    Rast_is_d_null_value(&values[i][1]))
	    continue;

	sumX += values[i][0];
	sumY += values[i][1];
	sumsqX += values[i][0] * values[i][0];
	sumsqY += values[i][1] * values[i][1];
	sumXY += values[i][0] * values[i][1];
	count++;
    }

    if (count < 2) {
	Rast_set_d_null_value(result, 1);
	return;
    }

    B = (sumXY - sumX * sumY / count) / (sumsqX - sumX * sumX / count);
    R = (sumXY - sumX * sumY / count) /
	sqrt((sumsqX - sumX * sumX / count) * (sumsqY - sumY * sumY / count));

    meanX = sumX / count;

    meanY = sumY / count;

    switch (which) {
    case REGRESSION_SLOPE:
	*result = B;
	break;
    case REGRESSION_OFFSET:
	A = meanY - B * meanX;
	*result = A;
	break;
    case REGRESSION_COEFF_DET:
	*result = R;
	break;
    case REGRESSION_COEFF_DET_ADJ:
	*result = 1 - (1 - R) * ((count - 1) / (count - 2 - 1));
	break;
    case REGRESSION_F_VALUE:
	F = R * R / (1 - R * R / count - 2);
	*result = F;
	break;
    case REGRESSION_T_VALUE:
	T = sqrt(R) * sqrt((count - 2) / (1 - R));
	*result = T;
	break;
    default:
	Rast_set_d_null_value(result, 1);
	break;
    }

    /* Check for NaN */
    if (*result != *result)
	Rast_set_d_null_value(result, 1);
}

void reg_m(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_SLOPE);
}

void reg_c(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_OFFSET);
}

void reg_r2(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_COEFF_DET);
}

void reg_r2_adj(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_COEFF_DET);
}

void reg_f(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_F_VALUE);
}

void reg_t(DCELL * result, DCELL (*values)[2], int n)
{
    reg(result, values, n, REGRESSION_T_VALUE);
}

typedef void stat_func(DCELL *, DCELL (*)[2], int);

struct menu
{
    stat_func *method;		/* routine to compute new value */
    char *name;			/* method name */
    char *text;			/* menu display - full description */
} menu[] = {
    {reg_m,      "slope",       "linear regression slope"},
    {reg_c,      "offset",      "linear regression offset"},
    {reg_r2,     "detcoeff",    "linear regression coefficient of determination"},
    {reg_r2_adj, "adjdetcoeff", "adjusted coefficient of determination"},
    {reg_f,      "f",           "F statistic"},
    {reg_t,      "t",           "T statistic"},
    {NULL,         NULL,          NULL}
};

struct input
{
    const char *name;
    int fd;
    DCELL *buf;
};

struct output
{
    const char *name;
    int fd;
    DCELL *buf;
    stat_func *method_fn;
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
    struct
    {
	struct Option *xinput, *yinput, *output, *method;
    } parm;
    struct
    {
	struct Flag *nulls;
    } flag;
    int i;
    int num_inputs;
    struct input *xinputs, *yinputs;
    int num_outputs;
    struct output *outputs;
    struct History history;
    DCELL (*values)[2], (*values_tmp)[2];
    int nrows, ncols;
    int row, col;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
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
	G_fatal_error(_("Regression parameters can not be calculated for less than 3 maps per series"));

    if (num_inputs < 7)
	G_warning(_("Regression parameters are dubious for less than 7 maps per series"));

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
	G_fatal_error(_("output= and method= must have the same number of values"));

    outputs = G_calloc(num_outputs, sizeof(struct output));

    for (i = 0; i < num_outputs; i++) {
	struct output *out = &outputs[i];
	const char *output_name = parm.output->answers[i];
	const char *method_name = parm.method->answers[i];
	int method = find_method(method_name);

	out->name = output_name;
	out->method_fn = menu[method].method;
	out->buf = Rast_allocate_d_buf();
	out->fd = Rast_open_new(output_name, DCELL_TYPE);
    }

    /* initialise variables */
    values = (DCELL(*)[2]) G_malloc(num_inputs * 2 * sizeof(DCELL));
    values_tmp = (DCELL(*)[2]) G_malloc(num_inputs * 2 * sizeof(DCELL));

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

	    for (i = 0; i < num_inputs; i++) {
		DCELL x = xinputs[i].buf[col];
		DCELL y = yinputs[i].buf[col];

		if (Rast_is_d_null_value(&x) || Rast_is_d_null_value(&y))
		    null = 1;

		values[i][0] = x;
		values[i][1] = y;
	    }

	    for (i = 0; i < num_outputs; i++) {
		struct output *out = &outputs[i];

		if (null && flag.nulls->answer)
		    Rast_set_d_null_value(&out->buf[col], 1);
		else {
		    memcpy(values_tmp, values, num_inputs * 2 * sizeof(DCELL));
		    (*out->method_fn)(&out->buf[col], values_tmp, num_inputs);
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
