/***********************************************************************/
/*
  init_segment_file.c

  CONTAINS

  1) init_segment_file                                                 */

/***********************************************************************/

/***********************************************************************/
/*
  init_segment_file

  Called from:
  
  1) scan_all_cells     scan_all_cells.c
  2) systematic_sample  systematic_sample.c
  3) random_sample      random_sample.c
  4) point_sample       point_sample.c

  Calls:
 
  None                                                                 */

/***********************************************************************/

#include <grass/gis.h>
#include <grass/segment.h>

#include "global_vars.h"

void init_segment_file (int nrows, int ncols, SEGMENT *seg_to_init_p, 
			SEGMENT *seg_patt_p)
{
  int row, col;
  char *value;
  CELL data;

  value = (char*) &data;

  if (from_cells && patt_flag && (background == -1))
    {
      CELL data_read;
      char *value_to_get;
      
      value_to_get = (char*) &data_read;
      for (row = 0; row < nrows; row ++)
	{
	  for (col = 0; col < ncols; col ++)
	    {
	      segment_get (seg_patt_p, value_to_get,
			  row, col);
	      if (! data_read)
		data = background;
	      else
		data = 0;
	      segment_put (seg_to_init_p, value,
			   row, col);
	    }
	}
    }
  else
    {
      data = background;
      for (row = 0; row < nrows; row ++)
	{
	  for (col = 0; col < ncols; col ++)
	    {
	      segment_put (seg_to_init_p, value, row, col);
	    }
	}
    }
}
