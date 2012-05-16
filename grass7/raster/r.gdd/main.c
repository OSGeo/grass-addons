
/****************************************************************************
 *
 * MODULE:       r.series
 * AUTHOR(S):    Glynn Clements <glynn gclements.plus.com> (original contributor)
 *               Hamish Bowman <hamish_b yahoo.com>, Jachym Cepicky <jachym les-ejk.cz>,
 *               Martin Wegmann <wegmann biozentrum.uni-wuerzburg.de>
 * PURPOSE:      
 * COPYRIGHT:    (C) 2002-2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <limits.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/stats.h>

struct menu
{
    stat_func *method;		/* routine to compute new value */
    stat_func_w *method_w;	/* routine to compute new value (weighted) */
    int is_int;			/* result is an integer */
    char *name;			/* method name */
    char *text;			/* menu display - full description */
} menu[] = {
    {c_ave,    w_ave,    0, "average",    "average value"},
    {c_count,  NULL,     1, "count",      "count of non-NULL cells"},
    {c_median, w_median, 0, "median",     "median value"},
    {c_mode,   w_mode,   0, "mode",       "most frequently occuring value"},
    {c_min,    NULL,     0, "minimum",    "lowest value"},
    {c_minx,   NULL,     1, "min_raster", "raster with lowest value"},
    {c_max,    NULL,     0, "maximum",    "highest value"},
    {c_maxx,   NULL,     1, "max_raster", "raster with highest value"},
    {c_stddev, w_stddev, 0, "stddev",     "standard deviation"},
    {c_range,  NULL,     0, "range",      "range of values"},
    {c_sum,    w_sum,    0, "sum",        "sum of values"},
    {c_var,    w_var,    0, "variance",   "statistical variance"},
    {c_divr,   NULL,     1, "diversity",  "number of different values"},
    {c_reg_m,  NULL,     0, "slope",      "linear regression slope"},
    {c_reg_c,  NULL,     0, "offset",     "linear regression offset"},
    {c_reg_r2, NULL,     0, "detcoeff",   "linear regression coefficient of determination"},
    {c_quart1, w_quart1, 0, "quart1",     "first quartile"},
    {c_quart3, w_quart3, 0, "quart3",     "third quartile"},
    {c_perc90, w_perc90, 0, "perc90",     "ninetieth percentile"},
    {c_quant,  w_quant,  0, "quantile",   "arbitrary quantile"},
    {c_skew,   w_skew,   0, "skewness",   "skewness"},
    {c_kurt,   w_kurt,   0, "kurtosis",   "kurtosis"},
    {NULL,     NULL,     0, NULL,         NULL}
};

static double f_box(double x)
{
    return (x > 1) ? 0
	: 1;
}

static double f_bartlett(double x)
{
    return (x > 1) ? 0
	: 1 - x;
}

static double f_hermite(double x)
{
    return (x > 1) ? 0
	: (2 * x - 3) * x * x + 1;
}

static double f_gauss(double x)
{
    return exp(-2 * x * x) * sqrt(2 / M_PI);
}

static double f_normal(double x)
{
    return f_gauss(x / 2) / 2;
}

static double f_sinc(double x)
{
    return (x == 0) ? 1 : sin(M_PI * x) / (M_PI * x);
}

static double lanczos(double x, int a)
{
    return (x > a) ? 0
	: f_sinc(x) * f_sinc(x / a);
}

static double f_lanczos1(double x)
{
    return lanczos(x, 1);
}

static double f_lanczos2(double x)
{
    return lanczos(x, 2);
}

static double f_lanczos3(double x)
{
    return lanczos(x, 3);
}

static double f_hann(double x)
{
    return cos(M_PI * x) / 2 + 0.5;
}

static double f_hamming(double x)
{
    return 0.46 * cos(M_PI * x) + 0.54;
}


static double f_blackman(double x)
{
    return cos(M_PI * x) / 2 + 0.08 * cos(2 * M_PI * x) + 0.42;
}

struct window_type {
    const char *name;
    double (*func)(double);
    int radius;
} w_menu[] = {
    {"box",       f_box,       1},
    {"bartlett",  f_bartlett,  1},
    {"gauss",     f_gauss,     4},
    {"normal",    f_normal,    8},
    {"hermite",   f_hermite,   1},
    {"sinc",      f_sinc,      0},
    {"lanczos1",  f_lanczos1,  1},
    {"lanczos2",  f_lanczos2,  2},
    {"lanczos3",  f_lanczos3,  3},
    {"hann",      f_hann,      0},
    {"hamming",   f_hamming,   0},
    {"blackman",  f_blackman,  0},
    {NULL},
};

