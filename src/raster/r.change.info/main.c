/****************************************************************************
 *
 * MODULE:       r.change.info
 * AUTHOR(S):    Markus Metz
 *               based on r.neighbors
 *
 * PURPOSE:      Change assessment for categorical raster series
 *
 * COPYRIGHT:    (C) 2014 by the GRASS Development Team
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
#include "ncb.h"
#include "window.h"
#include "local_proto.h"

typedef DCELL dfunc(void);

struct menu {
    dfunc *method; /* routine to compute new value */
    char *name;    /* method name */
    char *text;    /* menu display - full description */
};

#define NO_CATS 0

/* modify this table to add new methods */
static struct menu menu[] = {
    {pc, "pc", "proportion of changes"},
    {gain1, "gain1", "Information gain for category distributions"},
    {gain2, "gain2", "Information gain for size distributions"},
    {gain3, "gain3", "Information gain for category and size distributions"},
    {ratio1, "ratio1", "Information gain ratio for category distributions"},
    {ratio2, "ratio2", "Information gain ratio for size distributions"},
    {ratio3, "ratio3",
     "Information gain ratio for category and size distributions"},
    {gini1, "gini1", "Gini impurity for category distributions"},
    {gini2, "gini2", "Gini impurity for size distributions"},
    {gini3, "gini3", "Gini impurity for category and size distributions"},
    {dist1, "dist1", "Statistical distance for category distributions"},
    {dist2, "dist2", "Statistical distance for size distributions"},
    {dist3, "dist3",
     "Statistical distance for category and size distributions"},
    {chisq1, "chisq1", "CHI-square for category distributions"},
    {chisq2, "chisq2", "CHI-square for size distributions"},
    {chisq3, "chisq3", "CHI-square for category and size distributions"},
    {NULL, NULL, NULL}};

struct ncb ncb;
struct changeinfo ci;

struct output {
    const char *name;
    char title[1024];
    int fd;
    DCELL *buf;
    dfunc *method_fn;
};

static int find_method(const char *method_name)
{
    int i;

    for (i = 0; menu[i].name; i++)
        if (strcmp(menu[i].name, method_name) == 0)
            return i;

    G_fatal_error(_("Unknown method <%s>"), method_name);

    return -1;
}

int make_colors(struct Colors *colr, DCELL min, DCELL max);

