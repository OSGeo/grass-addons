/***********************************************************************/
/*
  scan_all_cells.c
  
  Updated by Mark Lake on 17/8/01 for GRASS 5.x

  CONTAINS

  1) scan_all_cells                                                    */

/***********************************************************************/

/***********************************************************************/
/*
  scan_all_cells

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

#include "init_segment_file.h"
#include "line_of_sight.h"
#include "count_visible_cells.h"
#include "cumulate_visible_cells.h"
#include "delete_lists.h"

void scan_all_cells (int nrows, int ncols, 
		     SEGMENT *seg_in_p, SEGMENT *seg_out_1_p, 
		     SEGMENT *seg_out_2_p, SEGMENT *seg_patt_p, 
		     SEGMENT *seg_patt_p_v,
		     double *attempted_sample, double *actual_sample,
		     int terse, RASTER_MAP_TYPE data_type)
{
  int row_viewpt, col_viewpt;
  int mask;
  int null_value;
  int null_count;
  void *value = NULL;
  double cells_in_map;
  CELL cell_no;
  long int cells_analysed;
  double viewpt_elev = 0.0;
  struct point *heads[16];
  /* the following are used to store different raster map types */
  CELL c_value;
  FCELL f_value;
  DCELL d_value;    
    

  /* Initialise output segment file with appropriate data value */
  init_segment_file (nrows, ncols, seg_out_2_p, seg_patt_p);
  
  /* Initialise variables */
  cell_no = 0;
  cells_analysed = 0;

  /* Loop through all cells and perform line of sight analysis from each */
  if (! terse)
    fprintf (stdout, "\nPercentage complete:\n");
  
  cells_in_map = nrows * ncols;
  null_count = 0;
  
  for (row_viewpt = 0; row_viewpt < nrows; row_viewpt ++) {
      for (col_viewpt = 0; col_viewpt < ncols; col_viewpt ++) {
	  	cell_no ++;
	  
	    if(patt_flag_v) {
	      value = (char*) &mask;
	      segment_get(seg_patt_p_v, value,
			  row_viewpt, col_viewpt);
	    } else 
	      mask = 1;
	  
	  /* Only include if viewpoint is in area of interest */
	  if (mask) {
	      cells_analysed ++;
	      
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
		if (G_is_c_null_value (&c_value)) {
			null_value = 1;
			null_count ++;
		}
             }		
	     if ( data_type == FCELL_TYPE ) {
		viewpt_elev = f_value + obs_elev;
		if (G_is_f_null_value (&f_value)) {
			null_value = 1;
			null_count ++;
		}		
             }		
	     if ( data_type == DCELL_TYPE ) {
		viewpt_elev = d_value + obs_elev;
		if (G_is_d_null_value (&d_value)) {
			null_value = 1;
			null_count ++;
		}
             }			  

             if (!null_value) { 	
	     	if (SPOT_SET) {
	       		if (ADJUST) {
				if (SPOT >= viewpt_elev) {
					viewpt_elev = SPOT + obs_elev;
				}
	       		} else {
	    			viewpt_elev = SPOT;
			}
	     	}
	
		  		  
	      	line_of_sight (cell_no, row_viewpt, col_viewpt,
			     nrows, ncols, viewpt_elev,
			     heads, seg_in_p, seg_out_1_p,
			     seg_patt_p, patt_flag, data_type);
	      
	      	if (! from_cells)
              		count_visible_cells (cell_no, row_viewpt, col_viewpt,
		                         seg_out_1_p, seg_out_2_p, seg_patt_p, heads);
	      	else
		    cumulate_visible_cells (cell_no, row_viewpt, col_viewpt,
		                            seg_out_1_p, seg_out_2_p, seg_patt_p, heads);
	      
	      	delete_lists (heads);
	      }
	  } /* END (process one cell in mask) */

	  /* Print progress report */	  
	  if (! terse) {
		  G_percent (cell_no, (int) cells_in_map, 2);
	  }
	}
  
  } /* END (loop through ALL cells) */

  /* Calculate sample */
  *attempted_sample = 100.0;
  cells_analysed = cells_analysed - null_count;
  *actual_sample = 100 / (double) cells_in_map * (double) cells_analysed;
}
