/* main.c for r.traveltime, December 2007, updated September 2014
 *
 * ############################################################################
 * #
 * # MODULE:       r.traveltime
 * #
 * # AUTHOR(S):    Kristian Foerster
 * #
 * # PURPOSE:      This program calculates traveltimes from a digital
 * #               terrain model, a roughness grid and some output
 * #               files from r.watershed. This tool is designed to
 * #               estimate a unit hydrograph for precipitation-runoff
 * #               prediction.
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
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/config.h>

/*
 * global declarations
 */
extern CELL f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

double res_x, res_y;
void *inrast_accu, *inrast_dtm, *inrast_n, *inrast_dir; /* input buffer */
unsigned char *outrast;                                 /* output buffer */
int in_accu, in_dir, in_n, in_dtm, outfd;               /* file descriptor */
RASTER_MAP_TYPE data_type_accu, data_type_dtm, data_type_n,
    data_type_dir; /* type of the map (CELL/DCELL/...) */
double **array_out;
int ac_thres;
double nc, b, dis, slope_min;

/*
 * the function inflow checks if an adjacent cell discharges into the active
 * cell
 */

int inflow(int loc_x, int loc_y, int vec_x, int vec_y)
{

    int x_exp, y_exp;
    int value;

    Rast_get_row(in_dir, inrast_dir, loc_y, data_type_dir);
    value = ((CELL *)inrast_dir)[loc_x];

    // conversions of the flow direction classification to vectors
    // Note: the flow directions categories have been changed to "agnps" format!
    switch (value) {
    case 1:
        x_exp = 0;
        y_exp = -1;
        break;
    case 2:
        x_exp = 1;
        y_exp = -1;
        break;
    case 3:
        x_exp = 1;
        y_exp = 0;
        break;
    case 4:
        x_exp = 1;
        y_exp = 1;
        break;
    case 5:
        x_exp = 0;
        y_exp = 1;
        break;
    case 6:
        x_exp = -1;
        y_exp = 1;
        break;
    case 7:
        x_exp = -1;
        y_exp = 0;
        break;
    case 8:
        x_exp = -1;
        y_exp = -1;
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
 * traveltime calculates travel times from one cell to another (time of
 * concentration)
 */

double traveltime(double length, double slope, double manning, double drainage)
{
    // double slope_min = 0.001;
    double t;
    double Q;

    if (slope < slope_min)
        slope = slope_min;

    /* for areas with drainage accumulation < threshold surface runoff will be
     * calculated, for areas with larger drainage accumulation the channel
     * formula is used instead
     */
    if (drainage < ac_thres) {
        /* overland flow according to
         * Woolhiser and Liggettis (1967)
         * Muzik (1996)
         * Melesse and Graham (2004)
         * please note: this formula expects effective rain / surface runoff
         * input in m/s
         */
        t = pow(length, 0.6) * pow(manning, 0.6) / pow(dis, 0.4) /
            pow(slope, 0.3); // surface runoff
    }
    else {
        // channel runoff
        // specific discharge l/s/km^2
        Q = dis * drainage * res_x * res_y; // equilibrium runoff, ! changed !
        t = length / pow(sqrt(slope) / nc * pow(Q / b, (2.0 / 3.0)), 0.6);
    }
    return t;
}

/*
 * ttime is a recursive function starting at the outlet moving up to the
 * watershed boundary calling the inflow and traveltime functions
 */

int ttime(double ftime, int x, int y, int dx, int dy)
{
    double thist = 0;
    double L, J;
    int i, j, v, accu, dir;
    double z1, z2;
    double manningsn;

    // get flow direction
    Rast_get_row(in_dir, inrast_dir, y, data_type_dir);
    dir = ((CELL *)inrast_dir)[x];

    // get flow accumulation
    Rast_get_row(in_accu, inrast_accu, y, data_type_accu);
    /* $kf 2014-09-25: check input of accumulation map...
     * Older versions of r.watershed generate CELL type
     * maps whereas the newer versions write FCELL maps.
     */
    switch (data_type_accu) {
    case CELL_TYPE:
        accu = ((CELL *)inrast_accu)[x];
        break;
    case DCELL_TYPE:
        accu = (int)((DCELL *)inrast_accu)[x];
        break;
    case FCELL_TYPE:
        accu = (int)((FCELL *)inrast_accu)[x];
        break;
    }

    // get roughness
    Rast_get_row(in_n, inrast_n, y, data_type_n);
    switch (data_type_n) {
    case DCELL_TYPE:
        manningsn = (double)((DCELL *)inrast_n)[x];
        break;
    case FCELL_TYPE:
        manningsn = (double)((FCELL *)inrast_n)[x];
        break;
    }

    // get elevation 2
    Rast_get_row(in_dtm, inrast_dtm, y, data_type_dtm);
    switch (data_type_dtm) {
    case CELL_TYPE:
        z2 = (double)((CELL *)inrast_dtm)[x];
        break;
    case DCELL_TYPE:
        z2 = (double)((DCELL *)inrast_dtm)[x];
        break;
    case FCELL_TYPE:
        z2 = (double)((FCELL *)inrast_dtm)[x];
        break;
    }

    // get elevation 1
    Rast_get_row(in_dtm, inrast_dtm, y - dy, data_type_dtm);
    switch (data_type_dtm) {
    case CELL_TYPE:
        z1 = (double)((CELL *)inrast_dtm)[x - dx];
        break;
    case DCELL_TYPE:
        z1 = (double)((DCELL *)inrast_dtm)[x - dx];
        break;
    case FCELL_TYPE:
        z1 = (double)((FCELL *)inrast_dtm)[x - dx];
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
 * main function of r.traveltime
 */

int main(int argc, char *argv[])
{

    struct Cell_head cellhd_accu, cellhd_dir, cellhd_dtm,
        cellhd_n;   /* it stores region information,
                       and header information of rasters */
    char *map_accu; /* input accu map */
    char *map_n;    /* input manning's n map */
    char *map_dtm;  /* input terrain model */
    char *map_dir;  /* input flow direction map */
    char *result;   /* output travel time map */
    char *mapset;   /* mapset name */
    double outx, outy;
    int nrows, ncols;
    int row, col;
    int verbose;
    int cx, cy, x, y;
    double discharge;

    struct Cell_head window;

    struct GModule *module; /* GRASS module for parsing arguments */

    /* options */
    struct Option *input_dir, *input_accu, *input_dtm, *input_n, *output,
        *input_outlet_x, *input_outlet_y, *input_thres, *input_nc, *input_b,
        *input_dis, *input_slmin;

    struct Flag *flag1; /* flags */

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    module->label = _("Estimation of travel times/isochrones.");
    module->description =
        _("Computes the travel time of surface runoff to an outlet");

    /* Define the different options as defined in gis.h */
    input_dir = G_define_standard_option(G_OPT_R_INPUT);
    input_dir->key = "dir";
    input_dir->description = "Flow direction map (e.g. derived by r.watershed)";

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

    input_dis = G_define_option();
    input_dis->key = "dis";
    input_dis->type = TYPE_STRING;
    input_dis->required = YES;
    input_dis->description = "Specific discharge [l/s/km**2]";
    input_dis->gisprompt = "old,cell,raster";

    input_slmin = G_define_option();
    input_slmin->key = "slopemin";
    input_slmin->type = TYPE_STRING;
    input_slmin->required = NO;
    input_slmin->description = "Minimum slope for flat areas [m/m]";
    input_slmin->gisprompt = "old,cell,raster";

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key = "out";
    output->description = "Output travel time map [seconds]";

    /* Define the different flags */
    flag1 = G_define_flag();
    flag1->key = 'q';
    flag1->description = _("Quiet");

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
    sscanf(input_dis->answer, "%lf", &discharge);
    result = output->answer;

    // options
    if (input_slmin->answer == NULL)
        slope_min = 0.001;
    else
        sscanf(input_slmin->answer, "%lf", &slope_min);

    verbose = (!flag1->answer);

    dis = discharge * 1.0E-9; // l/s/km^2 => m/s

    /* determine the inputmap type (CELL/FCELL/DCELL) */
    mapset = G_find_raster2(map_dir, "");
    data_type_dir = Rast_map_type(map_dir, mapset);
    in_dir = Rast_open_old(map_dir, mapset);

    mapset = G_find_raster2(map_accu, "");
    data_type_accu = Rast_map_type(map_accu, mapset);
    in_accu = Rast_open_old(map_accu, mapset);

    mapset = G_find_raster2(map_n, "");
    data_type_n = Rast_map_type(map_n, mapset);
    in_n = Rast_open_old(map_n, mapset);

    mapset = G_find_raster2(map_dtm, "");
    data_type_dtm = Rast_map_type(map_dtm, mapset);
    in_dtm = Rast_open_old(map_dtm, mapset);

    G_debug(3, "number of rows %d", cellhd_accu.rows);
    G_debug(3, "number of rows %d", cellhd_dir.rows);
    G_debug(3, "number of rows %d", cellhd_dtm.rows);
    G_debug(3, "number of rows %d", cellhd_n.rows);

    /* Allocate input buffer */
    inrast_accu = Rast_allocate_buf(data_type_accu);
    inrast_dir = Rast_allocate_buf(data_type_dir);
    inrast_n = Rast_allocate_buf(data_type_n);
    inrast_dtm = Rast_allocate_buf(data_type_dtm);

    /* Allocate output buffer, use input map data_type */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_buf(FCELL_TYPE);

    /* controlling, if we can write the raster */
    outfd = Rast_open_new(result, FCELL_TYPE);

    /* output array */
    array_out = (double **)malloc(nrows * sizeof(double *));
    if ((NULL == array_out))
        G_fatal_error("Out of memory ... !");

    int i, j;
    for (i = 0; i < nrows; i++) {
        array_out[i] = (double *)malloc(ncols * sizeof(double));
        if ((NULL == array_out[i]))
            G_fatal_error("Out of memory ... !");
    }

    for (i = 0; i < nrows; i++) {
        for (j = 0; j < ncols; j++) {
            array_out[i][j] = DBL_MAX;
        }
    }

    /*
     * terrain analysis begins here ...
     */

    G_get_window(&window);

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
    if (verbose) {
        printf("\ngrid location of outlet x=%d, y=%d\n(resolution %.0fx%.0f "
               "map units, meters expected)\n",
               cx, cy, res_x, res_y);
        printf("minimum slope=%7.5f\n", slope_min);
        printf("surface runoff: %f l/s/km**2 = %e m/s = %f mm/h\n", discharge,
               dis, (discharge * 1E-6 * 3600));
    }

    x = cx;
    y = cy;

    /*
     * first call of traveltime function
     */
    array_out[y][x] = 0.0;
    int m = ttime(0.0, x, y, 0, 0);

    /* output */
    for (row = 0; row < nrows; row++) {
        for (col = 0; col < ncols; col++) {
            ((CELL *)outrast)[col] = array_out[row][col];
        }
        /* write raster row to output raster file */
        Rast_put_row(outfd, outrast, CELL_TYPE);
    }

    /* closing raster files */
    //    Rast_close(inrast_accu);
    //    Rast_close(inrast_dir);
    //    Rast_close(inrast_dtm);
    //    Rast_close(inrast_n);

    Rast_close(in_dir);
    Rast_close(in_accu);
    Rast_close(in_n);
    Rast_close(in_dtm);
    Rast_close(outfd);

    return 0;
}