int main(int argc, char *argv[])
{
    char *p, *pp;
    size_t dlen;
    int num_outputs;
    struct output *outputs = NULL;
    RASTER_MAP_TYPE map_type;
    int row, col, ocol, roff, coff;
    int rspill, cspill;
    int orows, ocols;
    int readrow;
    int nrows, ncols;
    struct Range range;
    struct FPRange drange;
    DCELL dmin, dmax;
    CELL min, max, imin, imax;
    int i, n;
    int step;
    double alpha;
    struct Colors colr;
    struct Cell_head cellhd;
    struct Cell_head window, owind;
    struct History history;
    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *method, *wsize, *step, *alpha;
    } parm;
    struct {
        struct Flag *align, *circle;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("change detection"));
    G_add_keyword(_("landscape structure"));
    module->description = _("Landscape change assessment");

    parm.input = G_define_standard_option(G_OPT_R_INPUTS);

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->description = _("Name for output raster map(s)");
    parm.output->multiple = YES;

    parm.method = G_define_option();
    parm.method->key = "method";
    parm.method->type = TYPE_STRING;
    parm.method->required = NO;
    parm.method->answer = "ratio3";
    dlen = 0;
    for (n = 0; menu[n].name; n++) {
        dlen += strlen(menu[n].name);
    }
    dlen += n;
    p = G_malloc(dlen);
    for (n = 0; menu[n].name; n++) {
        if (n)
            strcat(p, ",");
        else
            *p = 0;
        strcat(p, menu[n].name);
    }
    parm.method->options = p;
    parm.method->description = _("Change assessment");
    dlen = 0;
    for (n = 0; menu[n].name; n++) {
        dlen += strlen(menu[n].name);
        dlen += strlen(menu[n].text);
    }
    dlen += n * 2;
    pp = G_malloc(dlen);
    for (n = 0; menu[n].name; n++) {
        if (n)
            strcat(pp, ";");
        else
            *pp = 0;
        strcat(pp, menu[n].name);
        strcat(pp, ";");
        strcat(pp, menu[n].text);
    }
    parm.method->descriptions = pp;
    parm.method->multiple = YES;

    parm.wsize = G_define_option();
    parm.wsize->key = "size";
    parm.wsize->type = TYPE_INTEGER;
    parm.wsize->required = NO;
    parm.wsize->description = _("Window size (cells)");
    parm.wsize->answer = "40";
    parm.wsize->guisection = _("Moving window");

    parm.step = G_define_option();
    parm.step->key = "step";
    parm.step->type = TYPE_INTEGER;
    parm.step->required = NO;
    parm.step->description = _("Processing step (cells)");
    parm.step->answer = "40";
    parm.step->guisection = _("Moving window");

    parm.alpha = G_define_option();
    parm.alpha->key = "alpha";
    parm.alpha->type = TYPE_DOUBLE;
    parm.alpha->required = NO;
    parm.alpha->label = _("Alpha for general entropy");
    parm.alpha->description = _("Default = 1 for Shannon Entropy");
    parm.alpha->answer = "1";

    flag.align = G_define_flag();
    flag.align->key = 'a';
    flag.align->description = _("Do not align input region with input maps");

    flag.circle = G_define_flag();
    flag.circle->key = 'c';
    flag.circle->description = _("Use circular mask");
    flag.circle->guisection = _("Moving window");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    sscanf(parm.wsize->answer, "%d", &ncb.nsize);
    if (ncb.nsize <= 1)
        G_fatal_error(_("Window size must be > 1"));
    ncb.n = ncb.nsize * ncb.nsize;

    sscanf(parm.step->answer, "%d", &step);
    if (step <= 0)
        G_fatal_error(_("Processing step must be positive"));

    if (step > ncb.nsize)
        G_fatal_error(_("Processing step can not be larger than window size"));

    sscanf(parm.alpha->answer, "%lf", &alpha);
    if (alpha <= 0)
        G_fatal_error(_("Alpha for general entropy must be positive"));
    set_alpha(alpha);

    for (i = 0; parm.input->answers[i]; i++)
        ;
    ncb.nin = i;
    if (ncb.nin < 2)
        G_fatal_error(_("At least two input maps are required"));

    ncb.in = G_malloc(ncb.nin * sizeof(struct input));

    for (i = 0; i < ncb.nin; i++)
        ncb.in[i].name = parm.input->answers[i];

    Rast_get_cellhd(ncb.in[0].name, "", &cellhd);
    G_get_window(&window);
    if (!flag.align->answer) {
        Rast_align_window(&window, &cellhd);
    }
    if (cellhd.rows < ncb.nsize)
        G_fatal_error(
            _("The current region is too small, it must have at least %d rows"),
            ncb.nsize);
    nrows = cellhd.rows;
    if (cellhd.cols < ncb.nsize)
        G_fatal_error(
            _("The current region is too small, it must have at least %d cols"),
            ncb.nsize);
    ncols = cellhd.cols;

    /* adjust the input window */
    roff = coff = 0;

    /* number of steps fitting into input rows */
    orows = (nrows - ncb.nsize) / step + 1;
    /* number of steps fitting into input cols */
    ocols = (ncols - ncb.nsize) / step + 1;

    rspill = nrows - ncb.nsize - (orows - 1) * step;
    if (rspill) {
        /* shrink input window */
        roff = rspill / 2;
        if (roff) {
            /* shift input north */
            window.north -= roff * window.ns_res;
        }
        /* shift input south */
        window.south += (rspill - roff) * window.ns_res;
        window.rows -= rspill;
    }
    cspill = ncols - ncb.nsize - (ocols - 1) * step;
    if (cspill) {
        /* shrink input window */
        coff = cspill / 2;
        if (coff) {
            /* shift input west */
            window.west += coff * window.ew_res;
        }
        /* shift input east */
        window.east -= (cspill - coff) * window.ew_res;
        window.cols -= cspill;
    }
    /* not needed */
    G_adjust_Cell_head(&window, 0, 0);

    Rast_set_input_window(&window);

    nrows = Rast_input_window_rows();
    ncols = Rast_input_window_cols();

    /* construct the output window */
    owind = window;
    owind.rows = orows;
    owind.cols = ocols;
    owind.ns_res = step * window.ns_res;
    owind.ew_res = step * window.ew_res;

    if (ncb.nsize != step) {
        owind.north = owind.north - ((ncb.nsize - step) / 2.0) * window.ns_res;
        owind.south = owind.south + ((ncb.nsize - step) / 2.0) * window.ns_res;

        owind.east = owind.east - ((ncb.nsize - step) / 2.0) * window.ew_res;
        owind.west = owind.west + ((ncb.nsize - step) / 2.0) * window.ew_res;
    }
    /* needed */
    G_adjust_Cell_head(&owind, 1, 1);

    Rast_set_output_window(&owind);

    /* open input raster maps */
    for (i = 0; i < ncb.nin; i++) {
        ncb.in[i].fd = Rast_open_old(ncb.in[i].name, "");
        map_type = Rast_get_map_type(ncb.in[i].fd);
        if (map_type != CELL_TYPE)
            G_warning(_("Input raster <%s> is not of type CELL"),
                      ncb.in[i].name);
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

    ncb.mask = NULL;

    for (i = 0; i < num_outputs; i++) {
        struct output *out = &outputs[i];
        const char *output_name = parm.output->answers[i];
        const char *method_name = parm.method->answers[i];
        int method = find_method(method_name);

        out->name = output_name;
        out->method_fn = menu[method].method;

        out->buf = Rast_allocate_d_output_buf();
        out->fd = Rast_open_new(output_name, DCELL_TYPE);

        sprintf(out->title, "%s, %dx%d window, step %d", menu[method].text,
                ncb.nsize, ncb.nsize, step);
    }

    if (flag.circle->answer)
        circle_mask();

    /* initialize change info */
    frexp(ncb.n, &ci.nsizebins);
    G_debug(1, "n cells: %d, size * size: %d", ncb.n, ncb.nsize * ncb.nsize);
    G_debug(1, "nsizebins: %d", ci.nsizebins);

    /* max number of different types */
    Rast_init_range(&range);
    Rast_read_range(ncb.in[0].name, "", &range);
    Rast_get_range_min_max(&range, &min, &max);
    for (i = 1; i < ncb.nin; i++) {
        Rast_init_range(&range);
        Rast_read_range(ncb.in[i].name, "", &range);
        Rast_get_range_min_max(&range, &imin, &imax);
        if (min > imin)
            min = imin;
        if (max < imax)
            max = imax;
    }
    ci.tmin = min;
    ci.ntypes = max - min + 1;
    ci.dts_size = ci.ntypes * ci.nsizebins;

    ci.n = G_malloc(ncb.nin * sizeof(int));
    ci.dt = G_malloc(ncb.nin * sizeof(double *));
    ci.dt[0] = G_malloc(ncb.nin * ci.ntypes * sizeof(double));
    ci.ds = G_malloc(ncb.nin * sizeof(double *));
    ci.ds[0] = G_malloc(ncb.nin * ci.nsizebins * sizeof(double));
    ci.dts = G_malloc(ncb.nin * sizeof(double *));
    ci.dts[0] = G_malloc(ncb.nin * ci.dts_size * sizeof(double));
    ci.ht = G_malloc(ncb.nin * sizeof(double));
    ci.hs = G_malloc(ncb.nin * sizeof(double));
    ci.hts = G_malloc(ncb.nin * sizeof(double));

    ci.ch = G_malloc(ncb.nin * sizeof(struct c_h));

    for (i = 0; i < ncb.nin; i++) {
        ci.ch[i].palloc = ci.ntypes;
        ci.ch[i].pst = G_malloc(ci.ntypes * sizeof(struct pst));

        ci.ch[i].pid_curr = G_malloc(ncb.nsize * sizeof(int));
        ci.ch[i].pid_prev = G_malloc(ncb.nsize * sizeof(int));

        if (i > 0) {
            ci.dt[i] = ci.dt[i - 1] + ci.ntypes;
            ci.ds[i] = ci.ds[i - 1] + ci.nsizebins;
            ci.dts[i] = ci.dts[i - 1] + ci.dts_size;
        }
    }

    /* allocate the cell buffers */
    allocate_bufs();

    /* initialize the cell bufs with 'nsize - 1' rows of the old cellfile */
    readrow = 0;
    for (row = 0; row < ncb.nsize - 1; row++)
        readcell(readrow++, nrows, ncols);

    for (row = 0; row < nrows - ncb.nsize + 1; row++) {
        G_percent(row, nrows, 5);
        readcell(readrow++, nrows, ncols);

        if (row % step)
            continue;

        for (col = 0, ocol = 0; col < ncols - ncb.nsize + 1;
             col += step, ocol++) {

            n = gather(col);

            for (i = 0; i < num_outputs; i++) {
                struct output *out = &outputs[i];
                DCELL *rp = &out->buf[ocol];

                if (n == 0) {
                    Rast_set_d_null_value(rp, 1);
                }
                else {
                    *rp = (*out->method_fn)();
                }
            }
        }

        for (i = 0; i < num_outputs; i++) {
            struct output *out = &outputs[i];

            Rast_put_d_row(out->fd, out->buf);
        }
    }
    G_percent(row, nrows, 2);

    for (i = 0; i < ncb.nin; i++)
        Rast_close(ncb.in[i].fd);

    for (i = 0; i < num_outputs; i++) {
        char ncs;
        int nc;

        Rast_close(outputs[i].fd);

        Rast_short_history(outputs[i].name, "raster", &history);
        Rast_command_history(&history);
        ncs = parm.method->answers[i][strlen(parm.method->answers[i]) - 1];
        nc = 0;
        if (ncs == '1')
            nc = ci.ntypes;
        else if (ncs == '2')
            nc = ci.nsizebins;
        else if (ncs == '3')
            nc = ci.dts_size;
        Rast_format_history(
            &history, HIST_DATSRC_1,
            "Change assessment with %s, %d classes, window size %d, step %d",
            parm.method->answers[i], nc, ncb.nsize, step);
        Rast_write_history(outputs[i].name, &history);

        Rast_put_cell_title(outputs[i].name, outputs[i].title);

        Rast_init_fp_range(&drange);
        Rast_read_fp_range(outputs[i].name, G_mapset(), &drange);
        Rast_get_fp_range_min_max(&drange, &dmin, &dmax);
        make_colors(&colr, dmin, dmax);
        Rast_write_colors(outputs[i].name, G_mapset(), &colr);
    }

    exit(EXIT_SUCCESS);
}

