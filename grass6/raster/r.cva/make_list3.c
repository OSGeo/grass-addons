/****************************************************************/
/*								*/
/*	make_list3.c                                       	*/
/*								*/
/*	This function adds a new point to the point list	*/
/*	for any segment of the map.				*/
/*								*/
/****************************************************************/	

/* Modified from r.los by Mark Lake on 14/12/95 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Add a new point to the list of cells that are 
 *    potentially visible from the current viewpoint, 
 *    i.e. which are within the maximum visible
 *    distance.
 *
 * Version 3.0, differs from v.1.0 as follows:-
 *
 * 1) Calls make_point.c version 3;
 * 2) Passes cell_no to make_point.c.
 *
 * Implicated files:-
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:-
 *
 * 1) Recieves cell_no and passes it on to make_point.c.
 *
 * Called by:
 * 
 * 1) segment
 *
 * Calls:
 *
 * 1) make_point
 * 2) find_orientation
 * 3) find_inclination 
 */

#include <stdlib.h>

#include <grass/segment.h>
#include <grass/gis.h>

#include "config.h"
#include "point.h"

#define		NEXT_PT		PRESENT_PT->next

struct point *make_list(struct point *head, int y, int x,
			SEGMENT *seg_in_p, SEGMENT *seg_out_p, 
			double viewpt_elev, int quadrant,
			int row_viewpt, int col_viewpt, CELL cell_no, 
			RASTER_MAP_TYPE data_type)
{
    double del_x,del_y,dist,sqrt(),orientation,inclination,
    find_orientation(), find_inclination();
    struct point *make_point();
    static struct point  *PRESENT_PT;
    extern struct Cell_head window;
    extern double AZIMUTH1;
    extern double AZIMUTH2;
    extern double VERT1;
    extern double VERT2;
    extern int AZIMUTH1_SET;
    extern int AZIMUTH2_SET;
    extern int VERT1_SET;
    extern int VERT2_SET;
    extern double max_dist;
    
    double v_angle, h_angle;
  
    del_x= abs(x)  ;
    del_y= abs(y)  ;
    
    dist = sqrt(del_x*del_x +del_y*del_y) * window.ns_res;
    
    /* if distance from viewpt is greater than the max	*/
    /* range specified, neglect that point			*/
    if (dist > max_dist) {
	  return(head);
    }
    
    /* otherwise find orientation and inclination		*/
    orientation = find_orientation(x,y,quadrant);
    inclination = find_inclination(x,y,viewpt_elev,seg_in_p,
				   row_viewpt,col_viewpt, data_type);
    
    /* check, if limits are imposed on orientation and inclination */
    if ( AZIMUTH1_SET ) {
        h_angle = orientation * (180.0 / 3.14159265359);
	h_angle = 360 - h_angle;
	h_angle = h_angle + 90;
	if (h_angle > 360) {
		h_angle = h_angle - 360;
	}
    	if (h_angle < AZIMUTH1) {
		return (head);
	}
    }
    if ( AZIMUTH2_SET ) {
        h_angle = orientation * (180.0 / 3.14159265359);
	h_angle = 360 - h_angle;
	h_angle = h_angle + 90;
	if (h_angle > 360) {
		h_angle = h_angle - 360;
	}
   	if (h_angle > AZIMUTH2) {
		return (head);
	}    
    }
    if ( VERT1_SET ) {
    	v_angle = inclination * (180.0 / 3.14159265359);
	if (v_angle > VERT1) {
		return (head);
	}
    }
    if ( VERT2_SET ) {
    	v_angle = inclination * (180.0 / 3.14159265359);
	if (v_angle < VERT2) {
		return (head);
	}	
    }
    
        
#ifdef DEBUG
    printf ("\nlist y = %d, x = %d", y, x);
#endif

    if(head == NULL)	
    {  			    /* 	first point ? 		*/
	head= make_point(orientation,inclination,y,x,
			 row_viewpt,col_viewpt,seg_out_p,cell_no);
	PRESENT_PT = head;
    }
    else 
    {	/*	add new point to tail of list		*/
	NEXT_PT = make_point(orientation,inclination,y,x,
			     row_viewpt,col_viewpt,seg_out_p,cell_no);
        PRESENT_PT = NEXT_PT ;
    }
    return(head);
    
}  

/********** END OF FUNCTION "MAKE_LIST" *************************/
