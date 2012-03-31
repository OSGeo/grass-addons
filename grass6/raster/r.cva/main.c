/***********************************************************************/
/*  
  r.cva   in $GIS/src.contrib/IoA

  *****
 
  Mark Lake  30/6/99 (pdated 17/8/01 for GRASS 5.x)

  University College London
  Institute of Archaeology
  31-34 Gordon Square
  London.  WC1H 0PY

  Email: mark.lake@ucl.ac.uk

  *****
  
  Adaptations for new GRASS 5 site and raster formats
  Adaptations for new GRASS 6 vector format
    
  by Benjamin Ducke 2004
  benducke@compuserve.de

  Summary of changes:
       	- updated to GRASS 5 sites API
		   	- use GRASS routines to convert Site coordinates to raster coords
			- handle CELL, FCELL or DCELL as elevation input map format
			- handle NULL values in input map by copying them through to result
  	     		- renamed flag '-n' to '-a'
		 	- new flag '-n': convert -1 to NULL in output map
			- max viewing distance now set to 2000 m by default
			- handle all progress display through 'G_percent()'
			- all output now goes to 'stdout', so it can be piped to a file
  			- made source code more readable
			- updated manual pages
			- update tcltkgrass menu file
			
	- updated to GRASS 6
			- use new vector points format instead of sites
			- read and interpret special attributes in the vector map's DB table
			  the same way ArcInfo(tm) Spatial Analyst Extension(tm I guess) does
			- same attributes can also be set as global options
			- earth curvature correction
			- fixed nasty FP handling bugs that would cause the previous GRASS 5 version to
			  crash when compiled with newer versions of GCC
			- lots of fixes for NULL data handling in DEM
			- updated HTML manual page to reflect changes
  
  *****

  ACKNOWLEDGEMENTS

  The first version of r.cva was written by the author as part of the
  MAGICAL Project directed by Dr. Steven Mithen (University of Reading,
  U.K.).  The MAGICAL Project was made possible by a Natural Environment 
  Research Council award (NERC GR3/9540) to Dr. Mithen.

  This version of r.cva was significantly enhanced during the author's
  tenure of a Leverhulme Trust Special Research Fellowship at the 
  Institute of Archaeology, U.C.L., U.K.

  r.cva draws heavily on the code for r.los, which was written by
  Kewan Q. Khawaja, Intelligent Engineering Systems Laboratory, M.I.T.

  *****

  PURPOSE

  1) Perform cumulative viewshed (CVA) analysis.

  OPTIONS

  1)  Record the number of cells visible from:
  
  all          every map cell;
  systematic   a systematic sample of map cells;
  random       a random sample of map cells;
  sites        a list of sites.

  2)  Record how often each cell in the map is visible from:
  
  all          every map cell;
  systematic   a systematic sample of map cells;
  random       a random sample of map cells;
  sites        a list of sites.

  3) Random sampling may occur with or without replacement.

  4) All types of sampling may be subject to binary masks such that:

     i)  Not all possible destination cells (cells to be `looked at')
         are of interest;

     ii) Not all possible viewpoints are of interest.

  5) It is possible to specify the height of the observer.

  6) It is possible to specify the height of the target object
     above ground.                                                     

  NOTE

  r.cva includes fixes for two bugs in the current version of r.los.
  These are that the observer elevation is cast to an integer, and that
  the patt_map does not effect the viewpoint and its immediately 
  neighbouring cells                                                   */

/***********************************************************************/
  
/***********************************************************************/
/* main                                                                
   
   Called from:
  
   1) None
 
   Calls functions in:
 
   1) scan_all_cells.c
   2) random_sample.c
   3) systematic_sample.c
   4) point_sample.c
   5) segment_file.c                                                   */

/***********************************************************************/

#include <stdlib.h>
#include <string.h>
#include "config.h"
#include <grass/segment.h>
#include <grass/gis.h>
#define MAIN
#include "global_vars.h"
#include "point.h"

#include "segment_file.h"
#include "scan_all_cells.h"
#include "systematic_sample.h"
#include "random_sample.h"
#include "point_sample.h"

