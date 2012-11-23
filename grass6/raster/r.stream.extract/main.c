
/****************************************************************************
 *
 * MODULE:       r.stream.extract
 * AUTHOR(S):    Markus Metz <markus.metz.giswork gmail.com>
 * PURPOSE:      Hydrological analysis
 *               Extracts stream networks from accumulation raster with
 *               given threshold
 * COPYRIGHT:    (C) 1999-2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#define MAIN
#include "local_proto.h"

/* global variables */
int nrows, ncols;
unsigned int *astar_pts;
unsigned int n_search_points, n_points, nxt_avail_pt;
unsigned int heap_size, *astar_added;
unsigned int n_stream_nodes, n_alloc_nodes;
struct point *outlets;
unsigned int n_outlets, n_alloc_outlets;
DCELL *acc;
CELL *ele;
char *asp;
CELL *stream;
FLAG *worked, *in_list;
char drain[3][3] = { {7, 6, 5}, {8, 0, 4}, {1, 2, 3} };
unsigned int first_cum;
char sides;
int c_fac;
int ele_scale;
int have_depressions;
struct RB_TREE *draintree;


int main(int argc, char *argv[])
{
    struct
    {
	struct Option *ele, *acc, *depression;
	struct Option *threshold, *d8cut;
	struct Option *mont_exp;
	struct Option *min_stream_length;
    } input;
    struct
    {
	struct Option *stream_rast;
	struct Option *stream_vect;
	struct Option *dir_rast;
    } output;
    struct GModule *module;
    int ele_fd, acc_fd, depr_fd;
    double threshold, d8cut, mont_exp;
    int min_stream_length = 0;
    char *mapset;

    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    module->keywords = _("raster");
    module->description = _("Stream network extraction");

    input.ele = G_define_standard_option(G_OPT_R_INPUT);
    input.ele->key = "elevation";
    input.ele->label = _("Elevation map");
    input.ele->description = _("Elevation on which entire analysis is based");

    input.acc = G_define_standard_option(G_OPT_R_INPUT);
    input.acc->key = "accumulation";
    input.acc->label = _("Accumulation map");
    input.acc->required = NO;
    input.acc->description =
	_("Stream extraction will use provided accumulation instead of calculating it anew");

    input.depression = G_define_standard_option(G_OPT_R_INPUT);
    input.depression->key = "depression";
    input.depression->label = _("Map with real depressions");
    input.depression->required = NO;
    input.depression->description =
	_("Streams will not be routed out of real depressions");

    input.threshold = G_define_option();
    input.threshold->key = "threshold";
    input.threshold->label = _("Minimum flow accumulation for streams");
    input.threshold->description = _("Must be > 0");
    input.threshold->required = YES;
    input.threshold->type = TYPE_DOUBLE;

    input.d8cut = G_define_option();
    input.d8cut->key = "d8cut";
    input.d8cut->label = _("Use SFD above this threshold");
    input.d8cut->description =
	_("If accumulation is larger than d8cut, SFD is used instead of MFD."
	  " Applies only if no accumulation map is given.");
    input.d8cut->required = NO;
    input.d8cut->type = TYPE_DOUBLE;

    input.mont_exp = G_define_option();
    input.mont_exp->key = "mexp";
    input.mont_exp->type = TYPE_DOUBLE;
    input.mont_exp->required = NO;
    input.mont_exp->answer = "0";
    input.mont_exp->label =
	_("Montgomery exponent for slope, disabled with 0");
    input.mont_exp->description =
	_("Montgomery: accumulation is multiplied with pow(slope,mexp) and then compared with threshold.");

    input.min_stream_length = G_define_option();
    input.min_stream_length->key = "stream_length";
    input.min_stream_length->type = TYPE_INTEGER;
    input.min_stream_length->required = NO;
    input.min_stream_length->answer = "0";
    input.min_stream_length->label =
	_("Delete stream segments shorter than stream_length cells.");
    input.min_stream_length->description =
	_("Applies only to first-order stream segments (springs/stream heads).");

    output.stream_rast = G_define_standard_option(G_OPT_R_OUTPUT);
    output.stream_rast->key = "stream_rast";
    output.stream_rast->description =
	_("Output raster map with unique stream ids");
    output.stream_rast->required = NO;
    output.stream_rast->guisection = _("Output options");

    output.stream_vect = G_define_standard_option(G_OPT_V_OUTPUT);
    output.stream_vect->key = "stream_vect";
    output.stream_vect->description =
	_("Output vector with unique stream ids");
    output.stream_vect->required = NO;
    output.stream_vect->guisection = _("Output options");

    output.dir_rast = G_define_standard_option(G_OPT_R_OUTPUT);
    output.dir_rast->key = "direction";
    output.dir_rast->description =
	_("Output raster map with flow direction");
    output.dir_rast->required = NO;
    output.dir_rast->guisection = _("Output options");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /***********************/
    /*    check options    */
    /***********************/

    /* input maps exist ? */
    if (!G_find_cell(input.ele->answer, ""))
	G_fatal_error(_("Raster map <%s> not found"), input.ele->answer);

    if (input.acc->answer) {
	if (!G_find_cell(input.acc->answer, ""))
	    G_fatal_error(_("Raster map <%s> not found"), input.acc->answer);
    }

    if (input.depression->answer) {
	if (!G_find_cell(input.depression->answer, ""))
	    G_fatal_error(_("Raster map <%s> not found"), input.depression->answer);
	have_depressions = 1;
    }
    else
	have_depressions = 0;

    /* threshold makes sense */
    threshold = atof(input.threshold->answer);
    if (threshold <= 0)
	G_fatal_error(_("Threshold must be > 0 but is %f"), threshold);

    /* d8cut */
    if (!input.d8cut->answer) {
	d8cut = DBL_MAX;
    }
    else {
	d8cut = atof(input.d8cut->answer);
	if (d8cut < 0)
	    G_fatal_error(_("d8cut must be positive or zero but is %f"),
			  d8cut);
    }

    /* Montgomery stream initiation */
    if (input.mont_exp->answer) {
	mont_exp = atof(input.mont_exp->answer);
	if (mont_exp < 0)
	    G_fatal_error(_("Montgomery exponent must be positive or zero but is %f"),
			  mont_exp);
	if (mont_exp > 3)
	    G_warning(_("Montgomery exponent is %f, recommended range is 0.0 - 3.0"),
		      mont_exp);
    }
    else
	mont_exp = 0;

    /* Minimum stream segment length */
    if (input.min_stream_length->answer) {
	min_stream_length = atoi(input.min_stream_length->answer);
	if (min_stream_length < 0)
	    G_fatal_error(_("Minimum stream length must be positive or zero but is %d"),
			  min_stream_length);
    }
    else
	min_stream_length = 0;

    /* Check for some output map */
    if ((output.stream_rast->answer == NULL)
	&& (output.stream_vect->answer == NULL)
	&& (output.dir_rast->answer == NULL)) {
	G_fatal_error(_("Sorry, you must choose at least one output map."));
    }

    /*********************/
    /*    preparation    */
    /*********************/

    /* open input maps */
    mapset = G_find_cell2(input.ele->answer, "");
    ele_fd = G_open_cell_old(input.ele->answer, mapset);
    if (ele_fd < 0)
	G_fatal_error(_("Could not open input map %s"), input.ele->answer);

    if (input.acc->answer) {
	mapset = G_find_cell2(input.acc->answer, "");
	acc_fd = G_open_cell_old(input.acc->answer, mapset);
	if (acc_fd < 0)
	    G_fatal_error(_("Could not open input map %s"),
			  input.acc->answer);
    }
    else
	acc_fd = -1;

    if (input.depression->answer) {
	mapset = G_find_cell2(input.depression->answer, "");
	depr_fd = G_open_cell_old(input.depression->answer, mapset);
	if (depr_fd < 0)
	    G_fatal_error(_("Could not open input map %s"),
			  input.depression->answer);
    }
    else
	depr_fd = -1;

    /* set global variables */
    nrows = G_window_rows();
    ncols = G_window_cols();
    sides = 8;			/* not a user option */
    c_fac = 5;			/* not a user option, MFD covergence factor 5 gives best results  */

    /* allocate memory */
    ele = (CELL *) G_malloc(nrows * ncols * sizeof(CELL));
    asp = (char *) G_malloc(nrows * ncols * sizeof(char));
    acc = (DCELL *) G_malloc(nrows * ncols * sizeof(DCELL));

    /* load maps */
    if (load_maps(ele_fd, acc_fd, depr_fd) < 0)
	G_fatal_error(_("Could not load input map(s)"));

    /********************/
    /*    processing    */
    /********************/

    /* sort elevation and get initial stream direction */
    if (do_astar() < 0)
	G_fatal_error(_("Could not sort elevation map"));

    /* extract streams */
    if (acc_fd < 0) {
	if (do_accum(d8cut) < 0)
	    G_fatal_error(_("Could not calculate flow accumulation"));
    }

    stream = (CELL *) G_malloc(nrows * ncols * sizeof(CELL));
    if (extract_streams
	(threshold, mont_exp, min_stream_length) < 0)
	G_fatal_error(_("Could not extract streams"));

    G_free(acc);

    /* thin streams */
    if (thin_streams() < 0)
	G_fatal_error(_("Could not extract streams"));

    /* delete short streams */
    if (min_stream_length) {
	if (del_streams(min_stream_length) < 0)
	    G_fatal_error(_("Could not extract streams"));
    }

    /* write output maps */
    if (close_maps(output.stream_rast->answer, output.stream_vect->answer,
		   output.dir_rast->answer) < 0)
	G_fatal_error(_("Could not write output maps"));

    G_free(ele);
    G_free(stream);
    G_free(asp);

    exit(EXIT_SUCCESS);
}
