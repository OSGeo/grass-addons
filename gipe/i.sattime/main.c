/****************************************************************************
 *
 * MODULE:       i.sattime
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the time of satellite overpass
 * 		 using sun elevation angle, latitude and DOY.
 *
 * COPYRIGHT:    (C) 2007-2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
    
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
    
#define PI 3.1415927

int main(int argc, char *argv[]) 
{
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4, *output1;
    struct History history;	/*metadata */

    /************************************/ 
    char *name;			/*input raster name */
    char *result1;		/*output raster name */
    
    /*File Descriptors */ 
    int infd_lat, infd_lon, infd_doy, infd_phi;
    int outfd1;
    char *lat, *lon, *doy, *phi;
    void *inrast_lat, *inrast_lon, *inrast_doy, *inrast_phi;

    DCELL * outrast1;

    /************************************/ 
    G_gisinit(argv[0]);
    module = G_define_module();
    module->keywords = _("satellite time, overpass");
    module->description = _("creates a satellite overpass time map");
    
    /* Define the different options */ 
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("doy");
    input1->description = _("Name of the DOY input map");

    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = _("lat");
    input2->description = _("Name of the latitude input map");

    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = _("long");
    input3->description = _("Name of the longitude input map");

    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = _("sun_elev");
    input4->description = _("Name of the sun elevation angle input map");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description =
	_("Name of the output satellite overpass time layer");

    /********************/ 
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    doy = input1->answer;
    lat = input2->answer;
    lon = input3->answer;
    phi = input4->answer;
    result1 = output1->answer;

    /***************************************************/ 
    if ((infd_doy = G_open_cell_old(doy, "")) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), doy);
    inrast_doy = G_allocate_d_raster_buf();

    /***************************************************/ 
    if ((infd_lat = G_open_cell_old(lat, "")) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), lat);
    inrast_lat = G_allocate_d_raster_buf();
    
    /***************************************************/ 
    if ((infd_lon = G_open_cell_old(lon, "")) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), lon);
    inrast_lon = G_allocate_d_raster_buf();
    
    /***************************************************/ 
    if ((infd_phi = G_open_cell_old(phi, "")) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), phi);
    inrast_phi = G_allocate_d_raster_buf();
    
    /***************************************************/ 
    nrows = G_window_rows();
    ncols = G_window_cols();

    outrast1 = G_allocate_d_raster_buf();
    if ((outfd1 = G_open_raster_new(result1, DCELL_TYPE)) < 0)
	G_fatal_error(_("Could not open <%s>"), result1);

    for (row = 0; row < nrows; row++)
    {
	DCELL d;
	DCELL d_frac_year;
	DCELL d_tc_wa;
	DCELL d_delta;
	DCELL d_Wa;
	DCELL d_Wa1;
	DCELL d_Wa2;
	DCELL d_time;
	DCELL d_lat;
	DCELL d_lon;
	DCELL d_doy;
	DCELL d_phi;
	G_percent(row, nrows, 2);

	if (G_get_raster_row(infd_doy, inrast_doy, row, DCELL_TYPE) < 0)
	    G_fatal_error(_("Could not read from <%s>"), doy);
	if (G_get_raster_row(infd_lat, inrast_lat, row, DCELL_TYPE) < 0)
	    G_fatal_error(_("Could not read from <%s>"), lat);
	if (G_get_raster_row(infd_lon, inrast_lon, row, DCELL_TYPE) < 0)
	    G_fatal_error(_("Could not read from <%s>"), lon);
	if (G_get_raster_row(infd_phi, inrast_phi, row, DCELL_TYPE) < 0)
	    G_fatal_error(_("Could not read from <%s>"), phi);

	for (col = 0; col < ncols; col++)
        {
            d_doy = ((DCELL *) inrast_doy)[col];
            d_lat = ((DCELL *) inrast_lat)[col];
            d_lon = ((DCELL *) inrast_lon)[col];
            d_phi = ((DCELL *) inrast_phi)[col];

	    d_frac_year = (360.0 / 365.25) * d_doy;
	    d_delta =
		0.396372 - 22.91327 * cos(d_frac_year * PI / 180.0) +
		4.02543 * sin(d_frac_year * PI / 180.0) -
		0.387205 * cos(2 * d_frac_year * PI / 180.0) +
		0.051967 * sin(2 * d_frac_year * PI / 180.0) -
		0.154527 * cos(3 * d_frac_year * PI / 180.0) +
		0.084798 * sin(3 * d_frac_year * PI / 180.0);
	    d_tc_wa =
		0.004297 + 0.107029 * cos(d_frac_year * PI / 180.0) -
		1.837877 * sin(d_frac_year * PI / 180.0) -
		0.837378 * cos(2 * d_frac_year * PI / 180.0) -
		2.340475 * sin(2 * d_frac_year * PI / 180.0);
	    d_Wa1 =
		cos((90.0 - d_phi) * PI / 180.0) -
		sin(d_delta * PI / 180.0) * sin(d_lat * PI / 180.0);
	    d_Wa2 = cos(d_delta * PI / 180.0) * cos(d_lat * PI / 180.0);
	    d_Wa = acos(d_Wa1 / d_Wa2);
	    d_time = ((d_Wa - (d_lon * PI / 180.0) - d_tc_wa) / 15.0) + 12.0;
	    outrast1[col] = d_time;
        }
	if (G_put_raster_row(outfd1, outrast1, DCELL_TYPE) < 0)
	    G_fatal_error(_("Cannot write to output raster file"));
    }
    G_free(inrast_lat);
    G_free(inrast_lon);
    G_free(inrast_doy);
    G_free(inrast_phi);
    G_close_cell(infd_lat);
    G_close_cell(infd_lon);
    G_close_cell(infd_doy);
    G_close_cell(infd_phi);
    G_free(outrast1);
    G_close_cell(outfd1);

    G_short_history(result1, "raster", &history);
    G_command_history(&history);
    G_write_history(result1, &history);

    exit(EXIT_SUCCESS);
}


