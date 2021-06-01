
/****************************************************************************************************************
			r.clim
			
 *   Copyright (C) 2002-2006 by the GRASS Development Team
 *   Author(s): Chiara Sboarina, Centro di Ecologia Alpina - Viote del Monte Bondone (TN) - Italy (2001)
 *
 *
 *      This program is free software under the GNU General Public
 *      License (>=v2). Read the file COPYING that comes with GRASS
 *      for details.

This raster module creates two raster map layers:
1. solar radiation
2. percentage relative humidity

The calculation of the two values for each raster cell is based on the C code cclimm.c a simplified version of
mtclim43.c by Peter Thornton (2000) of the NTSG, School of Forestry University of Montana. 
The cclimm.c code is thought for monthly data and doesn't consider arid correction so this module isn't indicated
for arid region.

The input units are:
Temperatures           degrees C
Precipitation          mm / day
Elevation              m
Slope		       degrees
Aspect		       degrees 
Latitude               decimal degrees
E/W horizons           decimal degrees

while the output units are:
Relative humidity	%
Radiation              W/m2, average over daylight period

'r.clim' can be run in two standard GRASS modes: interactive and command line.
For an interactive run, type in r.clim and follows the prompt.
For a command line mode type in 

	r.clim tmin=name tmax=name prcp=name elev=name slope=name aspect=name lat=name ehoriz=name
	whoriz=name month=number rad=name hum=name
	
****************************************************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>


/* optical airmass by degrees */
float optam[21] =
    { 2.90, 3.05, 3.21, 3.39, 3.69, 3.82, 4.07, 4.37, 4.72, 5.12, 5.60, 6.18,
    6.88, 7.77, 8.90, 10.39, 12.44, 15.36, 19.79, 26.96, 30.00
};

/* julian day for each month */
float julian[12] =
    { 15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349 };

struct Cell_head window;

