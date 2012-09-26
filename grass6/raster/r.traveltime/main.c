/* main.c for r.traveltime, December 2007
 *
 * ############################################################################
 * #
 * # MODULE:       r.traveltime
 * #
 * # AUTHOR(S):    Kristian Foerster
 * #
 * # PURPOSE:      This programm calculates traveltimes from a digital
 * #               terrain model, a roughness grid and some output
 * #               files from r.watershed. The aim of this tool is to
 * #               estimate a unit hydrograph for precipitation-runoff
 * #               prediction
 * #
 * # COPYRIGHT:    (c) 2007 Kristian Foerster
 * #
 * #               This program is free software under the GNU General Public
 * #               License
 * #
 * #############################################################################
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include <float.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/config.h>


/* 
 * global declarations
 */
extern CELL f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

double res_x, res_y;
void *inrast_accu, *inrast_dtm, *inrast_n, *inrast_dir;	/* input buffer */
unsigned char *outrast;		/* output buffer */
int in_accu, in_dir, in_n, in_dtm, outfd;	/* file descriptor */
RASTER_MAP_TYPE data_type_accu, data_type_dtm, data_type_n, data_type_dir;	/* type of the map (CELL/DCELL/...) */
double **array_out;
int ac_thres;
double nc, b, ep, fdis;

/*
 * the function inflow checks if an adjacent cell discharges in the active cell
 */

int inflow(int loc_x, int loc_y, int vec_x, int vec_y)
{

    int x_exp, y_exp;
    int value;

    if (G_get_raster_row(in_dir, inrast_dir, loc_y, data_type_dir) < 0)
	G_fatal_error(_("Could not read from map"));
    value = ((CELL *) inrast_dir)[loc_x];

    // conversions of the flow direction classification to vectors

    switch (value) {
    case 1:
	x_exp = 1;
	y_exp = -1;
	break;
    case 2:
	x_exp = 0;
	y_exp = -1;
	break;
    case 3:
	x_exp = -1;
	y_exp = -1;
	break;
    case 4:
	x_exp = -1;
	y_exp = 0;
	break;
    case 5:
	x_exp = -1;
	y_exp = 1;
	break;
    case 6:
	x_exp = 0;
	y_exp = 1;
	break;
    case 7:
	x_exp = 1;
	y_exp = 1;
	break;
    case 8:
	x_exp = 1;
	y_exp = 0;
	break;
    default:
	x_exp = 1;
	y_exp = 0;
	break;
    }
    if ((vec_x == x_exp * (-1)) & (vec_y == y_exp * (-1)))
	return 1;
    else
	return 0;
}

/*
 * traveltime calculates traveltimes from one cell to another
 */

double traveltime(double length, double slope, double manning,
		  double drainage)
{
    double slope_min = 0.001;
    double t;
    double Q;

    if (slope < slope_min)
	slope = slope_min;

    /* for areas with drainage accumulation < threshold surface runoff will be calculated
     * areas with larger drainage accumulation the channel formula is used instead
     */

    if (drainage < ac_thres) {
	t = pow(length, 0.6) * pow(manning, 0.6) / pow(ep / 1000.0 / 3600.0, 0.4) / pow(slope, 0.3);	//surface runoff
    }
    else {
	Q = fdis * drainage * res_x * res_y * ep / 1000.0 / 3600.0;	//equilibrium runoff
	t = length / pow(sqrt(slope) / nc * pow(Q / b, (2.0 / 3.0)), 0.6);	// channel runoff
    }

    return t / 60.0;		//seconds to minutes
}

/*
 * ttime is a recursive function starting at the outlet moving up to the watershed boundary
 * calling the inflow and traveltime functions
 */