static char *build_window_list(void)
{
    char *buf = G_malloc(1024);
    char *p = buf;
    int i;

    for (i = 0; w_menu[i].name; i++) {
	const char *q;

	if (i)
	    *p++ = ',';
	for (q = w_menu[i].name; *q; p++, q++)
	    *p = *q;
    }
    *p = '\0';

    return buf;
}

static int find_window(const char *name)
{
    int i;

    for (i = 0; w_menu[i].name; i++)
	if (strcmp(w_menu[i].name, name) == 0)
	    return i;

    G_fatal_error(_("Unknown window <%s>"), name);

    return -1;
}

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
    stat_func_w *method_fn_w;
    double quantile;
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
	struct Option *input, *file, *output, *method, *quantile, *range, *weight;
    } parm;
    struct
    {
	struct Flag *nulls, *lazy, *outlier;
    } flag;
    int i;
    int num_inputs;
    struct input *inputs = NULL;
    int num_outputs;
    struct output *outputs = NULL;
    struct History history;
    DCELL *values = NULL, *values_tmp = NULL;
    DCELL (*values_w)[2], (*values_tmp_w)[2];	/* list of neighborhood values and weights */
    double *weights;
    int nrows, ncols;
    int row, col;
    double lo, hi;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    module->description =
	_("Makes each output cell value a "
	  "function of the values assigned to the corresponding cells "
	  "in the input raster map layers.");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);
    parm.input->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description = _("Input file with raster map names, one per line");
    parm.file->required = NO;

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->multiple = YES;

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = YES;
    parm.method->options = build_method_list();
    parm.method->description = _("Aggregate operation");
    parm.method->multiple = YES;

    parm.weight = G_define_option();
    parm.weight->key = "window";
    parm.weight->type = TYPE_STRING;
    parm.weight->required = NO;
    parm.weight->multiple = NO;
    parm.weight->description = _("weighing window");
    parm.weight->options = build_window_list();

    parm.quantile = G_define_option();
    parm.quantile->key = "quantile";
    parm.quantile->type = TYPE_DOUBLE;
    parm.quantile->required = NO;
    parm.quantile->description = _("Quantile to calculate for method=quantile");
    parm.quantile->options = "0.0-1.0";
    parm.quantile->multiple = YES;

    parm.range = G_define_option();
    parm.range->key = "range";
    parm.range->type = TYPE_DOUBLE;
    parm.range->key_desc = "lo,hi";
    parm.range->description = _("Ignore values outside this range");

    flag.nulls = G_define_flag();
    flag.nulls->key = 'n';
    flag.nulls->description = _("Propagate NULLs");

    flag.lazy = G_define_flag();
    flag.lazy->key = 'z';
    flag.lazy->description = _("Don't keep files open");

    flag.outlier = G_define_flag();
    flag.outlier->key = 'o';
    flag.outlier->description = _("Remove outliers");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    if (parm.range->answer) {
	lo = atof(parm.range->answers[0]);
	hi = atof(parm.range->answers[1]);
    }

    if (parm.input->answer && parm.file->answer)
        G_fatal_error(_("input= and file= are mutually exclusive"));
 
    if (!parm.input->answer && !parm.file->answer)
        G_fatal_error(_("Please specify input= or file="));


    /* process the input maps from the file */
    if (parm.file->answer) {
	FILE *in;
	int max_inputs;
    
	in = fopen(parm.file->answer, "r");
	if (!in)
	    G_fatal_error(_("Unable to open input file <%s>"), parm.file->answer);
    
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
	    if (!flag.lazy->answer)
		p->fd = Rast_open_old(p->name, "");
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
	    if (!flag.lazy->answer)
		p->fd = Rast_open_old(p->name, "");
    	}
    }

    /* set the weights */
    if (parm.weight->answer) {
	int method = find_window(parm.weight->answer);
	double (*func)(double) = w_menu[method].func;
	double radius = (num_inputs - 1) / 2.0;
	
	values_w = (DCELL(*)[2]) G_malloc(num_inputs * 2 * sizeof(DCELL));
	values_tmp_w = (DCELL(*)[2]) G_malloc(num_inputs * 2 * sizeof(DCELL));
	weights = (DCELL *) G_malloc(num_inputs * sizeof(DCELL));

	for (i = 0; i < num_inputs; i++) {
	    double x = fabs((i - radius) / radius);

	    if (w_menu[method].radius > 1)
		x *= w_menu[method].radius;
	    weights[i] = (*func)(x);
	}
    }
    else {
	values_w = NULL;
	values_tmp_w = NULL;
	weights = NULL;
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
	if (weights) {
	    if (menu[method].method_w) {
		out->method_fn = NULL;
		out->method_fn_w = menu[method].method_w;
	    }
	    else {
		G_warning(_("Method %s not compatible with weighing window, using unweighed version instead"),
		          method_name);
		
		out->method_fn = menu[method].method;
		out->method_fn_w = NULL;
	    }
	}
	else {
	    out->method_fn = menu[method].method;
	    out->method_fn_w = NULL;
	}
	out->quantile = (parm.quantile->answer && parm.quantile->answers[i])
	    ? atof(parm.quantile->answers[i])
	    : 0;
	out->buf = Rast_allocate_d_buf();
	out->fd = Rast_open_new(output_name,
				menu[method].is_int ? CELL_TYPE : DCELL_TYPE);
    }

    /* initialise variables */
    values = G_malloc(num_inputs * sizeof(DCELL));
    values_tmp = G_malloc(num_inputs * sizeof(DCELL));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* process the data */
    G_verbose_message(_("Percent complete..."));

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

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

	for (col = 0; col < ncols; col++) {
	    int null = 0, non_null = 0;

	    for (i = 0; i < num_inputs; i++) {
		DCELL v = inputs[i].buf[col];

		if (Rast_is_d_null_value(&v))
		    null = 1;
		else if (parm.range->answer && (v < lo || v > hi)) {
		    Rast_set_d_null_value(&v, 1);
		    null = 1;
		}
		else
		    non_null++;

		if (weights) {
		    values_w[i][0] = v;
		    values_w[i][1] = weights[i];
		}
		values[i] = v;
	    }

	    if (flag.outlier->answer && non_null > 5) {
		/* remove outlier */
		/* lower bound = 1st_Quartile - 1.5 * (3rd_Quartile - 1st_Quartile) */
		double quart1, quart3, lower_bound;

		memcpy(values_tmp, values, num_inputs * sizeof(DCELL));
		c_quart1(&quart1, values_tmp, num_inputs, NULL);
		memcpy(values_tmp, values, num_inputs * sizeof(DCELL));
		c_quart3(&quart3, values_tmp, num_inputs, NULL);

		if (quart1 < quart3)
		    lower_bound = quart1 - 0.5 * (quart3 - quart1);
		else
		    lower_bound = -1e100;

		for (i = 0; i < num_inputs; i++) {
		    DCELL v = values[i];

		    if (v <= lower_bound) {
			Rast_set_d_null_value(&v, 1);
			null = 1;
			/* non_null--; */
			values[i] = v;
			if (weights)
			    values_w[i][0] = v;
		    }
		}
	    }

	    for (i = 0; i < num_outputs; i++) {
		struct output *out = &outputs[i];

		if (non_null < 2 || (null && flag.nulls->answer))
		    Rast_set_d_null_value(&out->buf[col], 1);
		else {
		    if (out->method_fn_w) {
			memcpy(values_tmp_w, values_w, num_inputs * 2 * sizeof(DCELL));
			(*out->method_fn_w)(&out->buf[col], values_tmp_w, num_inputs, &out->quantile);
		    }
		    else {
			memcpy(values_tmp, values, num_inputs * sizeof(DCELL));
			(*out->method_fn)(&out->buf[col], values_tmp, num_inputs, &out->quantile);
		    }
		}
	    }
	}

	for (i = 0; i < num_outputs; i++)
	    Rast_put_d_row(outputs[i].fd, outputs[i].buf);
    }

    G_percent(row, nrows, 2);

    /* close output maps */
    for (i = 0; i < num_outputs; i++) {
	struct output *out = &outputs[i];

	Rast_close(out->fd);

	Rast_short_history(out->name, "raster", &history);
	Rast_command_history(&history);
	Rast_write_history(out->name, &history);
    }

    /* Close input maps */
    if (!flag.lazy->answer) {
    	for (i = 0; i < num_inputs; i++)
	    Rast_close(inputs[i].fd);
    }

    exit(EXIT_SUCCESS);
}