int main(int argc, char *argv[])
{
    /* physical constants and model parameters
     * (dim) stands for dimensionless values   */

#define SECPERRAD 13750.9871	/* seconds per radian of hour angle */
#define RADPERDAY 0.017214	/* radians of Earth orbit per julian day */
#define RADPERDEG 0.01745329	/* radians per degree */
#define MINDECL -0.4092797	/* minimum declination (radians) */
#define DAYSOFF 11.25		/* julian day offset of winter solstice */
#define SRADDT 600.0		/* timestep for radiation routine (seconds) */
#define MA       28.9644e-3	/* (kg mol-1) molecular weight of air */
#define MW       18.0148e-3	/* (kg mol-1) molecular weight of water */
#define R        8.3143		/* (m3 Pa mol-1 K-1) gas law constant */
#define G_STD    9.80665	/* (m s-2) standard gravitational accel. */
#define P_STD    101325.0	/* (Pa) standard pressure at 0.0 m elevation */
#define T_STD    288.15		/* (K) standard temp at 0.0 m elevation  */
#define CP       1010.0		/* (J kg-1 K-1) specific heat of air */
#define LR_STD   0.0065		/* (-K m-1) standard temperature lapse rate */
#define EPS      0.62196351	/* (MW/MA) unitless ratio of molec weights */
#define PI       3.14159265	/* pi */
    /* parameters for the Tair algorithm */
#define TDAYCOEF     0.45	/* (dim) daylight air temperature coefficient (dim) */
    /* parameters for the snowpack algorithm */
#define SNOW_TCRIT   -6.0	/* (deg C) critical temperature for snowmelt */
#define SNOW_TRATE  0.042	/* (cm/degC/day) snowmelt rate */
    /* parameters for the radiation algorithm */
#define TBASE       0.851904	/* (dim) max inst. trans., 0m, nadir, dry atm */
#define ABASE     -5.79e-5	/* (1/Pa) vapor pressure effect on transmittance */
#define C             1.548	/* (dim) radiation parameter */
#define B0          0.0130104	/* (dim) radiation parameter */
#define B1          0.20224	/* (dim) radiation parameter */
#define B2          0.185896	/* (dim) radiation parameter */
#define RAIN_SCALAR  0.75	/* (dim) correction to trans. for rain day */
#define DIF_ALB       0.6	/* (dim) diffuse albedo for horizon correction */
#define SC_INT       1.32	/* (MJ/m2/day) snow correction intercept */
#define SC_SLOPE    0.096	/* (MJ/m2/day/cm) snow correction slope */

    /* variables */

    int nrows, ncols;
    int nmonth, ami;

    double newsnow, snowmelt, snowpack =
	0.0, swe, t1, t2, pratio, trans1, lati, pend, esp, coszeh, coszwh, dt,
	dh, decl;
    double bsg1, bsg2, bsg3, cosegeom, sinegeom, coshss, hss, daylen, sc,
	dir_beam_topa, sum_trans, sum_flat_potrad, sum_slope_potrad;
    double h, cza, cbsa, dir_flat_topa, am, trans2, ttmax0, flat_potrad,
	slope_potrad, avg_horizon, horizon_scalar, slope_excess;
    double slope_scalar, sky_prop, b, t_fmax, pva, tday, pvs, t_tmax, t_final,
	pdif, pdir, srad1, srad2, tdew;

    /*other local variables */
    int col, row, verbose, tmin_fd, tmax_fd, prcp_fd, elev_fd, slope_fd,
	aspect_fd, lat_fd, ehoriz_fd, whoriz_fd, rad_fd, hum_fd;

    FCELL *tmin,		/*fcell buffer for minimum temperature map layer */
     *tmax,			/*fcell buffer for maximum temperature map layer */
     *prcp,			/*fcell buffer for precipitation map layer */
     *lat;			/*fcell buffer for latitudine map layer */
    CELL *elev,			/*cell buffer for elevation map layer */
     *slope,			/*cell buffer for slope map layer */
     *aspect,			/*cell buffer for aspect map layer */
     *ehoriz,			/*cell buffer for east horizon map layer */
     *whoriz,			/*cell buffer for west horizon map layer */
     *rad,			/*cell buffer for solar radiation map layer */
     *hum;			/*cell buffer for relative humidity map layer */

    extern struct Cell_head window;

    struct
    {
	struct Option *tmin, *tmax, *prcp, *elev, *slope,
	    *aspect, *lat, *ehoriz, *whoriz, *month, *rad, *hum;
    } parm;

    struct Flag *flag1;
    struct GModule *module;

    /* initialize access to database and create temporary files */
    G_gisinit(argv[0]);

    /* Set description */
    module = G_define_module();
    module->description =
	_("Creates two raster map layers: 1. solar radiation  2. percentage relative humidity");

    parm.tmin = G_define_option();
    parm.tmin->key = "tmin";
    parm.tmin->key_desc = "name";
    parm.tmin->type = TYPE_STRING;
    parm.tmin->required = YES;
    parm.tmin->gisprompt = "old,cell,raster";
    parm.tmin->description =
	_("Name of input raster map containing MINIMUM TEMPERATURE");

    parm.tmax = G_define_option();
    parm.tmax->key = "tmax";
    parm.tmax->key_desc = "name";
    parm.tmax->type = TYPE_STRING;
    parm.tmax->required = YES;
    parm.tmax->gisprompt = "old,cell,raster";
    parm.tmax->description =
	_("Name of input raster map containing MAXIMUM TEMPERATURE");

    parm.prcp = G_define_option();
    parm.prcp->key = "prcp";
    parm.prcp->key_desc = "name";
    parm.prcp->type = TYPE_STRING;
    parm.prcp->required = YES;
    parm.prcp->gisprompt = "old,cell,raster";
    parm.prcp->description =
	_("Name of input raster map containing PRECIPITATION in mm");

    parm.elev = G_define_option();
    parm.elev->key = "elev";
    parm.elev->key_desc = "name";
    parm.elev->type = TYPE_STRING;
    parm.elev->gisprompt = "old,cell,raster";
    parm.elev->description =
	_("Name of input raster map containing ELEVATION (m)");

    parm.slope = G_define_option();
    parm.slope->key = "slope";
    parm.slope->key_desc = "name";
    parm.slope->type = TYPE_STRING;
    parm.slope->gisprompt = "old,cell,raster";
    parm.slope->description =
	_("Name of input raster map containing SLOPE (degree)");

    parm.aspect = G_define_option();
    parm.aspect->key = "aspect";
    parm.aspect->key_desc = "name";
    parm.aspect->type = TYPE_STRING;
    parm.aspect->gisprompt = "old,cell,raster";
    parm.aspect->description =
	_("Name of input raster map containing ASPECT (degree, anti-clockwise from E)");

    parm.lat = G_define_option();
    parm.lat->key = "lat";
    parm.lat->key_desc = "name";
    parm.lat->type = TYPE_STRING;
    parm.lat->required = YES;
    parm.lat->gisprompt = "old,cell,raster";
    parm.lat->description =
	_("Name of input raster map containing LATITUDE in decimal degrees");

    parm.ehoriz = G_define_option();
    parm.ehoriz->key = "ehoriz";
    parm.ehoriz->key_desc = "name";
    parm.ehoriz->type = TYPE_STRING;
    parm.ehoriz->gisprompt = "old,cell,raster";
    parm.ehoriz->description =
	_("Name of input raster map containing EAST HORIZON (degree)");

    parm.whoriz = G_define_option();
    parm.whoriz->key = "whoriz";
    parm.whoriz->key_desc = "name";
    parm.whoriz->type = TYPE_STRING;
    parm.whoriz->gisprompt = "old,cell,raster";
    parm.whoriz->description =
	_("Name of input raster map containing WEST HORIZON (degree)");

    parm.month = G_define_option();
    parm.month->key = "month";
    parm.month->type = TYPE_INTEGER;
    parm.month->required = YES;
    parm.month->description =
	_("Number of the month in the year i.e. January=1, February=2,...");

    parm.rad = G_define_option();
    parm.rad->key = "rad";
    parm.rad->key_desc = "name";
    parm.rad->type = TYPE_STRING;
    parm.rad->required = YES;
    parm.rad->gisprompt = "new,cell,raster";
    parm.rad->description =
	_("Name of output raster map containing SOLAR RADIATION in W/m^2");

    parm.hum = G_define_option();
    parm.hum->key = "hum";
    parm.hum->key_desc = "name";
    parm.hum->type = TYPE_STRING;
    parm.hum->required = YES;
    parm.hum->gisprompt = "new,cell,raster";
    parm.hum->description =
	_("Name of output raster map containing RELATIVE HUMIDITY in %");

    flag1 = G_define_flag();
    flag1->key = 'v';
    flag1->description = _("Run verbosely");

    /*   Parse command line */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    verbose = flag1->answer;

    /*  Check if input layers exists in data base  */
    if (G_find_cell2(parm.tmin->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.tmin->answer);
    }
    if (G_find_cell2(parm.tmax->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.tmax->answer);
    }
    if (G_find_cell2(parm.prcp->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.prcp->answer);
    }
    if (G_find_cell2(parm.elev->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.elev->answer);
    }
    if (G_find_cell2(parm.slope->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.slope->answer);
    }
    if (G_find_cell2(parm.aspect->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.aspect->answer);
    }
    if (G_find_cell2(parm.lat->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.lat->answer);
    }
    if (G_find_cell2(parm.ehoriz->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.ehoriz->answer);
    }
    if (G_find_cell2(parm.whoriz->answer, "") == NULL) {
	G_fatal_error(_("%s - not found"), parm.whoriz->answer);
    }

    /*  Check if specified output layer name IS LEGAL  */
    if (G_legal_filename(parm.rad->answer) < 0) {
	G_fatal_error(_("%s - illegal name"), parm.rad->answer);
    }

    if (G_legal_filename(parm.hum->answer) < 0) {
	G_fatal_error(_("%s - illegal name"), parm.hum->answer);
    }

    /*check if the output layer names EXIST */
    if (G_find_cell2((parm.rad->answer), G_mapset())) {
	G_fatal_error(_("%s - exits in Mapset <%s>, select another name"),
		      parm.rad->answer, G_mapset());
    }
    if (G_find_cell2((parm.hum->answer), G_mapset())) {
	G_fatal_error(_("%s - exits in Mapset <%s>, select another name"),
		      parm.hum->answer, G_mapset());
    }

    /*  Get database window parameters  */
    if (G_get_window(&window) < 0) {
	G_fatal_error(_("Can't read current window parameters"));
    }

    /*  find number of rows and columns in window    */
    nrows = G_window_rows();
    ncols = G_window_cols();

    tmin = G_allocate_f_raster_buf();
    tmax = G_allocate_f_raster_buf();
    prcp = G_allocate_f_raster_buf();
    elev = G_allocate_cell_buf();
    slope = G_allocate_cell_buf();
    aspect = G_allocate_cell_buf();
    lat = G_allocate_f_raster_buf();
    ehoriz = G_allocate_cell_buf();
    whoriz = G_allocate_cell_buf();
    rad = G_allocate_cell_buf();
    hum = G_allocate_cell_buf();

    sscanf(parm.month->answer, "%d", &nmonth);

    /*  Open input cell layers for reading  */

    tmin_fd =
	G_open_cell_old(parm.tmin->answer,
			G_find_cell2(parm.tmin->answer, ""));
    if (tmin_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.tmin->answer);
    }
    tmax_fd =
	G_open_cell_old(parm.tmax->answer,
			G_find_cell2(parm.tmax->answer, ""));
    if (tmax_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.tmax->answer);
    }
    prcp_fd =
	G_open_cell_old(parm.prcp->answer,
			G_find_cell2(parm.prcp->answer, ""));
    if (prcp_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.prcp->answer);
    }
    elev_fd =
	G_open_cell_old(parm.elev->answer,
			G_find_cell2(parm.elev->answer, ""));
    if (elev_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.elev->answer);
    }
    slope_fd =
	G_open_cell_old(parm.slope->answer,
			G_find_cell2(parm.slope->answer, ""));
    if (slope_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.slope->answer);
    }
    aspect_fd =
	G_open_cell_old(parm.aspect->answer,
			G_find_cell2(parm.aspect->answer, ""));
    if (aspect_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.aspect->answer);
    }
    lat_fd =
	G_open_cell_old(parm.lat->answer, G_find_cell2(parm.lat->answer, ""));
    if (lat_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.lat->answer);
    }
    ehoriz_fd =
	G_open_cell_old(parm.ehoriz->answer,
			G_find_cell2(parm.ehoriz->answer, ""));
    if (ehoriz_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.ehoriz->answer);
    }
    whoriz_fd =
	G_open_cell_old(parm.whoriz->answer,
			G_find_cell2(parm.whoriz->answer, ""));
    if (whoriz_fd < 0) {
	G_fatal_error(_("%s - can't open raster file"), parm.whoriz->answer);
    }
    rad_fd = G_open_cell_new(parm.rad->answer);
    hum_fd = G_open_cell_new(parm.hum->answer);


    /*major computation: compute HUM and RAD one cell a time */

    if (verbose)
	fprintf(stderr, "Percent Completed ... ");

    for (row = 0; row < nrows; row++) {
	if (verbose)
	    G_percent(row, nrows, 10);
	if (G_get_f_raster_row(tmin_fd, tmin, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_f_raster_row(tmax_fd, tmax, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_f_raster_row(prcp_fd, prcp, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_map_row(elev_fd, elev, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_map_row(slope_fd, slope, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_map_row(aspect_fd, aspect, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_f_raster_row(lat_fd, lat, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_map_row(ehoriz_fd, ehoriz, row) < 0)
	    G_fatal_error(_("Error reading row of data"));
	if (G_get_map_row(whoriz_fd, whoriz, row) < 0)
	    G_fatal_error(_("Error reading row of data"));

	/*initialize cell buffers for output map layers */
	for (col = 0; col < ncols; col++) {
	    rad[col] = hum[col] = 0;
	}

	for (col = 0; col < ncols; col++) {
	    newsnow = 0.0;
	    snowmelt = 0.0;
	    if (tmin[col] <= SNOW_TCRIT)
		newsnow = prcp[col];
	    else
		snowmelt = SNOW_TRATE * (tmin[col] - SNOW_TCRIT);
	    snowpack += newsnow - snowmelt;
	    if (snowpack < 0.0)
		snowpack = 0.0;
	    swe = snowpack;

	    /* STEP (1) calculate pressure ratio (site/reference) = f(elevation) */
	    t1 = 1.0 - (LR_STD * elev[col]) / T_STD;
	    t2 = G_STD / (LR_STD * (R / MA));
	    pratio = pow(t1, t2);
	    /* STEP (2) correct initial transmittance for elevation */
	    trans1 = pow(TBASE, pratio);
	    /* STEP (3) calculation of ttmax0, potential rad, and daylength */

	    /* precalculate the transcendentals */
	    lati = lat[col] * RADPERDEG;
	    if (lati > 1.5707)
		lati = 1.5707;
	    if (lati < -1.5707)
		lati = -1.5707;
	    pend = slope[col] * RADPERDEG;
	    esp = (-aspect[col] + 90) * RADPERDEG;
	    /* cosine of zenith angle for east and west horizons */
	    coszeh = cos(1.570796 - (ehoriz[col] * RADPERDEG));
	    coszwh = cos(1.570796 - (whoriz[col] * RADPERDEG));

	    /* sub-daily time and angular increment information */
	    dt = SRADDT;	/* set timestep */
	    dh = dt / SECPERRAD;	/* calculate hour-angle step */

	    /* calculate cos and sin of declination */
	    decl = MINDECL * cos((julian[nmonth] + DAYSOFF) * RADPERDAY);
	    /* do some precalculations for beam-slope geometry (bsg) */
	    bsg1 = -sin(pend) * sin(esp) * cos(decl);
	    bsg2 =
		(-cos(esp) * sin(pend) * sin(lati) +
		 cos(pend) * cos(lati)) * cos(decl);
	    bsg3 =
		(cos(esp) * sin(pend) * cos(lati) +
		 cos(pend) * sin(lati)) * sin(decl);

	    /* calculate daylength as a function of lat and decl */
	    cosegeom = cos(lati) * cos(decl);
	    sinegeom = sin(lati) * sin(decl);
	    coshss = -(sinegeom) / cosegeom;
	    if (coshss < -1.0)
		coshss = -1.0;	/* 24-hr daylight */
	    if (coshss > 1.0)
		coshss = 1.0;	/* 0-hr daylight */
	    hss = acos(coshss);	/* hour angle at sunset (radians) */
	    /* daylength (seconds) */
	    daylen = 2.0 * hss * SECPERRAD;
	    /* solar constant as a function of yearday (W/m^2) */
	    sc = 1368.0 + 45.5 * sin((2.0 * PI * julian[nmonth] / 365.25) +
				     1.7);
	    /* extraterrestrial radiation perpendicular to beam, total over the timestep (J) */
	    dir_beam_topa = sc * dt;
	    sum_trans = 0.0;
	    sum_flat_potrad = 0.0;
	    sum_slope_potrad = 0.0;

	    /* begin sub-daily hour-angle loop, from -hss to hss */
	    for (h = -hss; h < hss; h += dh) {
		/* calculate cosine of solar zenith angle */
		cza = cosegeom * cos(h) + sinegeom;

		/* calculate cosine of beam-slope angle */
		cbsa = sin(h) * bsg1 + cos(h) * bsg2 + bsg3;

		/* check if sun is above a flat horizon */
		if (cza > 0.0) {
		    /* when sun is above the ideal (flat) horizon, do all the flat-surface calculations to determine daily total
		     * transmittance, and save flat-surface potential radiation for later calculations of diffuse radiation */

		    /* potential radiation for this time period, flat surface,top of atmosphere */
		    dir_flat_topa = dir_beam_topa * cza;

		    /* determine optical air mass */
		    am = 1.0 / (cza + 0.0000001);
		    if (am > 2.9) {
			ami = (int)(acos(cza) / RADPERDEG) - 69;
			if (ami < 0)
			    ami = 0;
			if (ami > 20)
			    ami = 20;
			am = optam[ami];
		    }

		    /* correct instantaneous transmittance for this optical air mass */
		    trans2 = pow(trans1, am);

		    /* instantaneous transmittance is weighted by potential radiation for flat surface at top of atmosphere to get daily total transmittance */
		    sum_trans += trans2 * dir_flat_topa;

		    /* keep track of total potential radiation on a flat surface for ideal horizons */
		    sum_flat_potrad += dir_flat_topa;

		    /* keep track of whether this time step contributes to component 1 (direct on slope) */
		    if ((h < 0.0 && cza > coszeh && cbsa > 0.0) ||
			(h >= 0.0 && cza > coszwh && cbsa > 0.0)) {
			/* sun between east and west horizons, and direct on slope. this period contributes to component 1 */
			sum_slope_potrad += dir_beam_topa * cbsa;
		    }

		}		/* end if sun above ideal horizon */

	    }			/* end of sub-daily hour-angle loop */

	    /* calculate maximum daily total transmittance and daylight average flux density for a flat surface and the slope */
	    if (daylen) {
		ttmax0 = sum_trans / sum_flat_potrad;
		flat_potrad = sum_flat_potrad / daylen;
		slope_potrad = sum_slope_potrad / daylen;
	    }
	    else {
		ttmax0 = 0.0;
		flat_potrad = 0.0;
		slope_potrad = 0.0;
	    }


	    /* STEP (4)  calculate the sky proportion for diffuse radiation */
	    /* uses the product of spherical cap defined by average horizon angle and the great-circle truncation 
	     * of a hemisphere. this factor does notvary by yearday. */
	    avg_horizon = (ehoriz[col] + whoriz[col]) / 2.0;
	    horizon_scalar = 1.0 - sin(avg_horizon * RADPERDEG);
	    if (pend > avg_horizon)
		slope_excess = pend - avg_horizon;
	    else
		slope_excess = 0.0;
	    if (2.0 * avg_horizon > 180.0)
		slope_scalar = 0.0;
	    else {
		slope_scalar =
		    1.0 - (slope_excess / (180.0 - 2.0 * avg_horizon));
		if (slope_scalar < 0.0)
		    slope_scalar = 0.0;
	    }
	    sky_prop = horizon_scalar * slope_scalar;

	    /* b parameter, and t_fmax not varying with Tdew, so these can be calculated once, outside the iteration
	     * between radiation and humidity estimates. Requires storing t_fmax in an array. */
	    /* b parameter from 30-day average of DTR */
	    b = B0 + B1 * exp(-B2 * (tmax[col] - tmin[col]));

	    /* proportion of daily maximum transmittance */
	    t_fmax = 1.0 - 0.9 * exp(-b * pow((tmax[col] - tmin[col]), C));

	    /* correct for precipitation if this is a rain day */
	    if (prcp[col])
		t_fmax *= RAIN_SCALAR;

	    /* calculate radiation assuming that Tdew = tmin+k*(tday-tmin) */
	    tday = 0.725 * tmax[col] + 0.275 * tmin[col];
	    tdew = tmin[col] + 0.29 * (tday - tmin[col]);
	    pva = 610.7 * exp(17.38 * tdew / (239.0 + tdew));
	    pvs = 610.7 * exp(17.38 * tday / (239.0 + tday));
	    hum[col] = (int)(pva / pvs * 100);
	    t_tmax = ttmax0 + ABASE * pva;

	    /* final daily total transmittance */
	    t_final = t_tmax * t_fmax;

	    /* estimate fraction of radiation that is diffuse, on an instantaneous basis, from relationship with daily total
	     * transmittance in Jones (Plants and Microclimate, 1992) Fig 2.8, p. 25, and Gates (Biophysical Ecology, 1980)
	     * Fig 6.14, p. 122. */
	    pdif = -1.25 * t_final + 1.25;
	    if (pdif > 1.0)
		pdif = 1.0;
	    if (pdif < 0.0)
		pdif = 0.0;

	    /* estimate fraction of radiation that is direct, on an instantaneous basis */
	    pdir = 1.0 - pdif;

	    /* the daily total radiation is estimated as the sum of the following two components:
	     * 1. The direct radiation arriving during the part of the day when there is direct beam on the slope.
	     * 2. The diffuse radiation arriving over the entire daylength (when sun is above ideal horizon). */

	    /* component 1 */
	    srad1 = slope_potrad * t_final * pdir;

	    /* component 2 (diffuse) */
	    /* includes the effect of surface albedo in raising the diffuse radiation for obstructed horizons */
	    srad2 =
		flat_potrad * t_final * pdif * (sky_prop +
						DIF_ALB * (1.0 - sky_prop));

	    /* snow pack influence on radiation */
	    if (swe > 0.0) {
		/* snow correction in J/m2/day */
		sc = (1.32 + 0.096 * swe) * 1e6;
		/* convert to W/m2 and check for zero daylength */
		if (daylen > 0.0)
		    sc /= daylen;
		else
		    sc = 0.0;
		/* set a maximum correction of 100 W/m2 */
		if (sc > 100.0)
		    sc = 100.0;
	    }
	    else
		sc = 0.0;

	    /* save daily radiation and daylength */
	    rad[col] = (int)(srad1 + srad2 + sc);

	}

	G_put_raster_row(rad_fd, rad, CELL_TYPE);
	G_put_raster_row(hum_fd, hum, CELL_TYPE);
    }

    if (verbose)
	G_percent(row, nrows, 10);

    G_close_cell(tmin_fd);
    G_close_cell(tmax_fd);
    G_close_cell(prcp_fd);
    G_close_cell(elev_fd);
    G_close_cell(slope_fd);
    G_close_cell(aspect_fd);
    G_close_cell(lat_fd);
    G_close_cell(ehoriz_fd);
    G_close_cell(whoriz_fd);
    G_close_cell(rad_fd);
    G_close_cell(hum_fd);


    exit(EXIT_SUCCESS);
}