int make_colors(struct Colors *colr, DCELL min, DCELL max)
{
    DCELL val1, val2;
    int r1, g1, b1, r2, g2, b2;
    DCELL rng;

    if (Rast_is_d_null_value(&min)) {
        min = 0;
        max = 1;
    }
    if (min > 0)
        min = 0;

    rng = max - min;

    /* colors: green -> yellow -> orange -> red */
    Rast_init_colors(colr);
    val1 = min;
    val2 = min + rng * 0.2;
    r1 = 150;
    g1 = 255;
    b1 = 150;
    r2 = 255;
    g2 = 255;
    b2 = 0;
    Rast_add_d_color_rule(&val1, r1, g1, b1, &val2, r2, g2, b2, colr);
    val1 = val2;
    r1 = r2;
    g1 = g2;
    b1 = b2;
    val2 = min + rng * 0.5;
    r2 = 255;
    g2 = 122;
    b2 = 0;
    Rast_add_d_color_rule(&val1, r1, g1, b1, &val2, r2, g2, b2, colr);
    val1 = val2;
    r1 = r2;
    g1 = g2;
    b1 = b2;
    val2 = max + 1.0e-12;
    r2 = 255;
    g2 = 0;
    b2 = 0;
    Rast_add_d_color_rule(&val1, r1, g1, b1, &val2, r2, g2, b2, colr);

    return 1;
}
