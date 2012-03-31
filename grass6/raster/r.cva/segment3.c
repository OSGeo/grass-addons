/****************************************************************/
/*								*/
/*	segment3.c	                                	*/
/*								*/
/*	This function picks up all the points in one segment	*/
/*	and performs los analysis on them.			*/
/*								*/
/****************************************************************/

/* Modified from r.los by MWL on 14/12/95 to:
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Return the head of a list of cells in the current
 *    segment that are visible from the current viewpoint.
 *
 * Version 3.0, differs from v.1.0 as follows:
 *
 * 1) Calls make_list.c version 3;
 * 2) Calls pts_elim.c version3;
 * 3) Recieves cell_no and passes it to make_list.c.
 *    and pts_elim.c.
 *
 * Implicated files:
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:
 *
 * 1) Recieves cell_no and passes it on to make_list.c
 *    and pts_elim.c.
 */

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "point.h"

#define  NULL_HERE  0

#define	  NEXT_PT		PRESENT_PT->next
#define	  NEXT_PT_BACK_PTR	PRESENT_PT->next->previous
#define	  HEAD_BACK_PTR		head->previous

struct point *segment(int segment_no, int xmax, int ymax,
		      double slope_1, double slope_2, 
		      int flip, int sign_on_y, int sign_on_x,
		      double viewpt_elev, 
		      SEGMENT *seg_in_p, SEGMENT *seg_out_p, SEGMENT *seg_patt_p, 
		      int row_viewpt, int col_viewpt, int patt_flag,
		      CELL cell_no, RASTER_MAP_TYPE data_type)
{
    int lower_limit_y ,upper_limit_y,less,x,y;
    int x_actual,y_actual,x_flip,y_flip;
    struct point *head = NULL_HERE, *PRESENT_PT, *make_list();
    int quadrant;
    struct point *hidden_point_elimination();
    
    /*   decide which one of the four quadrants	*/
    quadrant = 1 + (segment_no-1)/4;

#ifdef DEBUG
    printf ("\n Quadrant = %d", quadrant);
#endif

    if(slope_1 != 0){ less= ymax/slope_1 + 0.99;
		      xmax= (xmax<=less)?xmax:less;
		  }

    /*   outer loop over x coors for picking up points */

    for(x=xmax ; x > 0; x--)
    {
	
	/*   calculate limits for range of y for a single x */
        lower_limit_y = x * slope_1 + 0.9;
        upper_limit_y = x * slope_2 ;
        upper_limit_y = (upper_limit_y<=ymax)?upper_limit_y:ymax;
	
	/*   loop over y range to pick up correct points */
        for(y= upper_limit_y; y>= lower_limit_y ; y--)
        {
	/*   calculate actual x, y that lie in current segment */

	    if(flip==0) { x_flip = x; y_flip = y;}
	    else        { y_flip = x; x_flip = y;}
 
	    x_actual = sign_on_x*x_flip ;  
	    y_actual = sign_on_y*y_flip;
	    
	    
	    /*   add chosen point to the point list */
	    head = make_list(head,y_actual,x_actual,seg_in_p,seg_out_p,
			     viewpt_elev,quadrant,row_viewpt,col_viewpt,cell_no, data_type);
	}
    }  /*   end of outer loop */
 
    if(head != NULL_HERE)
    {
	/*   assign back pointers in linked list */
        HEAD_BACK_PTR = NULL_HERE;
	PRESENT_PT = head;
        while(NEXT_PT != NULL_HERE)
	{
	    NEXT_PT_BACK_PTR = PRESENT_PT;
	    PRESENT_PT = NEXT_PT;
        }
	head = hidden_point_elimination(head,viewpt_elev,
					seg_in_p,seg_out_p,seg_patt_p,quadrant,sign_on_y,
					sign_on_x,row_viewpt,col_viewpt,patt_flag,cell_no,
					data_type);
	}     

#ifdef DEBUG
    printf ("\nSegment, head = %p", head); fflush (stdout);        
#endif

    return(head);
    
} 

/**************** END OF FUNCTION "SEGMENT" *********************/
