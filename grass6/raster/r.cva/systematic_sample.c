/***********************************************************************/
/*
  systematic_sample.c

  Updated by Mark Lake on 17/8/01 for GRASS 5.x

  CONTAINS

  1) systematic_sample                                                 */

/***********************************************************************/

/***********************************************************************/
/*
  systematic_sample

  Called from:
  
  1) main                   main.c
 
  Calls:
 
  1) line_of_sight          line_of_site.c
  2) count_visible_cells    count_visible_cells.c
  3) cumulate_visible_cells cumulate_visible_cells.c
  4) delete_lists           delete_lists.c                             */

/***********************************************************************/

#include "config.h"
#include <math.h>

#include <grass/gis.h>
#include <grass/segment.h>

#include "point.h"
#include "global_vars.h"

#include "init_segment_file.h"
#include "line_of_sight.h"
#include "count_visible_cells.h"
#include "cumulate_visible_cells.h"
#include "delete_lists.h"

void systematic_sample (int nrows, int ncols,
			SEGMENT *seg_in_p, SEGMENT *seg_out_1_p,
			SEGMENT *seg_out_2_p, SEGMENT *seg_patt_p,
			SEGMENT *seg_patt_p_v, 
			double *attempted_sample, double *actual_sample,
			int terse,
			int absolute,
			RASTER_MAP_TYPE data_type)
{
  int row_viewpt, col_viewpt;
  int mask;
  int null_value;
  int null_count;
  void *value = NULL;
  CELL cell_no, actual_cells;
  double viewpt_elev = 0.0;
  struct point *heads[16];
  
  double row_increment, col_increment;
  double no_cells_to_sample, actual_cells_to_sample, cells_in_map;
  double side_of_square_sample;
  double ratio_of_sides, rows_in_sample, cols_in_sample;
  double sample_row, sample_col;
  
  /* the following are used to store different raster map types */
  CELL c_value;
  FCELL f_value;
  DCELL d_value;



  /* Initialise output segment file with appropriate data value */
  init_segment_file (nrows, ncols, seg_out_2_p, seg_patt_p);

  /*  Calculate the row and col spacings */
  if (absolute)                  /* Sample is no. of cells not % */
    no_cells_to_sample = (long int) sample;
  else  
    no_cells_to_sample =  sample / 100.0 * (double) nrows * (double) ncols;
  side_of_square_sample = sqrt (no_cells_to_sample);
  ratio_of_sides = (double) nrows / (double) ncols;
  rows_in_sample = ratio_of_sides * side_of_square_sample;
  if (fmod (rows_in_sample, (double) 1) < 0.5)
    rows_in_sample = floor (rows_in_sample);
  else 
    rows_in_sample = ceil (rows_in_sample);
  cols_in_sample = (1 / ratio_of_sides) * side_of_square_sample;
  if (fmod (cols_in_sample, (double) 1) < 0.5)
    cols_in_sample = floor (cols_in_sample);
  else 
    cols_in_sample = ceil (cols_in_sample);
  row_increment = nrows / rows_in_sample;
  col_increment = ncols / cols_in_sample;
  actual_cells_to_sample = rows_in_sample * cols_in_sample;
  cells_in_map = nrows * ncols;
  null_count = 0;
  

  /* Loop through sample of cells and perform
       line of sight analysis from each */

  if (! terse)
    fprintf (stdout, "\nPercentage complete:\n");
  
  actual_cells = 0;
  cell_no = 0;
  
  sample_row = ((double) nrows - ((rows_in_sample - 1) * row_increment)) / 2;
  while (sample_row < nrows) {
    sample_col = ((double) ncols - ((cols_in_sample - 1) * col_increment)) / 2;
      
	while (sample_col < ncols) {
	    row_viewpt = floor (sample_row);
	    col_viewpt = floor (sample_col);

	    cell_no ++;
	  
	    if (patt_flag_v) {
	      value = (char*) &mask;
	      segment_get(seg_patt_p_v, value,
			  row_viewpt, col_viewpt);
	    } else 
	        mask = 1;

	    /* Only include if viewpoint is in area of interest */
	    if (mask) {
	      actual_cells ++;
	  
	      /* Read elevation of current view point */	      
	      /* value = (char*) &read_viewpt_elev; */
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
		    		count_visible_cells (cell_no, row_viewpt, col_viewpt, seg_out_1_p, seg_out_2_p,
		                         seg_patt_p, heads);
	        	else
		      		cumulate_visible_cells (cell_no, row_viewpt, col_viewpt, seg_out_1_p, seg_out_2_p,
		                              seg_patt_p, heads);
	      		delete_lists (heads);
	  	}

	  	/* Print progress report */
	  	if (! terse) {
		  G_percent (actual_cells, (int) actual_cells_to_sample, 1);
	  	}
	  }
	  sample_col += col_increment;
	} /* END (while (sample_col < ncols) */
	
    sample_row += row_increment;
  } /* END ( while (sample_row < nrows) ) */


  /* Calculate sample */
  actual_cells = actual_cells - null_count;
  if (absolute) {
  	*attempted_sample = actual_cells_to_sample;
  	*actual_sample = actual_cells;
  } else {
  	*attempted_sample = 100.0 / cells_in_map * actual_cells_to_sample;
  	*actual_sample = 100.0 / cells_in_map * actual_cells;
  }
}