int ttime(double ftime, int x, int y, int dx, int dy)
{
    double thist = 0;
    double L, J;
    int i, j, v, accu, dir;
    double z1, z2;
    double manningsn;

    if (G_get_raster_row(in_dir, inrast_dir, y, data_type_dir) < 0)
	G_fatal_error(_("Could not read from map"));
    dir = ((CELL *) inrast_dir)[x];

    if (G_get_raster_row(in_accu, inrast_accu, y, data_type_accu) < 0)
	G_fatal_error(_("Could not read from map"));
    accu = ((CELL *) inrast_accu)[x];

    if (G_get_raster_row(in_n, inrast_n, y, data_type_n) < 0)
	G_fatal_error(_("Could not read from map"));
    switch (data_type_n) {
    case DCELL_TYPE:
	manningsn = (double)((DCELL *) inrast_n)[x];
	break;
    case FCELL_TYPE:
	manningsn = (double)((FCELL *) inrast_n)[x];
	break;
    }

    if (G_get_raster_row(in_dtm, inrast_dtm, y, data_type_dtm) < 0)
	G_fatal_error(_("Could not read from map"));
    switch (data_type_dtm) {
    case CELL_TYPE:
	z2 = (double)((CELL *) inrast_dtm)[x];
	break;
    case DCELL_TYPE:
	z2 = (double)((DCELL *) inrast_dtm)[x];
	break;
    case FCELL_TYPE:
	z2 = (double)((FCELL *) inrast_dtm)[x];
	break;
    }

    if (G_get_raster_row(in_dtm, inrast_dtm, y - dy, data_type_dtm) < 0)
	G_fatal_error(_("Could not read from map"));
    switch (data_type_dtm) {
    case CELL_TYPE:
	z1 = (double)((CELL *) inrast_dtm)[x - dx];
	break;
    case DCELL_TYPE:
	z1 = (double)((DCELL *) inrast_dtm)[x - dx];
	break;
    case FCELL_TYPE:
	z1 = (double)((FCELL *) inrast_dtm)[x - dx];
	break;
    }



    for (i = -1; i < 2; i++) {
	for (j = -1; j < 2; j++) {
	    if (inflow(x + i, y + j, i, j) > 0) {
		L = sqrt(pow(i * res_x, 2.0) + pow(j * res_y, 2.0));
		J = 1.0 * (z2 - z1) / L;
		// time from here to outlet
		thist = ftime + traveltime(L, J, manningsn, accu);
		array_out[y + j][x + i] = thist;
		int r = ttime(thist, x + i, y + j, i, j);

		v = 1;
	    }
	    else {
		v = 0;
	    }
	}
    }
    return v;
}


/*
 * main function
 */

