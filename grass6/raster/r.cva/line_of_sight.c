/***********************************************************************/
/*
  line_of_site.c
  
  Updated by Mark Lake on 17/8/01 for GRASS 5.x
 
  CONTAINS

  1) line_of_site                                                      */

/***********************************************************************/

/***********************************************************************/
/*
  line_of_site

  Called from:

  1) scan_all_cells     scan_all_cells.c
  2) random_sample      random_sample.c
  3) systematic_sample  systematic_sample.c
  4) point_sample       point_sample.c
  
  Calls:
  
  1)  segment()         segment3.c                                     */

/***********************************************************************/

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"    
#include "point.h"
#include "segment3.h"

void line_of_sight (CELL cell_no, int row_viewpt, int col_viewpt,
		    int nrows, int ncols, double viewpt_elev,
		    struct point *heads[],
            SEGMENT *seg_in_p, SEGMENT *seg_out_1_p, SEGMENT *seg_patt_p,
		    int patt_flag, RASTER_MAP_TYPE data_type)

     /* struct point *heads[] is same as "struct point **heads" */

{
  int a,b;
  int segment_no, flip, xmax, ymax, sign_on_y, sign_on_x;
  double slope_1, slope_2;
    
  /* Do los analysis from current viewpoint for 16 segments  */
  for(segment_no=1; segment_no<=16; segment_no++)
    {
      sign_on_y= 1- (segment_no-1)/8 * 2;
      if(segment_no>4 && segment_no<13)
	sign_on_x= -1; 
      else sign_on_x=1;
      

      /* Calc slopes for bounding rays of this segment */

      if(segment_no==1 || segment_no==4 || segment_no==5  ||
	 segment_no==8 || segment_no==9 || segment_no==12 ||
	 segment_no==13 || segment_no==16)
	{ 
	  slope_1= 0.0;      
	  slope_2= 0.5;
	}
      else
	{ 
	  slope_1= 0.5;      
	  slope_2= 1.0;
	}
      if(segment_no==1 || segment_no==2 || segment_no==7 || 
	 segment_no==8 || segment_no==9  || segment_no==10 || 
	 segment_no==15 || segment_no==16)
	flip = 0;
      else flip = 1;
	

      /* Calculate max and min 'x' and 'y' */

      a= ((ncols-1)*(sign_on_x+1)/2 - sign_on_x * col_viewpt);
      b= (1-sign_on_y)/2*(nrows-1) + sign_on_y*row_viewpt;
      if(flip==0)
	{
	  xmax=a; 
	  ymax=b;
	}
      else
	{ 
	  xmax=b; 
	  ymax=a;
	}
          
      /* Perform los analysis for this segment */
	  /* this function is in file 'segment3.c' */
      heads[segment_no-1] = segment(segment_no,xmax,ymax,
				   slope_1,slope_2,flip,sign_on_y,sign_on_x,
				   viewpt_elev,
	               seg_in_p,seg_out_1_p, seg_patt_p,
				   row_viewpt,col_viewpt,patt_flag,
				   cell_no, data_type);
    }
}
