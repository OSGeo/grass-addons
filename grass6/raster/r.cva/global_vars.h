/***********************************************************************/
/*
  global_vars.h

  CONTAINS

  Global variables                                                     */

/***********************************************************************/

#ifdef MAIN
#define GLOBAL
#else
#define GLOBAL extern
#endif

GLOBAL double Re;

GLOBAL double obs_elev, target_elev;
GLOBAL double max_dist;
GLOBAL double sample;
GLOBAL int background, seed, from_cells;
GLOBAL int patt_flag, patt_flag_v;
GLOBAL int show_mask;
GLOBAL int fract;
GLOBAL struct Cell_head window;   /* Region info used for sites option */

/* distance above which to apply earth curvature correction */
GLOBAL double DIST_CC;

/* these are set if the vector points support the ArcGIS attributes */
GLOBAL double SPOT;
GLOBAL int SPOT_SET;
GLOBAL double OFFSETB;
GLOBAL int OFFSETB_SET;
GLOBAL int ADJUST;
GLOBAL double AZIMUTH1;
GLOBAL int AZIMUTH1_SET;
GLOBAL double AZIMUTH2;
GLOBAL int AZIMUTH2_SET;
GLOBAL double VERT1;
GLOBAL int VERT1_SET;
GLOBAL double VERT2;
GLOBAL int VERT2_SET;
GLOBAL double RADIUS1;

