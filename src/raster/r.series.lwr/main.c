/****************************************************************************
 *
 * MODULE:       r.series.lwr
 * AUTHOR(S):    Markus Metz
 *               based on r.hants
 * PURPOSE:      time series correction
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
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
#include <float.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/gmath.h>

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

static double uniform(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;

    if (dist < 1)
        return 1;

    return 0;
}

static double triangular(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;

    if (dist == 0)
        return 1;

    if (dist >= 1)
        return 0;

    return (1.0 - dist);
}

static double epanechnikov(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;

    if (dist == 0)
        return 1;

    if (dist >= 1)
        return 0;

    return (1.0 - dist * dist);
}

static double quartic(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;
    double tmp;

    if (dist == 0)
        return 1;

    if (dist >= 1)
        return 0;

    tmp = 1.0 - dist * dist;

    return (tmp * tmp);
}

static double tricube(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;
    double tmp;

    if (dist == 0)
        return 1;

    if (dist >= 1)
        return 0;

    tmp = 1.0 - dist * dist * dist;

    return (tmp * tmp * tmp);
}

static double cosine(double ref, double x, double max)
{
    double dist = fabs(x - ref) / max;

    if (dist == 0)
        return 1;

    if (dist >= 1)
        return 0;

    return (cos(M_PI_2 * dist));
}

static int solvemat(double **m, double a[], double B[], int n)
{
    int i, j, i2, j2, imark;
    double factor, temp, *tempp;
    double pivot; /* ACTUAL VALUE OF THE LARGEST PIVOT CANDIDATE */

    for (i = 0; i < n; i++) {
        j = i;

        /* find row with largest magnitude value for pivot value */

        pivot = m[i][j];
        imark = i;
        for (i2 = i + 1; i2 < n; i2++) {
            temp = fabs(m[i2][j]);
            if (temp > fabs(pivot)) {
                pivot = m[i2][j];
                imark = i2;
            }
        }

        /* if the pivot is very small then the points are nearly co-linear */
        /* co-linear points result in an undefined matrix, and nearly */
        /* co-linear points results in a solution with rounding error */

        if (fabs(pivot) < GRASS_EPSILON) {
            G_debug(4, "Matrix is unsolvable");
            return 0;
        }

        /* if row with highest pivot is not the current row, switch them */

        if (imark != i) {
            /*
            for (j2 = 0; j2 < n; j2++) {
                temp = m[imark][j2];
                m[imark][j2] = m[i][j2];
                m[i][j2] = temp;
            }
            */

            tempp = m[imark];
            m[imark] = m[i];
            m[i] = tempp;

            temp = a[imark];
            a[imark] = a[i];
            a[i] = temp;
        }

        /* compute zeros above and below the pivot, and compute
           values for the rest of the row as well */

        for (i2 = 0; i2 < n; i2++) {
            if (i2 != i) {
                factor = m[i2][j] / pivot;
                for (j2 = j; j2 < n; j2++)
                    m[i2][j2] -= factor * m[i][j2];
                a[i2] -= factor * a[i];
            }
        }
    }

    /* SINCE ALL OTHER VALUES IN THE MATRIX ARE ZERO NOW, CALCULATE THE
       COEFFICIENTS BY DIVIDING THE COLUMN VECTORS BY THE DIAGONAL VALUES. */

    for (i = 0; i < n; i++) {
        B[i] = a[i] / m[i][i];
    }

    return 1;
}

