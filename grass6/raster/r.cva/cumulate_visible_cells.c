/****************************************************************
 *      cumulate_visible_cells.c
 *
 *      Marks the cells visible from the current viewpoint
 *      by adding 1 to the values of visible cells on the 
 *      output segment file.  Writes the current viewpoint
 *      number to the temporary segment file to prevent
 *      cells which occur on more than one segment list from 
 *      being marked more than once for a given viewpoint.
 *      The end effect is to produce a map showing from how
 *      viewpoints a given cell can be seen.  Updates the 
 *      minimum and maximum number of visible cells.
  *
 ****************************************************************/

/* Written by Mark Lake on 1/3/96 to:-
 * 
 * 1) Cumulate the number of visible cells.
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 *
 * Modifications to r.los:-
 *
 * 1) r.los does not perform this function.
 *
 * Called by:-
 * 
 * Called by:
 * 
 * 1) scan_all_cells
 * 2) random_sample
 * 3) systematic_sample
 * 4) point_sample
 *
 * Calls:
 *
 * 1)  None.
 */

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "global_vars.h"

#include "point.h"

#define NEXT_SEARCH_PT  SEARCH_PT->next

void cumulate_visible_cells (CELL cell_no,
                             int row_viewpt, int col_viewpt,
                             SEGMENT  *seg_out_1_p, SEGMENT  *seg_out_2_p,
                             SEGMENT *seg_patt_p,
                             struct point *heads[])

/* struct point *heads[] is same as "struct point **heads" */

{
  int segment_no;
  int mask;
  char *value_read, *value_to_write;
  CELL visible_cells;
  CELL data_read, data_to_write;
  struct point *SEARCH_PT;  

  /* Count cells visible from current viewpoint */
  visible_cells = 0;
  value_read = (char*) &data_read;
  value_to_write = (char*) &data_to_write;
  mask = 1;
  
  for (segment_no = 1; segment_no <= 16; segment_no++) {
      SEARCH_PT = heads[segment_no-1];

#ifdef DEBUG
      printf ("\nCumulate_cells SEARCH_PT = %p", SEARCH_PT);
      fflush (stdout);
#endif

      while(SEARCH_PT != NULL) {
	    segment_get (seg_out_1_p, value_read,
		             row_viewpt - SEARCH_PT->y, 
		             col_viewpt + SEARCH_PT->x);
		/*   if not already counted or deleted */
	  	if (data_read < cell_no ) {
	      visible_cells++;	      

	      /* Add one to cell on output segment file  */
	      segment_get (seg_out_2_p, value_read,
			   row_viewpt - SEARCH_PT->y, 
			   col_viewpt + SEARCH_PT->x);
	      if (data_read == background) /* NULL value */
		    data_read = 0;
	      
		  data_to_write = data_read + 1;
	      segment_put (seg_out_2_p, value_to_write,
			   row_viewpt - SEARCH_PT->y, 
			   col_viewpt + SEARCH_PT->x);		  

	      /* Write cell_no to temporary segment file to show 
		     that cell has already been counted              */
	      data_to_write = cell_no;
	      segment_put (seg_out_1_p, value_to_write,
			   row_viewpt - SEARCH_PT->y, 
			   col_viewpt + SEARCH_PT->x);
	    }
	    SEARCH_PT = NEXT_SEARCH_PT;
	  }	    	  
  } /* END (iterate through segments */
  
  /* Include viewpoint itself if it is not a masked destination */
  if (patt_flag) {
      segment_get (seg_patt_p, value_read, row_viewpt, col_viewpt);
      mask = (int) data_read;
  }

  if (mask) {
      segment_get (seg_out_2_p, value_read, row_viewpt, col_viewpt);
      if (data_read == background)
	    data_read = 0; 
      
	  data_to_write = data_read + 1;
      segment_put (seg_out_2_p, value_to_write, row_viewpt, col_viewpt);	  
  }	
}
