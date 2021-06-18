
/****************************************************************************
 *
 * MODULE:       i.dn2potrad.l5
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculate ETpot radiative for Landsat5 from DN.
 *
 * COPYRIGHT:    (C) 2007-2008 by the GRASS Development Team
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

#define MAXFILES 7

/*sun exo-atmospheric irradiance */
#define KEXO1 1969.0
#define KEXO2 1840.0
#define KEXO3 1551.0
#define KEXO4 1044.0
#define KEXO5 225.7
#define KEXO6 0.00
#define KEXO7 82.07

#define PI 3.1415926

int l5_in_read(char *metfName, int *path, int *row, double *latitude,
	       double *longitude, double *sun_elevation, double *sun_azimuth,
	       int *c_year, int *c_month, int *c_day, int *day, int *month,
	       int *year, double *decimal_hour);
int date2doy(int day, int month, int year);

double dn2rad_landsat5(int c_year, int c_month, int c_day, int year,
		       int month, int day, int band, int DN);
double rad2ref_landsat5(double radiance, double doy, double sun_elevation,
			double k_exo);
double tempk_landsat5(double l6);

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

    unsigned char *outrast[MAXFILES];

    RASTER_MAP_TYPE in_data_type[MAXFILES];

    RASTER_MAP_TYPE out_data_type = DCELL_TYPE;	/* 0=numbers  1=text */

    double kexo[MAXFILES];

    /*Metfile */
    char *metfName;		/*NLAPS report file, header in text format */

    char b1[80], b2[80], b3[80];

    char b4[80], b5[80];

    char b6[80], b7[80];	/*Load .tif names */

    double sun_elevation;

    double sun_azimuth;		/*not useful here, only for parser() */

    int c_day, c_month, c_year;	/*NLAPS processing date */

    int day, month, year;

    double decimal_hour;

    int l5path, l5row;

    /*EndofMetfile */
    int temp;

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

    double roh_w, tsw;

	/************************************/
    int histogram[100];

    /* Albedo correction coefficients*** */
    double a, b;

	/************************************/

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords =
	_("DN, reflectance, temperature, import, potential evapotranspiration");
    module->description =
	_("Calculates Potential evapotranspiration from Landsat 5 DN.\n");

    /* Define the different options */
    input = G_define_option();
    input->key = _("file");
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = _("old_file,file,file");
    input->description = _("Landsat 5TM NLAPS report File (.txt)");

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

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("ETpot output layer name");

    /* Define the different flags */

    flag1 = G_define_flag();
    flag1->key = _('a');
    flag1->description =
	_("Albedo dry run to calculate some water to beach/sand/desert stretching, a kind of simple atmospheric correction. Will slow down the processing.");

	/********************/
    if (G_parser(argc, argv))
	exit(-1);

    metfName = input->answer;
    result = output->answer;
    tsw = atof(input1->answer);
    roh_w = atof(input2->answer);

    if (tsw >= 1.0 || tsw <= 0.0) {
	G_fatal_error(_("Tsw is out of range, correct it."));
    }
    if (roh_w >= 1100.0 || roh_w <= 900.0) {
	G_fatal_error(_("Something wrong with roh_w value, please check."));
    }

	/********************************************/
    /*Fetch parameters for DN2Rad2Ref correction */
    l5_in_read(metfName, &l5path, &l5row, &latitude, &longitude,
	       &sun_elevation, &sun_azimuth, &c_year, &c_month, &c_day, &day,
	       &month, &year, &decimal_hour);
    /*      printf("%f/%f/%i-%i-%i\n",sun_elevation,sun_azimuth,day,month,year);
       for(i=0;i<MAXFILES;i++){
       printf("%i=>%f, %f, %f, %f\n",i,lmin[i],lmax[i],qcalmin[i],qcalmax[i]);
       }
     */
    doy = date2doy(day, month, year);
    printf("doy=%i\n", doy);

    if (year < 2000) {
	temp = year - 1900;
    }
    else {
	temp = year - 2000;
    }
    if (temp >= 10) {
	sprintf(b1, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B1.tif");
	sprintf(b2, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B2.tif");
	sprintf(b3, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B3.tif");
	sprintf(b4, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B4.tif");
	sprintf(b5, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B5.tif");
	sprintf(b6, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B6.tif");
	sprintf(b7, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "00", temp,
		doy, "50_B7.tif");
    }
    else {
	sprintf(b1, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B1.tif");
	sprintf(b2, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B2.tif");
	sprintf(b3, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B3.tif");
	sprintf(b4, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B4.tif");
	sprintf(b5, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B5.tif");
	sprintf(b6, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B6.tif");
	sprintf(b7, "%s%d%s%d%s%d%d%s", "LT5", l5path, "0", l5row, "000",
		temp, doy, "50_B7.tif");
    }

	/********************/
    /*Prepare sun exo-atm irradiance */

	/********************/

    kexo[0] = KEXO1;
    kexo[1] = KEXO2;
    kexo[2] = KEXO3;
    kexo[3] = KEXO4;
    kexo[4] = KEXO5;
    kexo[5] = KEXO6;		/*filling only */
    kexo[6] = KEXO7;

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
    /*Band6 */
    /* find map in mapset */
    mapset = G_find_cell2(b6, "");
    if (mapset == NULL) {
	G_fatal_error(_("cell file [%s] not found"), b6);
    }
    if (G_legal_filename(b6) < 0) {
	G_fatal_error(_("[%s] is an illegal name"), b6);
    }
    infd[5] = G_open_cell_old(b6, mapset);
    /* Allocate input buffer */
    in_data_type[5] = G_raster_map_type(b6, mapset);
    if ((infd[5] = G_open_cell_old(b6, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b6);
    }
    if ((G_get_cellhd(b6, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b6);
    }
    inrast[5] = G_allocate_raster_buf(in_data_type[5]);

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
    infd[6] = G_open_cell_old(b7, mapset);
    /* Allocate input buffer */
    in_data_type[6] = G_raster_map_type(b7, mapset);
    if ((infd[6] = G_open_cell_old(b7, mapset)) < 0) {
	G_fatal_error(_("Cannot open cell file [%s]"), b7);
    }
    if ((G_get_cellhd(b7, mapset, &cellhd)) < 0) {
	G_fatal_error(_("Cannot read file header of [%s]"), b7);
    }
    inrast[6] = G_allocate_raster_buf(in_data_type[6]);

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
       Shamelessly stolen from r.sun !!!!   
       Set up parameters for projection to lat/long if necessary */
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

    if (flag1->answer) {
	/*START ALBEDO HISTOGRAM STRETCH */
	/*This is correcting contrast for water/sand */
	/*A poor man's atmospheric correction... */
	for (i = 0; i < 100; i++) {
	    histogram[i] = 0;
	}
	for (row = 0; row < nrows; row++) {
	    G_percent(row, nrows, 2);
	    /* read input map */
	    for (i = 0; i < MAXFILES; i++) {
		if ((G_get_raster_row
		     (infd[i], inrast[i], row, in_data_type[i])) < 0) {
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
			dn2rad_landsat5(c_year, c_month, c_day, year, month,
					day, i + 1, d[i]);
		    if (i == 5) {	/*if band 6, process brightness temperature */
			if (dout[i] <= 0.0) {
			    dout[i] = -999.99;
			}
			else {
			    dout[i] = tempk_landsat5(dout[i]);
			}
		    }
		    else {	/*process reflectance */
			dout[i] =
			    rad2ref_landsat5(dout[i], doy, sun_elevation,
					     kexo[i]);
		    }
		}
		/* End of Convert DN 2 radiance 2 reflectance */

		/* Process regular data */
		d_albedo =
		    bb_alb_landsat(dout[0], dout[1], dout[2], dout[3],
				   dout[4], dout[6]);
		if (G_is_d_null_value(&d_albedo)) {
		    /*Do nothing */
		}
		else {
		    int temp;

		    temp = (int)(d_albedo * 100);
		    if (temp > 0) {
			histogram[temp] = histogram[temp] + 1.0;
		    }
		}
	    }
	}
	printf("Histogram of Albedo\n");
	int peak1, peak2, peak3;

	int i_peak1, i_peak2, i_peak3;

	peak1 = 0;
	peak2 = 0;
	peak3 = 0;
	i_peak1 = 0;
	i_peak2 = 0;
	i_peak3 = 0;
	for (i = 0; i < 100; i++) {
	    /*Search for peaks of datasets (1) */
	    if (i <= 10) {
		if (histogram[i] > peak1) {
		    peak1 = histogram[i];
		    i_peak1 = i;
		}
	    }
	    /*Search for peaks of datasets (2) */
	    if (i >= 10 && i <= 30) {
		if (histogram[i] > peak2) {
		    peak2 = histogram[i];
		    i_peak2 = i;
		}
	    }
	    /*Search for peaks of datasets (3) */
	    if (i >= 30) {
		if (histogram[i] > peak3) {
		    peak3 = histogram[i];
		    i_peak3 = i;
		}
	    }
	}
	int bottom1a, bottom1b;

	int bottom2a, bottom2b;

	int bottom3a, bottom3b;

	int i_bottom1a, i_bottom1b;

	int i_bottom2a, i_bottom2b;

	int i_bottom3a, i_bottom3b;

	bottom1a = 100000;
	bottom1b = 100000;
	bottom2a = 100000;
	bottom2b = 100000;
	bottom3a = 100000;
	bottom3b = 100000;
	i_bottom1a = 100;
	i_bottom1b = 100;
	i_bottom2a = 100;
	i_bottom2b = 100;
	i_bottom3a = 100;
	i_bottom3b = 100;
	/* Water histogram lower bound */
	for (i = 0; i < i_peak1; i++) {
	    if (histogram[i] <= bottom1a) {
		bottom1a = histogram[i];
		i_bottom1a = i;
	    }
	}
	/* Water histogram higher bound */
	for (i = i_peak2; i > i_peak1; i--) {
	    if (histogram[i] <= bottom1b) {
		bottom1b = histogram[i];
		i_bottom1b = i;
	    }
	}
	/* Land histogram lower bound */
	for (i = i_peak1; i < i_peak2; i++) {
	    if (histogram[i] <= bottom2a) {
		bottom2a = histogram[i];
		i_bottom2a = i;
	    }
	}
	/* Land histogram higher bound */
	for (i = i_peak3; i > i_peak2; i--) {
	    if (histogram[i] < bottom2b) {
		bottom2b = histogram[i];
		i_bottom2b = i;
	    }
	}
	/* Cloud/Snow histogram lower bound */
	for (i = i_peak2; i < i_peak3; i++) {
	    if (histogram[i] < bottom3a) {
		bottom3a = histogram[i];
		i_bottom3a = i;
	    }
	}
	/* Cloud/Snow histogram higher bound */
	for (i = 100; i > i_peak3; i--) {
	    if (histogram[i] < bottom3b) {
		bottom3b = histogram[i];
		i_bottom3b = i;
	    }
	}
	printf("peak1 %d %d\n", peak1, i_peak1);
	printf("bottom2b= %d %d\n", bottom2b, i_bottom2b);
	a = (0.36 - 0.05) / (i_bottom2b / 100.0 - i_peak1 / 100.0);
	b = 0.05 - a * (i_peak1 / 100.0);
	printf("a= %f\tb= %f\n", a, b);
    }				/*END OF FLAG1 */
    /*START PROCESSING */
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
		    dn2rad_landsat5(c_year, c_month, c_day, year, month, day,
				    i + 1, d[i]);
		if (i == 5) {	/*if band 6, process brightness temperature */
		    if (dout[i] <= 0.0) {
			dout[i] = -999.99;
		    }
		    else {
			dout[i] = tempk_landsat5(dout[i]);
		    }
		}
		else {		/*process reflectance */
		    dout[i] =
			rad2ref_landsat5(dout[i], doy, sun_elevation,
					 kexo[i]);
		}
	    }
	    /* End of Convert DN 2 radiance 2 reflectance */

	    /* Process regular data */
	    d_albedo =
		bb_alb_landsat(dout[0], dout[1], dout[2], dout[3], dout[4],
			       dout[7]);
	    if (flag1->answer) {
		/* Post-Process Albedo */
		d_albedo = a * d_albedo + b;
	    }
	    d_ndvi = nd_vi(d[2], d[3]);
	    d_e0 = emissivity_generic(d_ndvi);
	    d_solar = solar_day(d_lat, (double)doy, tsw);
	    d_rnetd = r_net_day(d_albedo, d_solar, tsw);
	    d_tempk = dout[5];
	    d_etpot = et_pot_day(d_albedo, d_solar, d_tempk, tsw, roh_w);
	    /* End of process regular data */

	    /* write output to file */
	    ((DCELL *) outrast[0])[col] = d_etpot;
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