static double term(int term, double x)
{
    switch (term) {
    case 0:
        return 1.0;
    case 1:
        return x;
    case 2:
        return x * x;
    case 3:
        return x * x * x;
    }

    return 0.0;
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *input, *file, *suffix, *order, /* polynomial order */
            *weight,                                  /* weighing function */
            *fet,                                     /* fit error tolerance */
            *ts,                                      /* time steps */
            *maxgap,                                  /* maximum gap size */
            *dod,   /* degree of over-determination */
            *range, /* range of valid values */
            *delta; /* threshold for high amplitudes */
    } parm;
    struct {
        struct Flag *lo, *hi, *lazy, *int_only;
    } flag;
    int i, j, k, n;
    int num_inputs, in_lo, in_hi;
    struct input *inputs = NULL;
    int num_outputs;
    struct output *outputs = NULL;
    char *suffix;
    struct History history;
    struct Colors colors;
    DCELL *values = NULL, *values2 = NULL;
    int nrows, ncols;
    int row, col;
    int order;
    double fet, maxerrlo, maxerrhi, lo, hi;
    DCELL *resultn;
    int msize;
    double **m, **m2, *a, *a2, *B;
    double *ts, maxgap, thisgap, prev_ts, next_ts, weight;
    double (*weight_func)(double, double, double);
    int dod;
    int *isnull, n_nulls;
    int min_points, n_points;
    int first, last, interp_only;
    int this_margin;
    double max_ts, tsdiff1, tsdiff2;
    double delta;
    int rejlo, rejhi;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    G_add_keyword(_("filtering"));
    module->description = _("Approximates a time series and creates "
                            "approximated, gap-filled output.");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);
    parm.input->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description =
        _("Input file with raster map names, one per line");
    parm.file->required = NO;

    parm.suffix = G_define_option();
    parm.suffix->key = "suffix";
    parm.suffix->type = TYPE_STRING;
    parm.suffix->required = NO;
    parm.suffix->answer = "_lwr";
    parm.suffix->label = _("Suffix for output maps");
    parm.suffix->description =
        _("The suffix will be appended to input map names");

    parm.order = G_define_option();
    parm.order->key = "order";
    parm.order->type = TYPE_INTEGER;
    parm.order->required = NO;
    parm.order->options = "0,1,2,3";
    parm.order->answer = "1";
    parm.order->label = _("order number");
    parm.order->description =
        _("Order of the polynomial fitting function, 0 means weighted average");

    parm.weight = G_define_option();
    parm.weight->key = "weight";
    parm.weight->type = TYPE_STRING;
    parm.weight->required = NO;
    parm.weight->options =
        "uniform,triangular,epanechnikov,quartic,tricube,cosine";
    parm.weight->answer = "tricube";
    parm.weight->description = _("Weighing kernel function");

    parm.fet = G_define_option();
    parm.fet->key = "fet";
    parm.fet->type = TYPE_DOUBLE;
    parm.fet->required = NO;
    parm.fet->multiple = NO;
    parm.fet->description = _("Fit error tolerance");

    parm.dod = G_define_option();
    parm.dod->key = "dod";
    parm.dod->type = TYPE_INTEGER;
    parm.dod->required = NO;
    parm.dod->answer = "0";
    parm.dod->description = _("Degree of over-determination");

    parm.range = G_define_option();
    parm.range->key = "range";
    parm.range->type = TYPE_DOUBLE;
    parm.range->key_desc = "lo,hi";
    parm.range->description = _("Ignore values outside this range");

    parm.ts = G_define_option();
    parm.ts->key = "time_steps";
    parm.ts->type = TYPE_DOUBLE;
    parm.ts->multiple = YES;
    parm.ts->description = _("Time steps of the input maps");

    parm.maxgap = G_define_option();
    parm.maxgap->key = "maxgap";
    parm.maxgap->type = TYPE_DOUBLE;
    parm.maxgap->description = _("Maximum gap size to be interpolated");

    parm.delta = G_define_option();
    parm.delta->key = "delta";
    parm.delta->type = TYPE_DOUBLE;
    parm.delta->answer = "0";
    parm.delta->label = _("Threshold for high amplitudes");
    parm.delta->description = _("Delta should be between 0 and 1");

    flag.lo = G_define_flag();
    flag.lo->key = 'l';
    flag.lo->description = _("Reject low outliers");

    flag.hi = G_define_flag();
    flag.hi->key = 'h';
    flag.hi->description = _("Reject high outliers");

    flag.lazy = G_define_flag();
    flag.lazy->key = 'z';
    flag.lazy->description = _("Don't keep files open");

    flag.int_only = G_define_flag();
    flag.int_only->key = 'i';
    flag.int_only->description = _("Do not extrapolate, only interpolate");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (parm.input->answer && parm.file->answer)
        G_fatal_error(_("input= and file= are mutually exclusive"));

    if (!parm.input->answer && !parm.file->answer)
        G_fatal_error(_("Please specify input= or file="));

    order = atoi(parm.order->answer);
    if (order < 0)
        G_fatal_error(_("The order number must be >= 0"));
    if (order > 3)
        G_fatal_error(_("The order number must be <= 3"));

    fet = DBL_MAX;
    if (parm.fet->answer) {
        fet = atof(parm.fet->answer);
        if (fet < 0)
            G_fatal_error(_("The fit error tolerance must be >= 0"));
    }
    dod = 0;
    if (parm.dod->answer) {
        dod = atoi(parm.dod->answer);
        if (dod < 0)
            G_fatal_error(_("The degree of over-determination must be >= 0"));
    }
    lo = -DBL_MAX;
    hi = DBL_MAX;
    if (parm.range->answer) {
        lo = atof(parm.range->answers[0]);
        hi = atof(parm.range->answers[1]);
    }
    delta = 0;
    if (parm.delta->answer) {
        delta = atof(parm.delta->answer);
        if (delta < 0 || delta > 1)
            G_fatal_error(
                _("The threshold for high amplitudes must be >= 0 and <= 1"));
    }

    rejlo = flag.lo->answer;
    rejhi = flag.hi->answer;
    if ((rejlo || rejhi) && !parm.fet->answer)
        G_fatal_error(_("Fit error tolerance is required when outliers should "
                        "be rejected"));

    weight_func = tricube;
    if (strcmp(parm.weight->answer, "uniform") == 0)
        weight_func = uniform;
    else if (strcmp(parm.weight->answer, "triangular") == 0)
        weight_func = triangular;
    else if (strcmp(parm.weight->answer, "epanechnikov") == 0)
        weight_func = epanechnikov;
    else if (strcmp(parm.weight->answer, "quartic") == 0)
        weight_func = quartic;
    else if (strcmp(parm.weight->answer, "tricube") == 0)
        weight_func = tricube;
    else if (strcmp(parm.weight->answer, "cosine") == 0)
        weight_func = cosine;
    else
        G_fatal_error(_("Unknown weighing function '%s'"), parm.weight->answer);

    interp_only = flag.int_only->answer;

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

    maxgap = ts[num_inputs - 1] - ts[0];
    if (parm.maxgap->answer) {
        maxgap = atof(parm.maxgap->answer);
    }

    /* open output maps */
    num_outputs = num_inputs;

    outputs = G_calloc(num_outputs, sizeof(struct output));

    suffix = parm.suffix->answer;
    if (!suffix)
        suffix = "_lwr";

    for (i = 0; i < num_outputs; i++) {
        struct output *out = &outputs[i];
        char xname[GNAME_MAX], xmapset[GMAPSET_MAX];
        const char *uname;
        char output_name[GNAME_MAX];

        uname = inputs[i].name;
        if (G_name_is_fully_qualified(inputs[i].name, xname, xmapset))
            uname = xname;
        sprintf(output_name, "%s%s", uname, suffix);

        out->name = G_store(output_name);
        out->buf = Rast_allocate_d_buf();
        out->fd = Rast_open_new(output_name, DCELL_TYPE);
    }

    min_points = 1 + order + dod;

    if (min_points > num_inputs)
        G_fatal_error(_("At least %d input maps are required for "
                        "order number %d and "
                        "degree of over-determination %d."),
                      min_points, order, dod);

    /* initialise variables */
    values = G_malloc(num_inputs * sizeof(DCELL));
    values2 = G_malloc(num_inputs * sizeof(DCELL));
    resultn = G_malloc(num_inputs * sizeof(DCELL));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    isnull = G_malloc(num_inputs * sizeof(int));

    msize = 1 + order;
    m = G_alloc_matrix(msize, msize);
    m2 = G_alloc_matrix(msize, msize);
    a = G_alloc_vector(msize);
    a2 = G_alloc_vector(msize);
    B = G_alloc_vector(msize);

    /* calculate weights for different margins */

    /* process the data */
    G_message(_("Local weighted regression of %d input maps..."), num_inputs);

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

        for (col = 0; col < ncols; col++) {

            first = last = -1;
            n_nulls = 0;
            for (i = 0; i < num_inputs; i++) {
                DCELL v = inputs[i].buf[col];

                isnull[i] = 0;
                if (Rast_is_d_null_value(&v)) {
                    isnull[i] = 1;
                    n_nulls++;
                }
                else if (parm.range->answer && (v < lo || v > hi)) {
                    Rast_set_d_null_value(&v, 1);
                    isnull[i] = 1;
                    n_nulls++;
                }
                else {
                    if (first == -1)
                        first = i;
                    last = i;
                }
                values[i] = v;
            }
            if (!interp_only) {
                first = 0;
                last = num_inputs - 1;
            }
            else {
                for (i = 0; i < first; i++)
                    Rast_set_d_null_value(&outputs[i].buf[col], 1);
                for (i = last + 1; i < num_inputs; i++)
                    Rast_set_d_null_value(&outputs[i].buf[col], 1);
            }

            /* LWR */
            if (num_inputs - n_nulls >= min_points) {

                thisgap = 0;
                prev_ts = next_ts = ts[0] - (ts[1] - ts[0]);

                for (i = first; i <= last; i++) {
                    DCELL result;

                    if (isnull[i]) {
                        if (next_ts < ts[i]) {
                            if (i > 0)
                                prev_ts = ts[i] - (ts[i] - ts[i - 1]) / 2.0;
                            else
                                prev_ts = ts[i] - (ts[i + 1] - ts[i]) / 2.0;

                            j = i;
                            while (j < num_inputs - 1 && isnull[j + 1])
                                j++;

                            if (j < num_inputs - 1)
                                next_ts = ts[j] + (ts[j + 1] - ts[j]) / 2.0;
                            else
                                next_ts = ts[j] + (ts[j] - ts[j - 1]) / 2.0;

                            thisgap = next_ts - prev_ts;
                        }
                        if (thisgap > maxgap) {
                            Rast_set_d_null_value(&outputs[i].buf[col], 1);
                            continue;
                        }
                    }

                    /* margin around i */
                    n_points = 0;
                    in_lo = in_hi = i;
                    this_margin = 0;
                    if (!isnull[i])
                        n_points++;
                    for (j = 1; j < num_inputs; j++) {
                        if (i - j >= 0) {
                            if (!isnull[i - j]) {
                                n_points++;
                                in_lo = i - j;
                            }
                        }
                        if (i + j < num_inputs) {
                            if (!isnull[i + j]) {
                                n_points++;
                                in_hi = i + j;
                            }
                        }
                        if (n_points >= min_points) {
                            this_margin = j;
                            break;
                        }
                    }
                    if (interp_only && isnull[i] &&
                        (in_lo == i || in_hi == i)) {

                        Rast_set_d_null_value(&outputs[i].buf[col], 1);
                        continue;
                    }

                    tsdiff1 = ts[i] - ts[in_lo];
                    tsdiff2 = ts[in_hi] - ts[i];

                    max_ts = tsdiff1;
                    if (max_ts < tsdiff2)
                        max_ts = tsdiff2;

                    max_ts *= (1.0 + 1.0 / this_margin);

                    /* initialize matrix and vectors */
                    for (j = 0; j <= order; j++) {
                        a[j] = 0;
                        B[j] = 0;
                        m[j][j] = 0;
                        for (k = 0; k < j; k++) {
                            m[j][k] = m[k][j] = 0;
                        }
                    }

                    /* load points */
                    for (n = in_lo; n <= in_hi; n++) {
                        if (isnull[n])
                            continue;

                        weight = weight_func(ts[i], ts[n], max_ts);
                        for (j = 0; j <= order; j++) {
                            double val1 = term(j, ts[n]);

                            for (k = j; k <= order; k++) {
                                double val2 = term(k, ts[n]);

                                m[j][k] += val1 * val2 * weight;
                            }
                            a[j] += values[n] * val1 * weight;
                        }
                    }

                    /* TRANSPOSE VALUES IN UPPER HALF OF M TO OTHER HALF */
                    m2[0][0] = m[0][0];
                    a2[0] = a[0];
                    for (j = 1; j <= order; j++) {
                        for (k = 0; k < j; k++) {
                            m[j][k] = m[k][j];
                            m2[j][k] = m2[k][j] = m[k][j];
                        }
                        m[j][j] *= (1 + delta);
                        m2[j][j] = m[j][j];
                        a2[j] = a[j];
                    }

                    if (solvemat(m2, a2, B, order + 1) != 0) {
                        /* get estimate */
                        result = 0.0;
                        for (j = 0; j <= order; j++) {
                            result += B[j] * term(j, ts[i]);
                        }

                        if (rejlo || rejhi) {
                            int done = 0;

                            for (n = in_lo; n <= in_hi; n++) {
                                if (isnull[n])
                                    continue;

                                values2[n] = values[n];
                            }

                            while (!done) {
                                done = 1;

                                maxerrlo = maxerrhi = 0;
                                for (n = in_lo; n <= in_hi; n++) {
                                    if (isnull[n])
                                        continue;

                                    resultn[n] = 0.0;
                                    for (j = 0; j <= order; j++) {
                                        resultn[n] += B[j] * term(j, ts[n]);
                                    }
                                    if (maxerrlo < resultn[n] - values2[n])
                                        maxerrlo = resultn[n] - values2[n];
                                    if (maxerrhi < values2[n] - resultn[n])
                                        maxerrhi = values2[n] - resultn[n];
                                }

                                if (rejlo && maxerrlo > fet)
                                    done = 0;
                                if (rejhi && maxerrhi > fet)
                                    done = 0;

                                if (!done) {

                                    a2[0] = 0;
                                    m2[0][0] = m[0][0];
                                    for (j = 1; j <= order; j++) {
                                        for (k = 0; k < j; k++) {
                                            m2[j][k] = m2[k][j] = m[k][j];
                                        }
                                        m2[j][j] = m[j][j];
                                        a2[j] = 0;
                                    }

                                    /* replace outliers */
                                    for (n = in_lo; n <= in_hi; n++) {
                                        if (isnull[n])
                                            continue;

                                        weight =
                                            weight_func(ts[i], ts[n], max_ts);
                                        if (rejlo && resultn[n] - values2[n] >
                                                         maxerrlo * 0.5) {
                                            values2[n] =
                                                (resultn[n] + values2[n]) * 0.5;
                                        }
                                        if (rejhi && values2[n] - resultn[n] >
                                                         maxerrhi * 0.5) {
                                            values2[n] =
                                                (values2[n] + resultn[n]) * 0.5;
                                        }
                                        for (j = 0; j <= order; j++) {
                                            double val1 = term(j, ts[n]);

                                            a2[j] += values2[n] * val1 * weight;
                                        }
                                    }
                                    done = 1;
                                    if (solvemat(m2, a2, B, order + 1) != 0) {
                                        /* update estimate */
                                        result = 0.0;
                                        for (j = 0; j <= order; j++) {
                                            result += B[j] * term(j, ts[i]);
                                        }
                                        done = 0;
                                    }
                                }
                            }
                        }
                    }
                    else {
                        double wsum = 0.0;

                        G_warning(_("Points are (nearly) co-linear, using "
                                    "weighted average"));

                        result = 0.0;
                        for (n = in_lo; n <= in_hi; n++) {
                            if (isnull[n])
                                continue;

                            weight = weight_func(ts[i], ts[n], max_ts);
                            result += values[n] * weight;
                            wsum += weight;
                        }
                        result /= wsum;
                    }
                    if (result < lo)
                        result = lo;
                    if (result > hi)
                        result = hi;
                    outputs[i].buf[col] = result;
                }
            }
            else {
                for (i = 0; i < num_outputs; i++) {
                    struct output *out = &outputs[i];

                    Rast_set_d_null_value(&out->buf[col], 1);
                }
            }
        }

        for (i = 0; i < num_outputs; i++)
            Rast_put_d_row(outputs[i].fd, outputs[i].buf);
    }

    G_percent(row, nrows, 2);

    /* close input and output maps */
    for (i = 0; i < num_outputs; i++) {
        struct input *in = &inputs[i];
        struct output *out = &outputs[i];

        if (!flag.lazy->answer)
            Rast_close(in->fd);

        Rast_close(out->fd);

        Rast_short_history(out->name, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(out->name, &history);

        if (Rast_read_colors(in->name, "", &colors) == 1)
            Rast_write_colors(out->name, G_mapset(), &colors);
    }

    exit(EXIT_SUCCESS);
}
