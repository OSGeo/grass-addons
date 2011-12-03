
/****************************************************************************
 *
 * MODULE:       i.dn2potrad.l7
 * AUTHOR(S):    Yann Chemin - ychemin@gmail.com
 * PURPOSE:      Calculate ETpot radiative for Landsat7 from DN.
 *
 * COPYRIGHT:    (C) 2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General Public
 *   	    	 License. Read the file COPYING that comes with GRASS for details.
 *
 * THANKS:	 Brad Douglas helped fixing the filename fetching
 *  
 *****************************************************************************/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/gprojects.h>
#include <grass/glocale.h>

#define MAXFILES 9

/*sun exo-atmospheric irradiance */
#define KEXO1 1969.0
#define KEXO2 1840.0
#define KEXO3 1551.0
#define KEXO4 1044.0
#define KEXO5 225.7
#define KEXO7 82.07
#define KEXO8 1385.64		/*to find the real value in the internet */

#define PI 3.1415926


int l7_in_read(char *metfName, char *b1, char *b2, char *b3, char *b4,
	       char *b5, char *b61, char *b62, char *b7, char *b8,
	       double *lmin, double *lmax, double *qcalmin, double *qcalmax,
	       double *sun_elevation, double *sun_azimuth, int *day,
	       int *month, int *year);
int date2doy(int day, int month, int year);

double dn2rad_landsat7(double Lmin, double LMax, double QCalMax,
		       double QCalmin, int DN);
double rad2ref_landsat7(double radiance, double doy, double sun_elevation,
			double k_exo);
double tempk_landsat7(double l6);

double bb_alb_landsat(double bluechan, double greenchan, double redchan,
		      double nirchan, double chan5, double chan7);
double nd_vi(double redchan, double nirchan);

double emissivity_generic(double ndvi);

double solar_day(double lat, double doy, double tsw);

double r_net_day(double bbalb, double solar, double tsw);

