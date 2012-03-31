/***********************************************************************/
/*
  random_sample.c

  Updated by Mark Lake on 17/8/01 for GRASS 5.x

  CONTAINS

  1) random_sample                                                     */

/***********************************************************************/

/***********************************************************************/
/*
  random_sample

  Called from:
  
  1) main                   main.c
 
  Calls:
 
  1) line_of_sight          line_of_site.c
  2) count_visible_cells    count_visible_cells.c
  3) cumulate_visible_cells cumulate_visible_cells.c
  4) delete_lists           delete_lists.c                             */

/***********************************************************************/

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "point.h"
#include "global_vars.h"
#include "zufall.h"

#include "init_segment_file.h"
#include "line_of_sight.h"
#include "count_visible_cells.h"
#include "cumulate_visible_cells.h"
#include "delete_lists.h"

#define MAX_RANDOM_ALLOCATIONS 1000  /*   number of attempts to pick cell  
					 from which los has not yet been  
					 conducted before it is assumed   
					 that prog has gone into infinite 
					 loop   */

void random_sample (int nrows, int ncols, SEGMENT *seg_in_p,
		    SEGMENT *seg_out_1_p, SEGMENT *seg_out_2_p, 
		    SEGMENT *seg_patt_p, SEGMENT *seg_patt_p_v, 
		    SEGMENT *seg_rnd_p, 
		    double *attempted_sample, double *actual_sample,
		    int replace, int terse, int absolute, RASTER_MAP_TYPE data_type)
{
  int row_viewpt, col_viewpt;
  void *value;
  double viewpt_elev = 0.0;
  struct point *heads[16];
  
  extern long int random_int();
  int loop_check, duplicate;
  int row, col;
  int null_value;
  CELL mask;
  CELL cell_no;
  long int cells_in_map, cells_to_sample;
  long int cells_sampled, cells_sampled_uniquely;
  CELL data, already_analysed;
  char message[128];
  /* the following are used to store different raster map types */
  CELL c_value;
  FCELL f_value;
  DCELL d_value;
  

  /*   Seed random number generator */
  if ((seed < MIN_SEED) || (seed > MAX_SEED))
    G_fatal_error ("Seed out of range ");
    
  if (zufalli (seed) != 0) {
	sprintf (message, "Failed to seed random number generator!");
    G_fatal_error (message);
  }
  
  
  /* Initialise output segment file with appropriate data value */
  init_segment_file (nrows, ncols, seg_out_2_p, seg_patt_p);


  /* Initialise segment file used to prevent / report replacement */
  data = background;
  value = (char*) &data;
  for (row = 0; row < nrows; row ++) {
    for (col = 0; col < ncols; col ++) {
	  segment_put (seg_rnd_p, value, row, col);
	}
  }


  /* Initialise variables */
  already_analysed = background + 1;
  cells_in_map = nrows * ncols;
  if (absolute)                  /* Sample is no. of cells not % */
    cells_to_sample = (long int) sample;
  else
    cells_to_sample = (long int) (sample / 100.0 * (double) cells_in_map);
  cell_no = 0;
  cells_sampled = 0;
  cells_sampled_uniquely = 0;


  /* Randomly select cells and perform line of sight analysis from each */
  if (! terse)
   fprintf (stdout, "\nPercentage complete:\n");

  for (cells_sampled = 1; cells_sampled <= cells_to_sample; cells_sampled += 1) {
      cell_no ++;      

      /* Do preparatory things to prevent long or infinite loop */
      loop_check = 0;      
      do {	
	  	/* Check that number of attempts is not excessive */
	  	loop_check ++;
	  	if (loop_check > MAX_RANDOM_ALLOCATIONS) {
			sprintf (message, "Failed to pick a viewpoint which has not\nyet been analysed.");
	    	G_fatal_error (message);
		}
	 
	  	/* Randomly allocate the viewpoint... */
	  	row_viewpt = (int) random_int (0, nrows - 1);
	  	col_viewpt = (int) random_int (0, ncols - 1);

		/* check for NULL values in DEM */
	    	if ( data_type == CELL_TYPE ) {
	    		value = (CELL*) &c_value;
	    	}		      
	    	if ( data_type == FCELL_TYPE ) {
	    		value = (FCELL*) &f_value;
	    	}		      
	    	if ( data_type == DCELL_TYPE ) {
	    		value = (DCELL*) &d_value;
	    	}					      

	    	null_value = 0;
	    	segment_get (seg_in_p, value, row_viewpt, col_viewpt);

	    	if ( data_type == CELL_TYPE ) {
	    		viewpt_elev = c_value + obs_elev;
			if (G_is_c_null_value (&c_value)) {
				null_value = 1;
			}		    
            	}		    
	    	if ( data_type == FCELL_TYPE ) {
	    		viewpt_elev = f_value + obs_elev;
			if (G_is_f_null_value (&f_value)) {
				null_value = 1;
			}		    
            	}		    
	    	if ( data_type == DCELL_TYPE ) {
	    		viewpt_elev = d_value + obs_elev;
			if (G_is_d_null_value (&d_value)) {
				null_value = 1;
			}		    
            	}
	 
	  	/* ...and check that this cell has not already been analysed */
	  	value = (char*) &data;
	  	segment_get (seg_rnd_p, value, row_viewpt, col_viewpt);
	  	if (replace) {
	      		if (data == already_analysed) {
		  		data = background;  /* Trick to break out out
					 			   of repeat loop */
		  		duplicate = 1;
		  	} else
				duplicate = 0;
	    	} else
	      		duplicate = 0;

	  	/* Check whether viewpoint is in area of interest */
	  	if(patt_flag_v) {
	        	value = (char*) &mask;
	      		segment_get(seg_patt_p_v, value, row_viewpt, col_viewpt);
	    	} else
	      		mask = 1;
	  
	  } while ((data == already_analysed) || (! mask) || (null_value) );


      /* Don't actually reanalyse duplicates.  This saves time.
	     More importantly, it prevents erroneous results 
	     with cumulate (-f) option */
      if (! duplicate) {
	    cells_sampled_uniquely ++;

	    /* Mark viewpoint in temporary file to
	       prevent duplication or allow number of
	       duplications to be counted */	  
	    value = (char*) &already_analysed;
	    segment_put (seg_rnd_p, value, row_viewpt, col_viewpt);
	  
	 	 
	    /* Read elevation of current view point */
	    if ( data_type == CELL_TYPE ) {
	    	value = (CELL*) &c_value;
	    }		      
	    if ( data_type == FCELL_TYPE ) {
	    	value = (FCELL*) &f_value;
	    }		      
	    if ( data_type == DCELL_TYPE ) {
	    	value = (DCELL*) &d_value;
	    }					      

	    null_value = 0;
	    segment_get (seg_in_p, value, row_viewpt, col_viewpt);

	    if ( data_type == CELL_TYPE ) {
	    	viewpt_elev = c_value + obs_elev;
            }		    
	    if ( data_type == FCELL_TYPE ) {
	    	viewpt_elev = f_value + obs_elev;
            }		    
	    if ( data_type == DCELL_TYPE ) {
	    	viewpt_elev = d_value + obs_elev;
            }
	
	    if (SPOT_SET) {
	       	if (ADJUST) {
			if (SPOT >= viewpt_elev) {
				viewpt_elev = SPOT + obs_elev;
			}
	       	} else {
	    		viewpt_elev = SPOT;
		}
	    }
		  

	    /* Do line of sight analysis from current viewpoint */
	    line_of_sight (cell_no, row_viewpt, col_viewpt, nrows, ncols, viewpt_elev,
			           heads, seg_in_p, seg_out_1_p, seg_patt_p, patt_flag, data_type);

	    /* Calculate viewshed */	  
	    if (! from_cells) {
	      count_visible_cells (cell_no, row_viewpt, col_viewpt,
		                       seg_out_1_p, seg_out_2_p, seg_patt_p, heads);
	    } else {
	      cumulate_visible_cells (cell_no, row_viewpt, col_viewpt,
	                              seg_out_1_p, seg_out_2_p, seg_patt_p, heads);
            } 
	    /* Free memory used in line-of-sight analysis */
	    delete_lists (heads);
	  }
     

      /* Print percentage complete */
      if (! terse) {
	  	G_percent (cells_sampled, cells_to_sample, 1);
	  }
	  
   } /* END (loop through sampled cells) */


  /* Calculate_sample */
  if (absolute) {
      *attempted_sample = cell_no;
      *actual_sample = cells_sampled_uniquely;
  } else {
      *attempted_sample = 100.0 / (double) cells_in_map * (double) cell_no;
      *actual_sample = 100.0 / 
	(double) cells_in_map * (double) cells_sampled_uniquely;
  }
}
