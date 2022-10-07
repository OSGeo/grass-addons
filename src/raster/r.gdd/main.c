
/****************************************************************************
 *
 * MODULE:       r.gdd
 * AUTHOR(S):    Markus Metz
 *               based on r.series
 * PURPOSE:      Calculate GDD, Winler index, BEDD, Huglin
 * COPYRIGHT:    (C) 2012 by the GRASS Development Team
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

#define IDX_GDD 1
#define IDX_WINKLER 2
#define IDX_BEDD 3
#define IDX_HUGLIN 4

struct input
{
    const char *name;
    int fd;
    FCELL *buf;
};

struct output
{
    const char *name;
    int fd;
    FCELL *buf;
};

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct
    {
	struct Option *input, *add, *file, *output, *index, *range,
	              *scale, *shift, *baseline, *cutoff;
    } parm;
    struct
    {
	struct Flag *nulls, *lazy;
    } flag;
    char *desc = NULL;
    int idx, i;
    int num_inputs, max_inputs, add_in;
    struct input *inputs = NULL;
    struct output *out = NULL;
    struct History history;
    struct Colors colors;
    int nrows, ncols;
    int row, col;
    double lo, hi, tscale, tshift, baseline, cutoff;
    FCELL fnull;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    G_add_keyword(_("parallel"));
    module->description =
	_("Makes each output cell value a "
	  "function of the values assigned to the corresponding cells "
	  "in the input raster map layers.");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);
    parm.input->required = NO;

    parm.add = G_define_standard_option(G_OPT_R_INPUT);
    parm.add->key = "add";
    parm.add->description = _("Existing map to be added to output");
    parm.add->required = NO;

    parm.file = G_define_standard_option(G_OPT_F_INPUT);
    parm.file->key = "file";
    parm.file->description = _("Input file with raster map names, one per line");
    parm.file->required = NO;

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->multiple = NO;

    parm.index = G_define_option();
    parm.index->key = "index";
    parm.index->type = TYPE_STRING;
    parm.index->multiple = NO;
    parm.index->required = NO;
    parm.index->options = "gdd,winkler,bedd,huglin";
    parm.index->answer = "gdd";
    parm.index->label = "Index to calculate";
    G_asprintf(&desc,
	       "gdd;%s;winkler;%s;bedd;%s;huglin;%s",
	       _("Growing Degree Days"),
	       _("Winkler index"),
	       _("Biologically Effective Degree Days"),
	       _("Huglin Heliothermal index"));
    parm.index->descriptions = desc;

    parm.scale = G_define_option();
    parm.scale->key = "scale";
    parm.scale->type = TYPE_DOUBLE;
    parm.scale->answer = "1.0";
    parm.scale->required = NO;
    parm.scale->description = _("Scale factor for input");

    parm.shift = G_define_option();
    parm.shift->key = "shift";
    parm.shift->type = TYPE_DOUBLE;
    parm.shift->answer = "0.0";
    parm.shift->required = NO;
    parm.shift->description = _("Shift factor for input");

    parm.baseline = G_define_option();
    parm.baseline->key = "baseline";
    parm.baseline->type = TYPE_DOUBLE;
    parm.baseline->required = NO;
    parm.baseline->answer = "10";
    parm.baseline->description = _("Baseline temperature");

    parm.cutoff = G_define_option();
    parm.cutoff->key = "cutoff";
    parm.cutoff->type = TYPE_DOUBLE;
    parm.cutoff->required = NO;
    parm.cutoff->answer = "30";
    parm.cutoff->description = _("Cutoff temperature");

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

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    lo = -1.0 / 0.0;
    hi = 1.0 / 0.0;
    if (parm.range->answer) {
	lo = atof(parm.range->answers[0]);
	hi = atof(parm.range->answers[1]);
    }

    if (parm.scale->answer)
	tscale = atof(parm.scale->answer);
    else
	tscale = 1.;

    if (parm.shift->answer)
	tshift = atof(parm.shift->answer);
    else
	tshift = 0.;

    baseline = atof(parm.baseline->answer);
    cutoff = atof(parm.cutoff->answer);
    
    idx = 0;
    if (strcmp(parm.index->answer, "gdd") == 0)
	idx = IDX_GDD;
    else if (strcmp(parm.index->answer, "winkler") == 0)
	idx = IDX_WINKLER;
    else if (strcmp(parm.index->answer, "bedd") == 0)
	idx = IDX_BEDD;
    else if (strcmp(parm.index->answer, "huglin") == 0)
	idx = IDX_HUGLIN;
    else
        G_fatal_error(_("Unknown index '%s' for option %s"),
	              parm.index->answer, parm.index->key);
    
    if (cutoff <= baseline)
        G_fatal_error(_("'%s' must be > '%s'"), parm.cutoff->key,
	                                        parm.baseline->key);

    if (parm.input->answer && parm.file->answer)
        G_fatal_error(_("input= and file= are mutually exclusive"));
 
    if (!parm.input->answer && !parm.file->answer)
        G_fatal_error(_("Please specify input= or file="));

    max_inputs = 0;
    /* process the input maps from the file */
    if (parm.file->answer) {
	FILE *in;
    
	in = fopen(parm.file->answer, "r");
	if (!in)
	    G_fatal_error(_("Unable to open input file <%s>"), parm.file->answer);
    
	num_inputs = 0;

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
	    p->buf = Rast_allocate_f_buf();
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
	    p->buf = Rast_allocate_f_buf();
	    if (!flag.lazy->answer)
		p->fd = Rast_open_old(p->name, "");
    	}
	max_inputs = num_inputs;
    }

    if (parm.add->answer) {
	struct input *p;

	add_in = 1;
	if (num_inputs + 1 >= max_inputs) {
	    max_inputs += 2;
	    inputs = G_realloc(inputs, max_inputs * sizeof(struct input));
	}
	p = &inputs[num_inputs];
	p->name = parm.add->answer;
	G_verbose_message(_("Reading raster map <%s>..."), p->name);
	p->buf = Rast_allocate_f_buf();
	if (!flag.lazy->answer)
	    p->fd = Rast_open_old(p->name, "");
    }
    else
	add_in = 0;

    out = G_calloc(1, sizeof(struct output));

    out->name = parm.output->answer;

    out->buf = Rast_allocate_f_buf();
    out->fd = Rast_open_new(out->name, FCELL_TYPE);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    
    Rast_set_f_null_value(&fnull, 1);

    /* process the data */
    G_verbose_message(_("Percent complete..."));

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	if (flag.lazy->answer) {
	    /* Open the files only on run time */
	    for (i = 0; i < num_inputs + add_in; i++) {
		inputs[i].fd = Rast_open_old(inputs[i].name, "");
		Rast_get_f_row(inputs[i].fd, inputs[i].buf, row);
		Rast_close(inputs[i].fd);
	    }
	}
	else {
	    for (i = 0; i < num_inputs + add_in; i++)
	        Rast_get_f_row(inputs[i].fd, inputs[i].buf, row);
	}

        #pragma omp for schedule (static) private (col)

	for (col = 0; col < ncols; col++) {
	    int null = 0, non_null = 0;
	    FCELL min, max, avg, result;

	    min = fnull;
	    max = fnull;
	    avg = 0;

	    for (i = 0; i < num_inputs; i++) {
		FCELL v = inputs[i].buf[col];

		if (Rast_is_f_null_value(&v))
		    null = 1;
		else {
		    v = v * tscale + tshift;
		    if (parm.range->answer && (v < lo || v > hi)) {
			null = 1;
		    }
		    else {
			avg += v;
			if (Rast_is_f_null_value(&min) || min > v)
			    min = v;
			if (Rast_is_f_null_value(&max) || max < v)
			    max = v;
			non_null++;
		    }
		}
	    }

	    if (!non_null || (null && flag.nulls->answer)) {
		if (add_in)
		    result = inputs[num_inputs].buf[col];
		else
		    result = fnull;
	    }
	    else {

		avg /= non_null;

		if (idx == IDX_HUGLIN)
		    avg = (avg + max) / 2.;

		if (avg < baseline)
		    avg = baseline;
		if (idx == IDX_BEDD && avg > cutoff)
		    avg = cutoff;

		result = avg - baseline;

		if (result < 0.)
		    result = 0.;
		if (add_in)
		    result += inputs[num_inputs].buf[col];

	    }
	    out->buf[col] = result;
	}

	Rast_put_f_row(out->fd, out->buf);
    }

    G_percent(row, nrows, 2);

    /* close output map */
    Rast_close(out->fd);

    Rast_short_history(out->name, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(out->name, &history);

    /* Close input maps */
    if (!flag.lazy->answer) {
    	for (i = 0; i < num_inputs + add_in; i++)
	    Rast_close(inputs[i].fd);
    }

    /* set gdd color table */
    Rast_init_colors(&colors);
    Rast_make_colors(&colors, "gdd", 0, 6000);
    Rast_write_colors(out->name, G_mapset(), &colors);

    exit(EXIT_SUCCESS);
}