#define kSEGFRACT 4             /* Controls no. of segments 
                                   DO NOT CHANGE */

      
int main(int argc, char *argv[])
{
  int nrows, ncols;
  int new,old,patt,patt_v,in_fd,out_fd_1, out_fd_2;
  int patt_fd, patt_fd_v, rnd_fd;
  int same_mask;
  char old_mapset [50], patt_mapset [50], patt_mapset_v [50];
  char current_mapset [50];
  char in_name [128], out_name_1 [128], out_name_2 [128];
  char patt_name [128], patt_name_v [128], rnd_name [128];
  double attempted_sample, actual_sample;
  struct Categories cats;
  struct History history;
  extern struct Cell_head window;
  CELL *cell = NULL;
  DCELL *dcell = NULL;
  FCELL *fcell = NULL;
  SEGMENT seg_in, seg_out_1, seg_out_2, seg_patt, seg_patt_v, seg_rnd;
  SEGMENT *seg_patt_p_v = NULL;
  struct point *segment();
  struct GModule *module;
  struct Option *input, *patt_map, *patt_map_v, *type;
  struct Option *opt_obs_elev, *opt_target_elev;
  struct Option *opt_max_dist, *output, *opt_seed, *opt_sample;
  struct Option *sites;
  struct Option *curvature_corr;
  struct Option *spot, *offseta, *offsetb, *azimuth1, *azimuth2, *vert1, *vert2, *radius1, *radius2;
  struct Flag *replace, *from, *overwrite, *quiet, *mask, *silent;
  struct Flag *adjust, *absolute, *nulls, *ignore;
  /* stores cell data mode (CELL_TYPE, FCELL_TYPE or DCELL_TYPE) */
  int cell_mode;
  int make_nulls = 0; /* this signals whether -1 in output map should be
                             converted to NULL */

 
  /***********************************************************************/
  /* Preliminary things                                                  */
  /***********************************************************************/

  /* Initialize the GIS calls and sort out error handling */

  G_gisinit (argv[0]);
  G_sleep_on_error (0);


  /* Define the options */

  module = G_define_module();
  module->description = "Multiple/cumulative viewshed analysis";

  input = G_define_standard_option(G_OPT_R_INPUT) ;
  input->key        = "input";
  input->type       = TYPE_STRING;
  input->required   = YES;
  input->gisprompt  = "old,fcell,dcell,cell,raster" ;
  input->description= "Elevation raster map" ;
    
  patt_map = G_define_standard_option(G_OPT_R_INPUT);
  patt_map->key        = "target_mask";
  patt_map->type       = TYPE_STRING;
  patt_map->required   = NO;
  patt_map->description= "Binary raster map for target cells";
  patt_map->gisprompt  = "old,cell,raster" ;
  
  patt_map_v = G_define_standard_option(G_OPT_R_INPUT);
  patt_map_v->key        = "viewpt_mask";
  patt_map_v->type       = TYPE_STRING;
  patt_map_v->required   = NO;
  patt_map_v->description= "Binary raster map for viewpoints";
  patt_map_v->gisprompt  = "old,cell,raster" ;

  sites = G_define_standard_option(G_OPT_V_MAP);
  sites->key        = "sites";
  sites->type       = TYPE_STRING;
  sites->required   = NO;
  sites->description= "Vector map with sites points" ;

  output = G_define_standard_option(G_OPT_R_OUTPUT);
  output->key        = "output";
  output->type       = TYPE_STRING;
  output->required   = YES;
  output->gisprompt  = "cell,raster" ;
  output->description= "Raster map name for storing results";
    
  opt_obs_elev = G_define_option() ;
  opt_obs_elev->key        = "obs_elev";
  opt_obs_elev->type       = TYPE_DOUBLE;
  opt_obs_elev->required   = NO;
  opt_obs_elev->answer     = "1.75";
  opt_obs_elev->description= "Height of the viewing location";
    
  opt_target_elev = G_define_option() ;
  opt_target_elev->key        = "target_elev";
  opt_target_elev->type       = TYPE_DOUBLE;
  opt_target_elev->required   = NO;
  opt_target_elev->answer     = "0.0";
  opt_target_elev->description= "Height of the target location";

  opt_max_dist = G_define_option() ;
  opt_max_dist->key        = "max_dist";
  opt_max_dist->type       = TYPE_DOUBLE;
  opt_max_dist->required   = NO;
  opt_max_dist->answer     = "2000";
  opt_max_dist->options    = "0.0-9999999.9" ;
  opt_max_dist->description= "Max viewing distance in meters" ;

  opt_seed = G_define_option() ;
  opt_seed->key        = "seed";
  opt_seed->type       = TYPE_INTEGER;
  opt_seed->required   = NO;
  opt_seed->answer     = "1";
  opt_seed->options    = "0-32767" ;
  opt_seed->description= "Seed for the random number generator" ; 

  opt_sample = G_define_option() ;
  opt_sample->key        = "sample";
  opt_sample->type       = TYPE_DOUBLE;
  opt_sample->required   = NO;
  opt_sample->answer     = "10.0";
  opt_sample->description= "Sampling frequency as a percentage of cells" ; 
    
  type = G_define_option();
  type->key        = "type";
  type->type       = TYPE_STRING;
  type->required   = YES;
  type->answer     = "sites";
  type->options    = "sites,systematic,random,all";
  type->description= "Type of vieshed analysis";

  spot = G_define_option();
  spot->key = "spot";
  spot->type = TYPE_DOUBLE;
  spot->required = NO;
  spot->description = "Absolute observer height";
  
  offseta = G_define_option();
  offseta->key = "offseta";
  offseta->type = TYPE_DOUBLE;
  offseta->required = NO;
  offseta->description = "Observer offset (OFFSETA=obs_elev)";
  
  offsetb = G_define_option();
  offsetb->key = "offsetb";
  offsetb->type = TYPE_DOUBLE;
  offsetb->required = NO;
  offsetb->description = "target offset (OFFSETB=target_elev)";
  
  azimuth1 = G_define_option();
  azimuth1->key = "azimuth1";
  azimuth1->type = TYPE_DOUBLE;
  azimuth1->required = NO;
  azimuth1->options = "0.0-360.0";
  azimuth1->description = "Minimum azimuth (AZIMUTH1)";

  azimuth2 = G_define_option();
  azimuth2->key = "azimuth2";
  azimuth2->type = TYPE_DOUBLE;
  azimuth2->required = NO;
  azimuth2->options = "0.0-360.0";
  azimuth2->description = "Maximum azimuth (AZIMUTH2)";
  
  vert1 = G_define_option();
  vert1->key = "vert1";
  vert1->type = TYPE_DOUBLE;
  vert1->required = NO;
  vert1->options = "0.0-90.0";
  vert1->description = "Minimum vertical angle (VERT1)";
  
  vert2 = G_define_option();
  vert2->key = "vert2";
  vert2->type = TYPE_DOUBLE;
  vert2->required = NO;
  vert2->options = "-90.0-0.0";
  vert2->description = "Maximum vertical angle (VERT2)";

  radius1 = G_define_option();
  radius1->key = "radius1";
  radius1->type = TYPE_DOUBLE;
  radius1->required = NO;
  radius1->description = "Minimum distance from observer (RADIUS1)";

  radius2 = G_define_option();
  radius2->key = "radius2";
  radius2->type = TYPE_DOUBLE;
  radius2->required = NO;
  radius2->description = "Maximum distance to observer (RADIUS2)";
  
  curvature_corr = G_define_option ();
  curvature_corr->key = "curvc";
  curvature_corr->type = TYPE_DOUBLE;
  curvature_corr->required = NO;
  curvature_corr->answer = "0.0";
  curvature_corr->description = "Earth curvature correction threshold (0.0 = off)";
    
  from = G_define_flag ();
  from->key = 'f';
  from->description = "Calculate the `visibility from' rather than `viewsheds of' ";

  mask = G_define_flag ();
  mask->key = 'm';
  mask->description = "Differentiate masked cells from data value zero ";

  absolute = G_define_flag ();
  absolute->key = 'a';
  absolute->description = "Treat sample size as no. of cells ";

  overwrite = G_define_flag ();
  overwrite->key = 'o';
  overwrite->description = "Overwrite output file if it exists ";
  
  quiet = G_define_flag ();
  quiet->key = 'q';
  quiet->description = "Run quietly (i.e. do not report \% complete) ";
  
  replace = G_define_flag ();
  replace->key = 'r';
  replace->description = "Allow replacement during random sampling ";
  
  adjust = G_define_flag ();
  adjust->key = 'h';
  adjust->description = "Adjust spot heights below surface";

  ignore = G_define_flag ();
  ignore->key = 'i';
  ignore->description = "Ignore site attributes";

  nulls = G_define_flag ();
  nulls->key = 'n';
  nulls->description = "Convert -1 to NULL in output map ";
  
  silent = G_define_flag ();
  silent->key = 's';
  silent->description = "Run silently ";
  
  if (G_parser(argc, argv))
    exit (-1);
    

  /* Make numeric parameters globally available */
  sscanf (opt_obs_elev->answer, "%lf", &obs_elev);
  //sscanf (opt_target_elev->answer, "%lf", &target_elev);
  if ( opt_target_elev->answer != NULL ) {
  	OFFSETB_SET = 1; /* OFFSETB is the same as old parameter target_elev */
	OFFSETB = atof (opt_target_elev->answer);
  }  
  
  sscanf (opt_max_dist->answer, "%lf", &max_dist);
  sscanf (opt_seed->answer, "%d", &seed);
  sscanf (opt_sample->answer, "%lf", &sample);
  from_cells = from->answer;
  if(patt_map->answer == NULL)
    patt_flag = 0;
  else
    patt_flag = 1;
  if(patt_map_v->answer == NULL)
    patt_flag_v = 0;
  else
    patt_flag_v = 1;
  if (mask->answer)
    background = -1;
  else 
    background = 0;
  
  if (adjust->answer) {
  	ADJUST = 1;
  } else {
  	ADJUST = 0;
  }
  
  if (nulls->answer)
	make_nulls = 1;
  
  fract = kSEGFRACT;  

  /* Check sample size is sensible */
  if (!absolute->answer)
    {
      if ((sample < 0.0) || (sample > 100.0))
	G_fatal_error ("Sample size must be in range 0 to 100 ");
    }
  else
    if (sample < 0.0)
      G_fatal_error ("Sample size must be a positive number ");

  /* If both destination and viewpoint masks have been specified
     check whether they are the same.  If so set flag so that only
     one is loaded into memory and the other is simply made a duplicate
     set of pointers. */  
  if (patt_flag && patt_flag_v)
    {
      if (strcmp (patt_map->answer, patt_map_v->answer) == 0)
	same_mask = 1;
      else
	same_mask = 0;
    }
  else same_mask = 0;

  /* Must be quiet if silent */
  if (silent->answer)
    quiet->answer = 1;

  /* Get current region */  
  G_get_window (&window);
  nrows = G_window_rows();
  ncols = G_window_cols();  

  /* determine mode of input map */
  cell_mode = G_raster_map_type (input->answer,"");
  
  /* Allocate buffer space for row-io to layer */    
  cell = G_allocate_c_raster_buf(); /* we need a cell buffer, anyhow */
  if (cell_mode == FCELL_TYPE){ /* we might also need an fcell or dcell buffer for */
	  fcell = G_allocate_f_raster_buf(); /* elevation data */
  }
  if (cell_mode == DCELL_TYPE) {
	  dcell = G_allocate_d_raster_buf();
  }  

  /* Open files and initialise memory for random access */
  /* create segment files for all input raster maps and store */
  /* raster maps in them */ 
  /* input->answer is the elevation map */
  
  /* store elevation map in a CELL, FCELL or DCELL segment file, */
  /* according to its type */
  if ( cell_mode == CELL_TYPE) {  
    Segment_infile (input->answer, old_mapset, "", &old, 
		  in_name, &in_fd, &seg_in, cell, fract, cell_mode);
  }
  if ( cell_mode == FCELL_TYPE) {  
    Segment_infile (input->answer, old_mapset, "", &old, 
		  in_name, &in_fd, &seg_in, fcell, fract, cell_mode);
  } 
  if ( cell_mode == DCELL_TYPE) {  
    Segment_infile (input->answer, old_mapset, "", &old, 
		  in_name, &in_fd, &seg_in, dcell, fract, cell_mode);
  }
  
  /* store mask maps in CELL segment files */
  if (patt_flag)
    Segment_infile (patt_map->answer, patt_mapset, "", &patt, 
		            patt_name, &patt_fd, &seg_patt, cell, fract, CELL_TYPE);
  
  if (patt_flag_v) {
    if (same_mask)
	  seg_patt_p_v = &seg_patt;
    else {
	  seg_patt_p_v = &seg_patt_v;
	  Segment_infile (patt_map_v->answer, patt_mapset_v, "", &patt_v, 
			          patt_name_v, &patt_fd_v, seg_patt_p_v, cell, fract, CELL_TYPE);
	}
  }

  
  Segment_named_outfile  (output->answer, current_mapset, &new,
			  out_name_2, &out_fd_2, &seg_out_2,
			  overwrite->answer, quiet->answer, fract, CELL_TYPE);
  
  Segment_tmpfile (out_name_1, &out_fd_1, &seg_out_1, fract, CELL_TYPE);
  
  /* Record name of output map if in quiet mode but not silent mode */   
  if (!silent->answer)
    {
      if (quiet->answer)
	{
	  fprintf (stdout, "\n\nOutput map is: '%s'", output->answer);
	  if (mask->answer)
	    fprintf (stdout, "   (masked cells = -1)");
	  fflush (stdout);
	}
    }


  /***********************************************************************/
  /* Perform analysis of the type requested                              */
  /***********************************************************************/

  /* earth curvature correction threshold */
    DIST_CC = atof (curvature_corr->answer);
    Re = 6356766.0; /* radius of Earth in m */

  /* set attributes to default values */
    SPOT = 0.0;
    SPOT_SET = 0;
    OFFSETB = 0.0;
    OFFSETB_SET = 0;    
    AZIMUTH1 = 0.0;
    AZIMUTH1_SET = 0;
    AZIMUTH2 = 360.0;
    AZIMUTH2_SET = 0;
    VERT1 = 90.0;
    VERT1_SET = 0;
    VERT2 = -90.0;
    VERT2_SET = 0;
    RADIUS1 = 0.0;

  /* check for global attributes */
  if (spot->answer != NULL) {
  	SPOT = atof (spot->answer);
	SPOT_SET = 1;
  }
  if (offseta->answer != NULL) {
  	obs_elev = atof (offseta->answer);
  }
  if (offsetb->answer != NULL) {
  	OFFSETB_SET = 1;
	OFFSETB = atof (offsetb->answer);
  }
  if (azimuth1->answer != NULL) {
  	AZIMUTH1 = atof (azimuth1->answer);
  	AZIMUTH1_SET = 1;
  }
  if (azimuth2->answer != NULL) {
  	AZIMUTH2 = atof (azimuth2->answer);
	AZIMUTH2_SET = 1;
  }
  if (vert1->answer != NULL) {
  	VERT1 = atof (vert1->answer);
	VERT1_SET = 1;
  }
  if (vert2->answer != NULL) {
  	VERT2 = atof (vert2->answer);
	VERT2_SET = 1;
  }
  if (radius2->answer != NULL) {
  	max_dist = atof (radius2->answer);
  }
  if ((radius1->answer != NULL) && (atof (radius1->answer) < max_dist)) {
  	RADIUS1 = atof (radius1->answer);
  }
  

  /* use all raster cells in input map as observer locations (!) */	
  if (strcmp (type->answer, "all") == 0)
    scan_all_cells (nrows, ncols,
		    &seg_in, &seg_out_1, &seg_out_2, &seg_patt,
		    seg_patt_p_v, &attempted_sample, &actual_sample,
		    quiet->answer, cell_mode);
  
  /* use a gridded set of raster cells as observer locations */
  if (strcmp (type->answer, "systematic") == 0)
    systematic_sample (nrows, ncols,
		       &seg_in, &seg_out_1, &seg_out_2, &seg_patt,
		       seg_patt_p_v, &attempted_sample, 
		       &actual_sample, quiet->answer, 
		       absolute->answer, cell_mode);
  
  /* use a random set of raster cells as observer locations */
  if (strcmp (type->answer, "random") == 0) {
      Segment_tmpfile (rnd_name, &rnd_fd, &seg_rnd, fract, CELL_TYPE);    
      random_sample (nrows, ncols,
		     &seg_in, &seg_out_1, &seg_out_2, &seg_patt,
		     seg_patt_p_v, &seg_rnd,
		     &attempted_sample, &actual_sample,
		     replace->answer, quiet->answer,
		     absolute->answer, cell_mode);
      Close_segmented_tmpfile (rnd_name, rnd_fd, &seg_rnd);
  }
  
  /* do a point sample using site locations */
  if (strcmp (type->answer, "sites") == 0)  
    point_sample (&window, nrows, ncols,
		  &seg_in, &seg_out_1, &seg_out_2, &seg_patt, 
		  seg_patt_p_v, &attempted_sample, &actual_sample,
		  sites->answer, quiet->answer, cell_mode, ignore->answer);
  

  /***********************************************************************/
  /* Tidy up                                                             */
  /***********************************************************************/  
    
  /* write result file */
  Close_segmented_outfile (output->answer, new, out_name_2, out_fd_2, 
			               &seg_out_2, cell, quiet->answer,
  						   &seg_in, cell_mode, make_nulls);
  
  /* Close remaining files */
  Close_segmented_infile (old, in_name, in_fd, &seg_in);
  if (patt_flag)
    Close_segmented_infile (patt, patt_name, patt_fd, &seg_patt);    
  if ((patt_flag_v) && (! same_mask))
    Close_segmented_infile (patt_v, patt_name_v, patt_fd_v,
			    seg_patt_p_v);
  Close_segmented_tmpfile (out_name_1, out_fd_1, &seg_out_1);
    

  /* Remind user about value used to indicate NULL data */
  if ((! quiet->answer) && mask->answer)
    fprintf (stdout, "   (masked cells = -1)");


  /* Provide user with info about actual sampling frequencies */
  if (strcmp (type->answer, "sites") == 0)
    sample = attempted_sample;
  if (! quiet->answer)
    {
      fprintf (stdout, "\n");
      fflush (stdout);
    }
  if (!silent->answer)
    {
      if (absolute->answer)
	{     
	  fprintf (stdout, 
		   "\nSample: requested = %8.5lf  attempted = %8.5lf  actual = %8.5lf\n", sample, attempted_sample, actual_sample);
	}
      else
	{
	  fprintf (stdout, 
		   "\nSample: requested = %8.5lf%%  attempted = %8.5lf%%  actual = %8.5lf%%\n", sample, attempted_sample, actual_sample);
	}
      fflush (stdout);
    }


  /* Create support files */

  if (! quiet->answer)
    fprintf (stdout, "\nCreating support files "); fflush (stdout);

  
  /* Create category file for output map */  
  G_read_cats (output->answer, current_mapset, &cats);
  G_set_cats_fmt ("$1 cell$?s", 1.0, 0.0, 0.0, 0.0, &cats);
  G_write_cats (output->answer, &cats);
  G_free_cats (&cats);

  /* Create history support file for output map */  
  G_short_history (output->answer, "raster", &history);
  history.edlinecnt = 4;
  sprintf (history.edhist [0], "Sample type = %s", type->answer);
  sprintf (history.edhist[1], "Requested = %8.5lf%%", sample);
  sprintf (history.edhist[2], "Attempted = %8.5lf%%", attempted_sample);
  sprintf (history.edhist[3], "Actual = %8.5lf%%", actual_sample);
  if (G_write_history (output->answer, &history) == -1)
    G_warning ("Failed to write history file ");
  
  if (! quiet->answer)
    fprintf (stdout, "\nJob finished\n");

  return (0);
}
