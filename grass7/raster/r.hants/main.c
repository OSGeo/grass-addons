
/****************************************************************************
 *
 * MODULE:       r.hants
 * AUTHOR(S):    Wout Verhoef, NLR, Remote Sensing Dept., June 1998
 *               Mohammad Abouali, converted to MATLAB, 2011
 *               Markus Metz, converted to C, 2013
 *               based on r.series
 * PURPOSE:      time series correction
 * COPYRIGHT:    (C) 2013 by the GRASS Development Team
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
};

static int solvemat(double **m, double a[], double B[], int n)
{
    int i, j, i2, j2, imark;
    double factor, temp;
    double pivot;		/* ACTUAL VALUE OF THE LARGEST PIVOT CANDIDATE */

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

	if (pivot == 0.0) {
	    G_warning(_("Matrix is unsolvable"));
	    return 0;
	}

	/* if row with highest pivot is not the current row, switch them */

	if (imark != i) {
	    for (j2 = 0; j2 < n; j2++) {
		temp = m[imark][j2];
		m[imark][j2] = m[i][j2];
		m[i][j2] = temp;
	    }

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


int main(int argc, char *argv[])
{
    struct GModule *module;
    struct
    {
	struct Option *input, *file,
	              *nf,	/* number of harmonics */
		      *fet,	/* fit error tolerance */
		      *dod,	/* degree of over-determination */
	              *range,	/* low/high threshold */
		      *ts,	/* time steps*/
		      *bl,	/* length of base period */
		      *delta;	/* threshold for high amplitudes */
    } parm;
    struct
    {
	struct Flag *lo, *hi, *lazy;
    } flag;
    int i, j, k;
    int num_inputs;
    struct input *inputs = NULL;
    int num_outputs;
    struct output *outputs = NULL;
    struct History history;
    DCELL *values = NULL, *rc = NULL;
    int nrows, ncols;
    int row, col;
    double lo, hi, fet, *cs, *sn, *ts, delta;
    int bl;
    double **mat, **mat_t, **A, *za, *zr, maxerrlo, maxerrhi;
    int dod, nf, nr, nout, noutmax;
    int rejlo, rejhi, *useval, dumped;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    G_add_keyword(_("filtering"));
    module->description =
	_("Approximates a periodic time series "
	  "and creates approximated output.");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);
    parm.input->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description = _("Input file with raster map names, one per line");
    parm.file->required = NO;

    parm.nf = G_define_option();
    parm.nf->key = "nf";
    parm.nf->type = TYPE_INTEGER;
    parm.nf->required = YES;
    parm.nf->description = _("Number of frequencies");
    parm.nf->multiple = YES;

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

    parm.bl = G_define_option();
    parm.bl->key = "base_period";
    parm.bl->type = TYPE_INTEGER;
    parm.bl->description = _("Length of the base period");

    parm.delta = G_define_option();
    parm.delta->key = "base_period";
    parm.delta->type = TYPE_DOUBLE;
    parm.delta->answer = "0";
    parm.delta->description = _("Threshold for high amplitudes");

    flag.lo = G_define_flag();
    flag.lo->key = 'l';
    flag.lo->description = _("Reject low outliers");

    flag.hi = G_define_flag();
    flag.hi->key = 'h';
    flag.hi->description = _("Reject high outliers");

    flag.lazy = G_define_flag();
    flag.lazy->key = 'z';
    flag.lazy->description = _("Don't keep files open");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    if (parm.input->answer && parm.file->answer)
        G_fatal_error(_("input= and file= are mutually exclusive"));
 
    if (!parm.input->answer && !parm.file->answer)
        G_fatal_error(_("Please specify input= or file="));

    nf = atoi(parm.nf->answer);
    if (nf < 1)
	G_fatal_error(_("The number of frequencies must be > 0"));

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
    }
    
    rejlo = flag.lo->answer;
    rejhi = flag.hi->answer;

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

    /* length of base period */
    if (parm.bl->answer)
	bl = atoi(parm.bl->answer);
    else
	bl = num_inputs;

    num_outputs = num_inputs;

    outputs = G_calloc(num_outputs, sizeof(struct output));

    for (i = 0; i < num_outputs; i++) {
	struct output *out = &outputs[i];
	char output_name[GNAME_MAX];
	
	sprintf(output_name, "%s_hants", inputs[i].name);

	out->name = G_store(output_name);
	out->buf = Rast_allocate_d_buf();
	out->fd = Rast_open_new(output_name, DCELL_TYPE);
    }

    /* initialise variables */
    values = G_malloc(num_inputs * sizeof(DCELL));

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    cs = G_alloc_vector(bl);
    sn = G_alloc_vector(bl);
    ts = G_alloc_vector(num_inputs);
    rc = G_malloc(num_inputs * sizeof(DCELL));
    useval = G_malloc(num_inputs * sizeof(int));

    if (parm.ts->answer) {
    	for (i = 0; parm.ts->answers[i]; i++);
	if (i != num_inputs)
	    G_fatal_error(_("Number of time steps does not match number of input maps"));
    	for (i = 0; parm.ts->answers[i]; i++)
	    ts[i] = atof(parm.ts->answers[i]);
    }
    else {
	for (i = 0; i < num_inputs; i++) {
	    ts[i] = i;
	}
    }
    
    if (2 * nf + 1 < num_inputs)
	nr = 2 * nf + 1;
    else
	nr = num_inputs;

    noutmax = num_inputs - nr - dod;

    /* are the dimensions correct ? */
    mat = G_alloc_matrix(nr, num_inputs);
    mat_t = G_alloc_matrix(num_inputs, nr);
    A = G_alloc_matrix(nr, nr);
    za = G_alloc_vector(nr);
    zr = G_alloc_vector(nr);
    rc = G_alloc_vector(num_inputs);

    for (i = 0; i < bl; i++) {
	double ang = 2.0 * M_PI * i / bl;

	cs[i] = cos(ang);
	sn[i] = sin(ang);
    }
    for (j = 0; j < num_inputs; j++) {
	mat[0][j] = 1.;
	mat_t[j][0] = 1.;
    }

    for (i = 0; i < nr / 2; i++) {
	int i1 = 2 * i + 1;
	int i2 = 2 * i + 2;

	for (j = 0; j < num_inputs; j++) {

	    int idx = (int) ((i + 1) * (ts[j] - 1)) % bl;
	    
	    if (idx >= bl)
		G_fatal_error("cs/sn index out of range: %d, %d", idx, bl);

	    if (i2 >= nr)
		G_fatal_error("mat index out of range: %d, %d", 2 * i + 2, nr);
		
	    mat[i1][j] = cs[idx];
	    mat[i2][j] = sn[idx];
	    mat_t[j][i1] = mat[i1][j];
	    mat_t[j][i2] = mat[i2][j];
	}
    }


    /* process the data */
    G_verbose_message(_("Percent complete..."));

    dumped = 0;

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

		useval[i] = 0;
		if (Rast_is_d_null_value(&v)) {
		    null++;
		}
		else if (parm.range->answer && (v < lo || v > hi)) {
		    Rast_set_d_null_value(&v, 1);
		    null++;
		}
		else {
		    non_null++;
		    useval[i] = 1;
		}

		values[i] = v;
	    }
	    nout = null;

	    /* HANTS */
	    if (nout <= noutmax) {
		int n = 0, done = 0;

		while (!done) {
		    
		    /* za = mat * y */

		    /* A = mat * diag(p) * mat' */

		    /* mat: nr, num_inputs
		     * diag(p): num_inputs, num_inputs 
		     * mat_t: num_inputs, nr
		     * A temp: nr, num_inputs
		     * A: nr, nr */

		    for (i = 0; i < nr; i++) {
			za[i] = 0;
			for (j = 0; j < num_inputs; j++) {
			    if (useval[j])
				za[i] += mat[i][j] * values[j];
			}

			for (j = 0; j < nr; j++) {
			    A[i][j] = 0;
			    for (k = 0; k < num_inputs; k++) {
				if (useval[k])
				    A[i][j] += mat[i][k] * mat_t[k][j];
			    }
			    if (i > 0 && i == j)
				A[i][j] += delta;
			}
		    }
		    
		    /* zr = A \ za
		     * solve A * zr = za */
		    if (!solvemat(A, za, zr, nr)) {

			/*
			fprintf(stdout, "za:\n");
			for (i = 0; i < nr; i++)
			    fprintf(stdout, "%g\n", za[i]);
			    
			fprintf(stdout, "matrix A:\n");
			for (i = 0; i < nr; i++) {
			    for (j = 0; j < nr; j++) {
				fprintf(stdout, "%g  ", M(A, i, j));
			    }
			    fprintf(stdout, "\n");
			}

			G_fatal_error(_("Unable to solve matrix!"));
			*/
			done = -1;
			Rast_set_d_null_value(rc, num_outputs);
			break;
		    }

		    /* rc = mat' * zr */
		    maxerrlo = maxerrhi = 0;
		    for (i = 0; i < num_inputs; i++) {
			rc[i] = 0;
			for (j = 0; j < nr; j++) {
			    rc[i] += mat_t[i][j] * zr[j];
			}
			if (useval[i]) {
			    if (maxerrlo < rc[i] - values[i])
				maxerrlo = rc[i] - values[i];
			    if (maxerrhi < values[i] - rc[i])
				maxerrhi = values[i] - rc[i];

			}
		    }
		    if (rejlo && maxerrlo < fet) {
			done = 1;
		    }

		    if (rejhi && maxerrhi < fet) {
			done = 1;
		    }
		    
		    if (!done && (rejlo || rejhi)) {
			/* filter outliers */
			for (i = 0; i < num_inputs; i++) {

			    if (useval[i]) {
				if (rejlo && rc[i] - values[i] > maxerrlo * 0.5) {
				    useval[i] = 0;
				    nout++;
				}
				if (rejhi && values[i] - rc[i] > maxerrhi * 0.5) {
				    useval[i] = 0;
				    nout++;
				}
			    }
			}
		    }

		    n++;
		    if (n >= num_inputs)
			done = 1;
		    if (nout > noutmax)
			done = 1;
		}

		for (i = 0; i < num_outputs; i++) {
		    struct output *out = &outputs[i];
		    
		    out->buf[col] = rc[i];
		}
		
		if (non_null >= 20 && done == 1 && !dumped &&
		    row > nrows / 3 && col > ncols / 2 ) {
#if 0
		    for (i = 0; i < num_inputs; i++) {
			fprintf(stdout, "%g;%g\n", values[i], rc[i]);
		    }
#endif
		    dumped = 1;
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