int main(int argc, char *argv[])
{

    struct Cell_head cellhd_accu, cellhd_dir, cellhd_dtm, cellhd_n;	/* it stores region information,
									   and header information of rasters */
    char *map_accu;		/* input accu map */
    char *map_n;		/* input manning's n map */
    char *map_dtm;		/* input terrain model */
    char *map_dir;		/* input flow direction map */
    char *result;		/* output travel time map */
    char *mapset;		/* mapset name */
    double outx, outy;
    int nrows, ncols;
    int row, col;
    int verbose;
    int cx, cy, x, y;
    double factor;

    struct Cell_head window;

    struct GModule *module;	/* GRASS module for parsing arguments */

    /* options */
    struct Option *input_dir, *input_accu, *input_dtm, *input_n, *output,
	*input_outlet_x, *input_outlet_y, *input_thres, *input_nc, *input_b,
	*input_ep, *input_fdis;




    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */



    /* initialize module */
    module = G_define_module();
    module->description = _("Estimation of travel times/isochrones");

    /* Define the different options as defined in gis.h */
    input_dir = G_define_standard_option(G_OPT_R_INPUT);
    input_dir->key = "dir";
    input_dir->description =
	"Flow direction map (e.g. derived by r.watershed)";

    input_accu = G_define_standard_option(G_OPT_R_INPUT);
    input_accu->key = "accu";
    input_accu->description =
	"Flow accumulation map (e.g. derived by r.watershed)";

    input_dtm = G_define_standard_option(G_OPT_R_INPUT);
    input_dtm->key = "dtm";
    input_dtm->description =
	"Depressionless, filled terrain model (e.g. derived by r.fill.dir)";

    input_n = G_define_standard_option(G_OPT_R_INPUT);
    input_n->key = "manningsn";
    input_n->description = "Map with Manning's n value for surface roughness";

    input_outlet_x = G_define_option();
    input_outlet_x->key = "out_x";
    input_outlet_x->type = TYPE_STRING;
    input_outlet_x->required = YES;
    input_outlet_x->description = "x coordinate of basin outlet";
    input_outlet_x->gisprompt = "old,cell,raster";

    input_outlet_y = G_define_option();
    input_outlet_y->key = "out_y";
    input_outlet_y->type = TYPE_STRING;
    input_outlet_y->required = YES;
    input_outlet_y->description = "y coordinate of basin outlet";
    input_outlet_y->gisprompt = "old,cell,raster";

    input_thres = G_define_option();
    input_thres->key = "threshold";
    input_thres->type = TYPE_STRING;
    input_thres->required = YES;
    input_thres->description =
	"Minimum number of cells (threshold) that classify cell as channel";
    input_thres->gisprompt = "old,cell,raster";

    input_b = G_define_option();
    input_b->key = "b";
    input_b->type = TYPE_STRING;
    input_b->required = YES;
    input_b->description = "Channel width";
    input_b->gisprompt = "old,cell,raster";

    input_nc = G_define_option();
    input_nc->key = "nchannel";
    input_nc->type = TYPE_STRING;
    input_nc->required = YES;
    input_nc->description = "Channel roughness (Manning's n)";
    input_nc->gisprompt = "old,cell,raster";

    input_ep = G_define_option();
    input_ep->key = "ep";
    input_ep->type = TYPE_STRING;
    input_ep->required = YES;
    input_ep->description = "Excess precipitation [mm/h]";
    input_ep->gisprompt = "old,cell,raster";

    input_fdis = G_define_option();
    input_fdis->key = "fdis";
    input_fdis->type = TYPE_STRING;
    input_fdis->required = YES;
    input_fdis->description =
	"Reduction factor for equilibrium discharge, 0.0 < f <= 1.0 (default=1)";
    input_fdis->gisprompt = "old,cell,raster";

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key = "out";
    output->description = "Output travel time map [minutes]";

    /* options and flags pareser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    /* stores options and flags to variables */
    map_accu = input_accu->answer;
    map_dir = input_dir->answer;
    map_dtm = input_dtm->answer;
    map_n = input_n->answer;
    sscanf(input_outlet_x->answer, "%lf", &outx);
    sscanf(input_outlet_y->answer, "%lf", &outy);
    sscanf(input_thres->answer, "%d", &ac_thres);
    sscanf(input_b->answer, "%lf", &b);
    sscanf(input_nc->answer, "%lf", &nc);
    sscanf(input_ep->answer, "%lf", &ep);
    sscanf(input_fdis->answer, "%lf", &factor);

    result = output->answer;

    if (factor > 0 & factor <= 1.0)
	fdis = factor;
    else {
	printf("\nWARNING! Reduction factor is not valid!\n");
	exit(EXIT_FAILURE);
    }

    /* returns NULL if the map was not found in any mapset, 
     * mapset name otherwise */
    mapset = G_find_cell2(map_dir, "");
    if (mapset == NULL)
	G_fatal_error(_("cell file [%s] not found"), map_dir);

    mapset = G_find_cell2(map_accu, "");
    if (mapset == NULL)
	G_fatal_error(_("cell file [%s] not found"), map_accu);

    mapset = G_find_cell2(map_dtm, "");
    if (mapset == NULL)
	G_fatal_error(_("cell file [%s] not found"), map_dtm);

    mapset = G_find_cell2(map_n, "");
    if (mapset == NULL)
	G_fatal_error(_("cell file [%s] not found"), map_n);


    if (G_legal_filename(result) < 0)
	G_fatal_error(_("[%s] is an illegal name"), result);



    /* determine the inputmap type (CELL/FCELL/DCELL) */
    data_type_dir = G_raster_map_type(map_dir, mapset);
    data_type_accu = G_raster_map_type(map_accu, mapset);
    data_type_n = G_raster_map_type(map_n, mapset);
    data_type_dtm = G_raster_map_type(map_dtm, mapset);

    /* G_open_cell_old - returns file destriptor (>0) */
    if ((in_dir = G_open_cell_old(map_dir, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), map_dir);

    if ((in_accu = G_open_cell_old(map_accu, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), map_accu);

    if ((in_n = G_open_cell_old(map_n, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), map_n);

    if ((in_dtm = G_open_cell_old(map_dtm, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), map_dtm);

    /* controlling, if we can open input raster */
    if (G_get_cellhd(map_accu, mapset, &cellhd_accu) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), map_accu);

    if (G_get_cellhd(map_dir, mapset, &cellhd_dir) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), map_dir);

    if (G_get_cellhd(map_dtm, mapset, &cellhd_dtm) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), map_dtm);

    if (G_get_cellhd(map_n, mapset, &cellhd_n) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), map_n);

    G_debug(3, "number of rows %d", cellhd_accu.rows);
    G_debug(3, "number of rows %d", cellhd_dir.rows);
    G_debug(3, "number of rows %d", cellhd_dtm.rows);
    G_debug(3, "number of rows %d", cellhd_n.rows);

    /* Allocate input buffer */
    inrast_accu = G_allocate_raster_buf(data_type_accu);
    inrast_dir = G_allocate_raster_buf(data_type_dir);
    inrast_n = G_allocate_raster_buf(data_type_n);
    inrast_dtm = G_allocate_raster_buf(data_type_dtm);


    /* Allocate output buffer, use input map data_type */
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(FCELL_TYPE);

    /* controlling, if we can write the raster */
    if ((outfd = G_open_raster_new(result, FCELL_TYPE)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);

    /* output array */

    array_out = (double **)malloc(nrows * sizeof(double *));
    if ((NULL == array_out)) {
	printf("out of memory ... !");
	exit(EXIT_FAILURE);
    }
    int i, j;

    for (i = 0; i < nrows; i++) {
	array_out[i] = (double *)malloc(ncols * sizeof(double));
	if ((NULL == array_out[i])) {
	    printf("out of memory ... !");
	    exit(EXIT_FAILURE);
	}
    }

    for (i = 0; i < nrows; i++) {
	for (j = 0; j < ncols; j++) {
	    array_out[i][j] = DBL_MAX;
	}
    }

    /*
     * terrain analysis begins here ...
     */

    if (G_get_window(&window) < 0) {
	sprintf(map_dir, "can't read current window parameters");
	G_fatal_error(map_dir);
	exit(EXIT_FAILURE);
    }

    // map units to matrix locations

    cx = G_scan_easting(*input_outlet_x->answers, &outx, G_projection());
    cy = G_scan_northing(*input_outlet_y->answers, &outy, G_projection());

    if (!cx) {
	array_out[y][x] = 0.0;

	fprintf(stderr, "Illegal east coordinate <%s>\n",
		*input_outlet_y->answer);
	G_usage();
	exit(EXIT_FAILURE);
    }

    if (!cy) {
	fprintf(stderr, "Illegal north coordinate <%s>\n",
		*input_outlet_y->answer);
	G_usage();
	exit(EXIT_FAILURE);
    }



    if (outx < window.west || outx > window.east || outy < window.south ||
	outy > window.north) {
	fprintf(stderr, "Warning, ignoring point outside window: \n");
	fprintf(stderr, "   %.4f,%.4f\n", outx, outy);
    }


    res_x = window.ew_res;
    res_y = window.ns_res;

    cy = (window.north - outy) / res_y;
    cx = (outx - window.west) / res_x;
    if (verbose)
	printf
	    ("\ngrid location of outlet x=%d, y=%d\n(resolution %.0fx%.0f map units, meters expected)\n",
	     cx, cy, res_x, res_y);


    x = cx;
    y = cy;


    /*
     * first call of traveltime function
     */
    array_out[y][x] = 0.0;
    int m = ttime(0, x, y, 0, 0);

    /* output */
    for (row = 0; row < nrows; row++) {
	for (col = 0; col < ncols; col++) {
	    ((CELL *) outrast)[col] = array_out[row][col];
	}
	/* write raster row to output raster file */
	if (G_put_raster_row(outfd, outrast, CELL_TYPE) < 0)
	    G_fatal_error(_("Cannot write to <%s>"), result);
    }




    /* memory cleanup */
    G_free(inrast_accu);
    G_free(inrast_dir);
    G_free(inrast_dtm);
    G_free(inrast_n);
    G_free(outrast);

    /* closing raster files */
    G_close_cell(inrast_accu);
    G_close_cell(inrast_dir);
    G_close_cell(inrast_dtm);
    G_close_cell(inrast_n);
    G_close_cell(outfd);


    return 0;
}
