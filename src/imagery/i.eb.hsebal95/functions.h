/* These are the headers for the RS functions used in SEBAL */
/* 2004 */

/* Initial functions */
double DN2Rad_landsat7(double Lmin, double LMax, double QCalMax, double QCalmin,
                       int DN);
double Rad2Ref_landsat7(double radiance, double doy, double sun_elevation,
                        double k_exo);
double tempk_landsat7(double chan6);

double bb_alb_aster(double greenchan, double redchan, double nirchan,
                    double swirchan1, double swirchan2, double swirchan3,
                    double swirchan4, double swirchan5, double swirchan6);
double bb_alb_landsat(double bluechan, double greenchan, double redchan,
                      double nirchan, double chan5, double chan7);
double bb_alb_noaa(double redchan, double nirchan);

double bb_alb_modis(double redchan, double nirchan, double chan3, double chan4,
                    double chan5, double chan6, double chan7);
double nd_vi(double redchan, double nirchan);

double emissivity_generic(double ndvi);

double emissivity_modis(double e31, double e32);

double t0_dem(double dem, double tempk);

double t_air_approx(double temp_k);

/* Instantaneous rnet and g0 */
double r_net(double bbalb, double ndvi, double tempk, double tair, double e0,
             double tsw, double doy, double utc, double sunzangle);
double g_0(double bbalb, double ndvi, double tempk, double rnet, double utc);

/* Diurnal r_net and etpot */
double solar_day(double lat, double doy, double tsw);

double r_net_day(double bbalb, double solar, double tsw);

double et_pot_day(double bbalb, double solar, double tempk, double tsw);

/* Sensible heat flux functions */
double sensi_h(int iteration, double tempk_water, double tempk_desert,
               double t0_dem, double tempk, double ndvi, double ndvi_max,
               double dem, double rnet_desert, double g0_desert,
               double t0_dem_desert, double u2m, double dem_desert);
double roh_air_0(double tempk);

double zom_0(double ndvi, double ndvi_max);

double U_0(double zom_0, double u2m);

double rah_0(double zom_0, double u_0);

double h_0(double roh_air, double rah, double dtair);

double dt_air_approx(double temp_k);

double dt_air_0(double t0_dem, double tempk_water, double tempk_desert);

double dt_air_desert(double h_desert, double roh_air_desert, double rah_desert);
double dt_air(double t0_dem, double tempk_water, double tempk_desert,
              double dtair_desert);
double rohair(double dem, double tempk, double dtair);

double h1(double roh_air, double rah, double dtair);

double u_star(double t0_dem, double h, double ustar, double roh_air, double zom,
              double u2m);
double psi_h(double t0_dem, double h, double U_0, double roh_air);

double rah1(double psih, double u_star);

/* Final outputs */
double evap_fr(double r_net, double g0, double h);

double et_a(double r_net_day, double evap_f, double tempk);

double biomass(double ndvi, double solar_day, double evap_fr,
               double light_use_ef);
double soilmoisture(double ndvi, double evap_fr);