double et_pot_day(double bbalb, double solar, double tempk, double tsw,
		  double roh_w);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd;	/*region+header info */

    char *mapset;		/*mapset name */

    int nrows, ncols;

    int row, col;

    struct GModule *module;

    struct Option *input, *input1, *input2, *input3, *output;

    struct Flag *flag1;

    struct History history;	/*metadata */

	/************************************/
    /* FMEO Declarations**************** */
    char history_buf[200];

    char *name;			/*input raster name */

    char *result;		/*output raster name */

    /*File Descriptors */
    int infd[MAXFILES];

    int outfd[MAXFILES];

    char **names;

    char **ptr;

    int i = 0, j = 0;

    void *inrast[MAXFILES];

    DCELL *outrast[MAXFILES];

    RASTER_MAP_TYPE in_data_type[MAXFILES];

    RASTER_MAP_TYPE out_data_type = DCELL_TYPE;	/* 0=numbers  1=text */

    double kexo[MAXFILES];

    /*Metfile */
    char *metfName;		/*met file, header in text format */

    char b1[80], b2[80], b3[80];

    char b4[80], b5[80], b61[80];

    char b62[80], b7[80], b8[80];	/*Load .tif names */

    double lmin[MAXFILES];

    double lmax[MAXFILES];

    double qcalmin[MAXFILES];

    double qcalmax[MAXFILES];

    double sun_elevation;

    double sun_azimuth;		/*not useful here, only for parser() */

    int day, month, year;

    /*EndofMetfile */
    int doy;

    int not_ll = 0;		/*if proj is not lat/long, it will be 1. */

    struct pj_info iproj;

    struct pj_info oproj;

    /*      char            *lat; */
    double xp, yp;

    double xmin, ymin;

    double xmax, ymax;

    double stepx, stepy;

    double latitude, longitude;

    int chosen_tempk_band;

    double roh_w, tsw;

	/************************************/

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords =
	_("DN, reflectance, temperature, import, potential evapotranspiration");
    module->description =
	_("Calculates Potential evapotranspiration from Landsat 7 DN.\n");

    /* Define the different options */
    input = G_define_option();
    input->key = _("metfile");
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = _("old_file,file,file");
    input->description = _("Landsat 7ETM+ Header File (.met)");

    input1 = G_define_option();
    input1->key = _("tsw");
    input1->type = TYPE_DOUBLE;
    input1->required = YES;
    input1->gisprompt = _("value, parameter");
    input1->description =
	_("Single-way transmissivity of the atmosphere [0.0-1.0]");
    input1->answer = "0.7";

    input2 = G_define_option();
    input2->key = _("roh_w");
    input2->type = TYPE_DOUBLE;
    input2->required = YES;
    input2->gisprompt = _("value, parameter");
    input2->description = _("Density of water (~1000 g/m3)");
    input2->answer = "1010.0";

    input3 = G_define_option();
    input3->key = _("tempk_band");
    input3->type = TYPE_INTEGER;
    input3->required = YES;
    input3->gisprompt = _("value, parameter");
    input3->description = _("5=band61 || 6=band62");
    input3->answer = "5";

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("ETpot output layer name");

	/********************/
    if (G_parser(argc, argv))
	exit(-1);

    metfName = input->answer;
    result = output->answer;
    tsw = atof(input1->answer);
    roh_w = atof(input2->answer);
    chosen_tempk_band = atoi(input3->answer);

    if (tsw >= 1.0 || tsw <= 0.0) {
	G_fatal_error(_("Tsw is out of range, correct it."));
    }
    if (roh_w >= 1100.0 || roh_w <= 900.0) {
	G_fatal_error(_("Something wrong with roh_w value, please check."));
    }
    if (chosen_tempk_band != 5 && chosen_tempk_band != 6) {
	G_fatal_error(_("Tempk band is not good, change to 5 OR 6!"));
    }

	/******************************************/
    /*Fetch parameters for DN2Rad2Ref correction */
    l7_in_read(metfName, b1, b2, b3, b4, b5, b61, b62, b7, b8, lmin, lmax,
	       qcalmin, qcalmax, &sun_elevation, &sun_azimuth, &day, &month,
	       &year);
    doy = date2doy(day, month, year);
    /*      printf("%f/%f/%i-%i-%i\n",sun_elevation,sun_azimuth,day,month,year);
       for(i=0;i<MAXFILES;i++){
       printf("%i=>%f, %f, %f, %f\n",i,lmin[i],lmax[i],qcalmin[i],qcalmax[i]);
       }
       printf("b1=%s\n",b1);
       printf("b2=%s\n",b2);
       printf("b3=%s\n",b3);
       printf("b4=%s\n",b4);
       printf("b5=%s\n",b5);
       printf("b61=%s\n",b61);
       printf("b62=%s\n",b62);
       printf("b7=%s\n",b7);
       printf("b8=%s\n",b8);
       printf("doy=%i\n",doy);
     */

	/********************/
    /*Prepare sun exo-atm irradiance */

	/********************/

    kexo[0] = KEXO1;
    kexo[1] = KEXO2;
    kexo[2] = KEXO3;
    kexo[3] = KEXO4;
    kexo[4] = KEXO5;
    kexo[5] = 0.0;		/*filling */
    kexo[6] = 0.0;		/*filling */
    kexo[7] = KEXO7;
    kexo[8] = KEXO8;

	/***************************************************/
    /*Band1 */
    /* find map in mapset */
    mapset = G_find_cell2(b1, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b1);
    }
    if (G_legal_filename(b1) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b1);
    }
    infd[0] = G_open_cell_old(b1, mapset);
    /* Allocate input buffer */
    in_data_type[0] = G_raster_map_type(b1, mapset);
    if ((infd[0] = G_open_cell_old(b1, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b1);
    }
    if ((G_get_cellhd(b1, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b1);
    }
    inrast[0] = G_allocate_raster_buf(in_data_type[0]);

	/***************************************************/

	/***************************************************/
    /*Band2 */
    /* find map in mapset */
    mapset = G_find_cell2(b2, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b2);
    }
    if (G_legal_filename(b2) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b2);
    }
    infd[1] = G_open_cell_old(b2, mapset);
    /* Allocate input buffer */
    in_data_type[1] = G_raster_map_type(b2, mapset);
    if ((infd[1] = G_open_cell_old(b2, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b2);
    }
    if ((G_get_cellhd(b2, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b2);
    }
    inrast[1] = G_allocate_raster_buf(in_data_type[1]);

	/***************************************************/

	/***************************************************/
    /*Band3 */
    /* find map in mapset */
    mapset = G_find_cell2(b3, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b3);
    }
    if (G_legal_filename(b3) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b3);
    }
    infd[2] = G_open_cell_old(b3, mapset);
    /* Allocate input buffer */
    in_data_type[2] = G_raster_map_type(b3, mapset);
    if ((infd[2] = G_open_cell_old(b3, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b3);
    }
    if ((G_get_cellhd(b3, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b3);
    }
    inrast[2] = G_allocate_raster_buf(in_data_type[2]);

	/***************************************************/

	/***************************************************/
    /*Band4 */
    /* find map in mapset */
    mapset = G_find_cell2(b4, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b4);
    }
    if (G_legal_filename(b4) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b4);
    }
    infd[3] = G_open_cell_old(b4, mapset);
    /* Allocate input buffer */
    in_data_type[3] = G_raster_map_type(b4, mapset);
    if ((infd[3] = G_open_cell_old(b4, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b4);
    }
    if ((G_get_cellhd(b4, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b4);
    }
    inrast[3] = G_allocate_raster_buf(in_data_type[3]);

	/***************************************************/

	/***************************************************/
    /*Band5 */
    /* find map in mapset */
    mapset = G_find_cell2(b5, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b5);
    }
    if (G_legal_filename(b5) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b5);
    }
    infd[4] = G_open_cell_old(b5, mapset);
    /* Allocate input buffer */
    in_data_type[4] = G_raster_map_type(b5, mapset);
    if ((infd[4] = G_open_cell_old(b5, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b5);
    }
    if ((G_get_cellhd(b5, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b5);
    }
    inrast[4] = G_allocate_raster_buf(in_data_type[4]);

	/***************************************************/

	/***************************************************/
    /*Band61 */
    /* find map in mapset */
    mapset = G_find_cell2(b61, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b61);
    }
    if (G_legal_filename(b61) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b61);
    }
    infd[5] = G_open_cell_old(b61, mapset);
    /* Allocate input buffer */
    in_data_type[5] = G_raster_map_type(b61, mapset);
    if ((infd[5] = G_open_cell_old(b61, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b61);
    }
    if ((G_get_cellhd(b61, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b61);
    }
    inrast[5] = G_allocate_raster_buf(in_data_type[5]);

	/***************************************************/

	/***************************************************/
    /*Band62 */
    /* find map in mapset */
    mapset = G_find_cell2(b62, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b62);
    }
    if (G_legal_filename(b62) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b62);
    }
    infd[6] = G_open_cell_old(b62, mapset);
    /* Allocate input buffer */
    in_data_type[6] = G_raster_map_type(b62, mapset);
    if ((infd[6] = G_open_cell_old(b62, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b62);
    }
    if ((G_get_cellhd(b62, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b62);
    }
    inrast[6] = G_allocate_raster_buf(in_data_type[6]);

	/***************************************************/

	/***************************************************/
    /*Band7 */
    /* find map in mapset */
    mapset = G_find_cell2(b7, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b7);
    }
    if (G_legal_filename(b7) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b7);
    }
    infd[7] = G_open_cell_old(b7, mapset);
    /* Allocate input buffer */
    in_data_type[7] = G_raster_map_type(b7, mapset);
    if ((infd[7] = G_open_cell_old(b7, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b7);
    }
    if ((G_get_cellhd(b7, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b7);
    }
    inrast[7] = G_allocate_raster_buf(in_data_type[7]);

	/***************************************************/

	/***************************************************/
    /*Band8 */
    /* find map in mapset */
    mapset = G_find_cell2(b8, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b8);
    }
    if (G_legal_filename(b8) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b8);
    }
    infd[8] = G_open_cell_old(b8, mapset);
    /* Allocate input buffer */
    in_data_type[8] = G_raster_map_type(b8, mapset);
    if ((infd[8] = G_open_cell_old(b8, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b8);
    }
    if ((G_get_cellhd(b8, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b8);
    }
    inrast[8] = G_allocate_raster_buf(in_data_type[8]);

	/***************************************************/

	/***************************************************/
    /* Allocate output buffer, use input map data_type */
    stepx = cellhd.ew_res;
    stepy = cellhd.ns_res;
    xmin = cellhd.west;
    xmax = cellhd.east;
    ymin = cellhd.south;
    ymax = cellhd.north;

    nrows = G_window_rows();
    ncols = G_window_cols();

    /* Following is for latitude conversion from UTM to Geo
     * Shamelessly stolen from r.sun !!!!   
     * Set up parameters for projection to lat/long if necessary */
    if ((G_projection() != PROJECTION_LL)) {
	not_ll = 1;
	struct Key_Value *in_proj_info, *in_unit_info;

	if ((in_proj_info = G_get_projinfo()) == NULL)
	    G_fatal_error(_("Can't get projection info of current location"));
	if ((in_unit_info = G_get_projunits()) == NULL)
	    G_fatal_error(_("Can't get projection units of current location"));
	if (pj_get_kv(&iproj, in_proj_info, in_unit_info) < 0)
	    G_fatal_error(_("Can't get projection key values of current location"));
	G_free_key_value(in_proj_info);
	G_free_key_value(in_unit_info);
	/* Set output projection to latlong w/ same ellipsoid */
	oproj.zone = 0;
	oproj.meters = 1.;
	sprintf(oproj.proj, "ll");
	if ((oproj.pj = pj_latlong_from_proj(iproj.pj)) == NULL)
	    G_fatal_error(_("Unable to set up lat/long projection parameters"));
    }				/*End of stolen from r.sun */

    out_data_type = DCELL_TYPE;
    outrast[0] = G_allocate_raster_buf(out_data_type);
    if ((outfd[0] = G_open_raster_new(result, 1)) < 0)
	G_fatal_error(_("Could not open <%s>"), result);

    /* Process pixels */
    DCELL dout[MAXFILES];

    DCELL d[MAXFILES];

    DCELL d_albedo;

    DCELL d_tempk;

    DCELL d_ndvi;

    DCELL d_e0;

    DCELL d_lat;

    /*      DCELL d_doy; */
    DCELL d_tsw;

    /*      DCELL d_roh_w; */
    DCELL d_solar;

    DCELL d_rnetd;

    DCELL d_etpot;

    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	/* read input map */
	for (i = 0; i < MAXFILES; i++) {
	    if ((G_get_raster_row(infd[i], inrast[i], row, in_data_type[i])) <
		0) {
		G_fatal_error(_("Could not read from <%s>"), i);
	    }
	}
	/*process the data */
	for (col = 0; col < ncols; col++) {
	    /*Calculate Latitude */
	    latitude = ymax - (row * stepy);
	    longitude = xmin + (col * stepx);
	    if (not_ll) {
		if (pj_do_proj(&longitude, &latitude, &iproj, &oproj) < 0) {
		    G_fatal_error(_("Error in pj_do_proj"));
		}
	    }
	    else {
		/*Do nothing */
	    }
	    d_lat = latitude;
	    /*End of Calculate Latitude */

	    /* Convert DN 2 radiance 2 reflectance */
	    for (i = 0; i < MAXFILES; i++) {
		d[i] = (double)((CELL *) inrast[i])[col];
		dout[i] =
		    dn2rad_landsat7(lmin[i], lmax[i], qcalmax[i], qcalmin[i],
				    d[i]);
		if (i == 5 || i == 6) {	/*if band 61/62, process brightness temperature */
		    if (dout[i] <= 0.0) {
			dout[i] = -999.99;
		    }
		    else {
			dout[i] = tempk_landsat7(dout[i]);
		    }
		}
		else {		/*process reflectance */
		    dout[i] =
			rad2ref_landsat7(dout[i], doy, sun_elevation,
					 kexo[i]);
		}
	    }
	    /* End of Convert DN 2 radiance 2 reflectance */

	    /* Process regular data */
	    d_albedo =
		bb_alb_landsat(dout[0], dout[1], dout[2], dout[3], dout[4],
			       dout[7]);
	    d_ndvi = nd_vi(d[2], d[3]);
	    d_e0 = emissivity_generic(d_ndvi);
	    d_solar = solar_day(d_lat, (double)doy, tsw);
	    d_rnetd = r_net_day(d_albedo, d_solar, tsw);
	    d_tempk = dout[chosen_tempk_band];
	    d_etpot = et_pot_day(d_albedo, d_solar, d_tempk, tsw, roh_w);
	    /* End of process regular data */

	    /* write output to file */
	    outrast[0][col] = d_etpot;
	    /* End of write output to file */
	}
	if (G_put_raster_row(outfd[0], outrast[0], out_data_type) < 0)
	    G_fatal_error(_("Cannot write to <%s.%i>"), result, 0 + 1);
    }
    G_free(inrast[0]);
    G_close_cell(infd[0]);
    G_free(outrast[0]);
    G_close_cell(outfd[0]);

    G_command_history(&history);
    G_write_history(result, &history);

    return 0;
}
