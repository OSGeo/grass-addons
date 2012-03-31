/****************************************************************
 *      count_visible_cells.c
 *
 *      Counts the number of cells visible from the current
 *      viewpoint, i.e. counts the number of cells on the 
 *      16 segment lists.  Writes the current viewpoint number
 *      to the temporary segment file after a cell has been 
 *      counted in order prevent cells which occur on more than
 *      one list from being counted more than once.  Writes the 
 *      number of visible cells to the output segment file
 *      and updates the minimum and maximum number of visible
 *      cells.
 *
 ****************************************************************/

/* Written by Mark Lake on 1/3/96 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Count the number of cells visible from the current
 *    viewpoint.
 *
 * Modifications to r.los:-
 *
 * 1) r.los does not perform this function.
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

#include <grass/segment.h>
#include <grass/gis.h>

#include "config.h"
#include "point.h"
#include "global_vars.h"

#define NEXT_SEARCH_PT  SEARCH_PT->next

void count_visible_cells (CELL cell_no, int row_viewpt, int col_viewpt,
			  SEGMENT *seg_out_1_p, SEGMENT *seg_out_2_p, 
                          SEGMENT *seg_patt_p, struct point *heads[])

/*     struct point *heads[] is same as "struct point **heads" */

{
  int segment_no;
  char *value_read, *value_to_write;
  CELL visible_cells;
  CELL data_read, data_to_write;
  struct point *SEARCH_PT;
  int mask;
  
  visible_cells = 0;
  value_read = (char*) &data_read;
  value_to_write = (char*) &data_to_write;
  mask = 1;
  

  /* Count cells visible from current viewpoint */

  for (segment_no = 1; segment_no <= 16; segment_no++)
    {
      data_to_write =  cell_no;
      SEARCH_PT = heads[segment_no-1];
      while(SEARCH_PT != NULL)
	{
	  segment_get (seg_out_1_p, value_read,
		       row_viewpt - SEARCH_PT->y, 
		       col_viewpt + SEARCH_PT->x);
	  if (data_read == 0) /*   if not already counted or deleted */
	    {
	      visible_cells++;
	      

	      /* Write cell_no to temporary segment file to show 
	         that cell has already been counted              */
	      
		segment_put (seg_out_1_p, value_to_write,
			     row_viewpt - SEARCH_PT->y, 
			     col_viewpt + SEARCH_PT->x);
	    }
	  SEARCH_PT = NEXT_SEARCH_PT;
	}
    }
  
  /* Include viewpoint itself if it is not a masked destination */

  if (patt_flag)
    {
      segment_get (seg_patt_p, value_read, row_viewpt, col_viewpt);
      mask = (int) data_read;
      if (mask)
	visible_cells += 1; /*   include viewpoint */
    }

  value_to_write = (char*) &visible_cells;
  segment_put (seg_out_2_p, value_to_write, row_viewpt, col_viewpt);
}    

