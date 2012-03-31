/****************************************************************/
/*								*/
/*	pts_elim3.c 	                                	*/
/*								*/
/*	This function prunes a linked list of all points 	*/
/*	picked up from a map segment to leave only those	*/
/*	points in the list that are visible from the viewpt.	*/
/*								*/
/****************************************************************/

/* Modified from r.los by Mark Lake on 14/12/95 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Eliminate invisible cells from a segment list.
 *
 * Version 3.0, differs from v.1.0 as follows:-
 *
 * 1) Calls delete.c version 3;
 * 2) Receives cell_no and passes it to delete.c.
 *
 * Implicated files:-
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:-
 *
 * 1) Recieves cell_no and passes it on to delete.c.
 *
 * Called by:
 * 
 * 1) segment
 *
 * Calls:
 *
 * 1) find_orientation
 * 2) find_inclination
 * 3) delete
 */

#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "pts_elim3.h"
#include "point.h"
#include "radians.h"
#include "global_vars.h"

#define	  SECOND_PT			head->next

#define   NEXT_BLOCKING_PT		BLOCKING_PT->next
#define   BLOCKING_PT_X	 		BLOCKING_PT->x
#define   BLOCKING_PT_Y			BLOCKING_PT->y   
#define   BLOCKING_PT_INCLINATION 	BLOCKING_PT->inclination
#define   BLOCKING_PT_ORIENTATION	BLOCKING_PT->orientation

#define   NEXT_CHECKED_PT		CHECKED_PT->next
#define	  CHECKED_PT_X			CHECKED_PT->x
#define	  CHECKED_PT_Y			CHECKED_PT->y
#define	  CHECKED_PT_INCLINATION	CHECKED_PT->inclination
#define   CHECKED_PT_ORIENTATION	CHECKED_PT->orientation


/****************************************************************/
/*								*/
/*	This function takes a linked list of points picked	*/
/*	up from a segment of the map and deletes all the points	*/
/*	from the list that are not visible from the viewing pt.	*/
/*								*/
/****************************************************************/

struct point *hidden_point_elimination (struct point *head,
					double viewpt_elev,
					SEGMENT *seg_in_p,
					SEGMENT *seg_out_p,
					SEGMENT *seg_patt_p, 
					int quadrant, 
					int sign_on_y, int sign_on_x, 
					int row_viewpt, int col_viewpt,
					int patt_flag, CELL cell_no,
					RASTER_MAP_TYPE data_type)
{
    struct point *CHECKED_PT, *BLOCKING_PT, *delete();
    double orientation_neighbor_1,orientation_neighbor_2,
    find_orientation(),inclination_neighbor_1,
    inclination_neighbor_2,interpolated_inclination,
    find_inclination(),find_inclination2(),correct_neighbor_inclination,
    correct_neighbor_orientation,fabs();
    int correct_neighbor_x,correct_neighbor_y,neighbor_1_y,
    neighbor_1_x,neighbor_2_x,neighbor_2_y, uu,vv;
    CELL mask;
    char *value;
    int do_check = 1;
    extern double RADIUS1;
    extern int OFFSETB_SET;
    double del_x, del_y,dist,atan(),sqrt();


    uu = (sign_on_y + sign_on_x)/2;
    vv = (sign_on_y - sign_on_x)/2;
    
    value = (char *) &mask;
    
    
#ifdef DEBUG
    printf ("\nrow = %d, col = %d", row_viewpt, col_viewpt);
    fflush (stdout);
#endif

    /*   move blocking pt. from the 2nd pt till the end	*/
    for(BLOCKING_PT  = SECOND_PT; 
	BLOCKING_PT != NULL; 
	BLOCKING_PT  = NEXT_BLOCKING_PT)
    {

#ifdef DEBUG
      printf ("\nBlocking point y = %d, x = %d", 
	      BLOCKING_PT_Y, BLOCKING_PT_X);
      fflush (stdout);
#endif

	/*   calc coors of the two immediate neighbors on either  */
	/*   side of the blocking point                           */

	if(BLOCKING_PT_X == 0 || BLOCKING_PT_Y == 0)
	{
	    neighbor_1_x = BLOCKING_PT_X - vv;
	    neighbor_1_y = BLOCKING_PT_Y + uu;
	    
	    neighbor_2_x = BLOCKING_PT_X + uu;
	    neighbor_2_y = BLOCKING_PT_Y + vv;
	}
	else
	{
	    neighbor_1_x = BLOCKING_PT_X - uu;
	    neighbor_1_y = BLOCKING_PT_Y - vv;
	    
	    neighbor_2_x = BLOCKING_PT_X + vv;
	    neighbor_2_y = BLOCKING_PT_Y - uu;
	}
	
	/*   find orientation and inclination for both neighbors	*/
	orientation_neighbor_1 = 
	    find_orientation(neighbor_1_x,neighbor_1_y,quadrant);
	
	orientation_neighbor_2 = 
	    find_orientation(neighbor_2_x,neighbor_2_y,quadrant);

	inclination_neighbor_1 = 
	    find_inclination(neighbor_1_x,neighbor_1_y,viewpt_elev,
			     seg_in_p,row_viewpt,col_viewpt, data_type);
	
	inclination_neighbor_2 = 
	    find_inclination(neighbor_2_x,neighbor_2_y,viewpt_elev,
			     seg_in_p,row_viewpt,col_viewpt, data_type);

	/*   check all points behind the blocking point		*/
	for(CHECKED_PT  = head;
	    CHECKED_PT != BLOCKING_PT;
	    CHECKED_PT  = NEXT_CHECKED_PT)
	{
	    
#ifdef DEBUG
	  printf ("\nChecked point y = %d, x = %d",
		  CHECKED_PT_Y, CHECKED_PT_X);
	  fflush (stdout);
#endif

		
	    /*   if pattern layer specified, check to see if checked	*/
	    /*   point is of interest. If not, delete it from list	*/
	    if(patt_flag == 1)
	    {
		segment_get(seg_patt_p,value,
			    row_viewpt-CHECKED_PT_Y,col_viewpt+CHECKED_PT_X);
		
		if(mask == 0)
		{
		    head=delete(CHECKED_PT,head,seg_out_p,
				row_viewpt,col_viewpt,cell_no);
		    goto next_iter;
		}
	    }

	    /* if the OFFSETB parameter is set, we will raise the height of only the
	       target point under consideration, leaving all blocking points the
	       way they are. This improves visibility of current target point and
	       simulates an object of a known height */
	    if (OFFSETB_SET) {
	    	CHECKED_PT_INCLINATION = find_inclination2(CHECKED_PT_X,CHECKED_PT_Y,viewpt_elev,
			     seg_in_p,row_viewpt,col_viewpt, data_type);
	    }
	    
	    do_check = 1;

	    /* no need to check if this condition holds true */
	    if(BLOCKING_PT_INCLINATION <= CHECKED_PT_INCLINATION) {
	       do_check = 0;
	    } 
	    if (BLOCKING_PT_INCLINATION == NULLPT) {
	       do_check = 0;
	    }
	    
            /* delete this point, if it lies closer than the minimum distance */
	    del_x = abs(CHECKED_PT_X);
    	    del_y = abs(CHECKED_PT_Y);
    	    dist=sqrt(del_x * del_x + del_y * del_y)*window.ns_res;
	    if ( dist < RADIUS1) {
		head= delete(CHECKED_PT,head,seg_out_p,row_viewpt,col_viewpt,cell_no);		   
		   do_check = 0;
	    }
	
	    if (do_check == 1)
	    
	    {  	/*   otherwise, proceed to check */


		if(CHECKED_PT_ORIENTATION == BLOCKING_PT_ORIENTATION)
		{
		    head= delete(CHECKED_PT,head,seg_out_p,
				 row_viewpt,col_viewpt,cell_no);
		/*   if checked point directly behind, delete it */
		}
		else
		{	/*   if checked point not directly behind, check */
		    
		    /*   find the coors of the actual neighbor that might be  */
		    /*   required for interpolation.			      */
		    if(CHECKED_PT_ORIENTATION > BLOCKING_PT_ORIENTATION)
		    {
			correct_neighbor_x = neighbor_1_x;
			correct_neighbor_y = neighbor_1_y;
			correct_neighbor_inclination = inclination_neighbor_1;
			correct_neighbor_orientation = orientation_neighbor_1;
		    }
		    else
		    {
			correct_neighbor_x = neighbor_2_x;
			correct_neighbor_y = neighbor_2_y;
			correct_neighbor_inclination = inclination_neighbor_2;
			correct_neighbor_orientation = orientation_neighbor_2;
		    }
		    
		    if(fabs(BLOCKING_PT_ORIENTATION-CHECKED_PT_ORIENTATION) < 
		       fabs(BLOCKING_PT_ORIENTATION-correct_neighbor_orientation))
			
		    { /*   yes, the point neighboring the blocking point */
		      /*    must be taken into consideration		 */

			if(CHECKED_PT_Y == correct_neighbor_y && 
			   CHECKED_PT_X == correct_neighbor_x);	/*   same point */

			else
			{     /*   CHECK !! */
			    
			    
			    /*   if the checked point's inclination is even lower  */
			    /*   than that of the blocking pt.'s neighbor, blocked */
			    if(CHECKED_PT_INCLINATION < correct_neighbor_inclination)
			    {
				head= delete(CHECKED_PT,head,seg_out_p,
					     row_viewpt,col_viewpt,cell_no);
			    }
			    
			    else
			    {	/*   INTERPOLATION */

				
				interpolated_inclination= BLOCKING_PT_INCLINATION + 
				    (CHECKED_PT_ORIENTATION - BLOCKING_PT_ORIENTATION)/
					(correct_neighbor_orientation-BLOCKING_PT_ORIENTATION)*
					    (correct_neighbor_inclination - BLOCKING_PT_INCLINATION);
				
				if(CHECKED_PT_INCLINATION < interpolated_inclination)
				{	/*   interpolated point blocks */
				    head= delete(CHECKED_PT,head,seg_out_p,
						 row_viewpt,col_viewpt,cell_no);
				}
			    }
			}
		    }
		}
	    }
	  next_iter: 
	    ;
	}       /*   end of loop over points to be checked */




	/*   if pattern layer specified, check if blocking point */
	/*   itself is an area of interest. If not, of no use	 */
	if(patt_flag == 1)
	{
	    segment_get(seg_patt_p, value,row_viewpt- BLOCKING_PT_Y,
			col_viewpt+BLOCKING_PT_X);
	    if(mask == 0)
	    {

	      /* Commenting out the following fixes a bug in r.los.
		 In that program the 8 cells around the viewpoint
		 are marked as visible (when visible)
		 even if they fall outside the area of interest 
		 specified by the patt_map.  This occurs because
		 these cells are always the last blocking points
		 on the segment lists, and therefore don't get 
		 deleted when they should.  This fix allows them
		 to be deleted, but it required modifications
		 to delete, in delete3.c.  MWL 25/6/99 */
		 
	      /* if (NEXT_BLOCKING_PT != NULL) */

	      head = delete(BLOCKING_PT, head, seg_out_p,
				  row_viewpt, col_viewpt,cell_no);

	    }
	}

    }       /*   end of loop over blocking points */
    
    return(head);
    
}

/*********** END OF FUNCTION "HIDDEN_POINT_ELIMINATION" *********/

/* Called by:-
 *
 * 1) make_list()
 * 2) hidden_point_elimination()
 *
 * Calls:-
 * 
 * 1) None.
 */


/****************************************************************/
/*								*/
/*	This function finds the orientation of a point if	*/
/*	provided with the number of the quadrant and the	*/
/*	coordinates of that point.				*/
/*								*/
/****************************************************************/

double find_orientation(int x, int y, int quadrant)
{
    double del_x,del_y,atan(),angle;
    int abs();
	
    del_x = abs(x) ;
    del_y = abs(y);
    
    if(del_x == 0.0) angle = PIBYTWO;
    else	angle = atan(del_y/del_x) ;
    
    switch(quadrant)
    {
      case 1 : 
	  break;
	case 2 : 
	    angle = PI - angle; 
	  break;
	case 3 : 
	    angle = PI + angle; 
	  break;
	case 4 : 
	    angle = TWOPI - angle; 
	  break;
	default : 
	    break;
      }
    
    return(angle);
    
}       /* END OF FUNCTION ANGLE */

/************* END OF FUNCTION "FIND_ORIENTATION" ***************/

/* Called by:-
 *
 * 1) make_list()
 * 2) hidden_point_elimination()
 *
 * Calls:-
 * 
 * 1) None.
 */

/****************************************************************/
/*								*/
/*	This function calculates the vertical angle of a point	*/
/*	with respect to the viewing pt.				*/
/*								*/
/****************************************************************/

double find_inclination(int x, int y, double viewpt_elev, 
			SEGMENT *seg_in_p,
			int row_viewpt, int col_viewpt, RASTER_MAP_TYPE data_type)
{
    double del_x, del_y,dist,atan(),sqrt();
    int abs();
    double dest_elev = 0.0;
    extern struct Cell_head window;
    void *value = NULL;	
	/* these vars can store one data value from the elevation input map, */
	/* which could be CELL, DCELL or FCELL type. */
    CELL c_value;
    FCELL f_value;
    DCELL d_value;
    
    del_x = abs(x) ;
    del_y = abs(y) ;
        
    dist=sqrt(del_x * del_x + del_y * del_y)*window.ns_res;
    
    	/* this takes care, that target elevation has the right format, 
	   depending on type of input DEM */
    	
	if (data_type == CELL_TYPE) {
		value = (CELL*) &c_value;
	}
	if (data_type == FCELL_TYPE) {
		value = (FCELL*) &f_value;
	}
	if (data_type == DCELL_TYPE) {
		value = (DCELL*) &d_value;
	}
	
    /* read value from elevation input map, convert to appropriate */
	/* map type */
    segment_get(seg_in_p,value,row_viewpt-y,x+col_viewpt);

	if (data_type == CELL_TYPE) {	
	  if ( G_is_c_null_value (&c_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = c_value;
	  }
	}

	if (data_type == FCELL_TYPE) {
	  if ( G_is_f_null_value (&f_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = f_value;
	  }
	}

	if (data_type == DCELL_TYPE) {
	  if ( G_is_d_null_value (&d_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = d_value;	
	  }
	}

	/* CURVATURE CORRECTION */
	/* decrease height of target point */
	if (DIST_CC > 0.0) {
		if (dist >= DIST_CC) {
			dest_elev = dest_elev - ((dist*dist) / (2 * Re));
		}
	}
		
        	
    return(atan((dest_elev - viewpt_elev) / dist));
}


/* THIS IS CALLED IF ONLY THE TARGET POINT UNDER CURRENT CONSIDERATION IS TO
   BE RAISED BY 'OFFSETB' AMOUNT */
double find_inclination2(int x, int y, double viewpt_elev, 
			SEGMENT *seg_in_p,
			int row_viewpt, int col_viewpt, RASTER_MAP_TYPE data_type)
{
    double del_x, del_y,dist,atan(),sqrt();
    int abs();
    double dest_elev = 0.0;
    extern struct Cell_head window;
    void *value = NULL;	
	/* these vars can store one data value from the elevation input map, */
	/* which could be CELL, DCELL or FCELL type. */
    CELL c_value;
    FCELL f_value;
    DCELL d_value;
    
    del_x = abs(x) ;
    del_y = abs(y) ;
        
    dist=sqrt(del_x * del_x + del_y * del_y)*window.ns_res;
    
    	/* this takes care, that target elevation has the right format, 
	   depending on type of input DEM */
    	
	if (data_type == CELL_TYPE) {
		value = (CELL*) &c_value;
	}
	if (data_type == FCELL_TYPE) {
		value = (FCELL*) &f_value;
	}
	if (data_type == DCELL_TYPE) {
		value = (DCELL*) &d_value;
	}
	
    /* read value from elevation input map, convert to appropriate */
	/* map type */
    segment_get(seg_in_p,value,row_viewpt-y,x+col_viewpt);

	if (data_type == CELL_TYPE) {	
	  if ( G_is_c_null_value (&c_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = c_value + OFFSETB;
	  }
	}

	if (data_type == FCELL_TYPE) {
	  if ( G_is_f_null_value (&f_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = f_value + OFFSETB;
	  }
	}

	if (data_type == DCELL_TYPE) {
	  if ( G_is_d_null_value (&d_value) ) {
	  	return (NULLPT);
	  } else {
	  	dest_elev = d_value + OFFSETB;	
	  }
	}


	/* CURVATURE CORRECTION */
	/* decrease height of target point */
	if (DIST_CC > 0.0) {
		if (dist >= DIST_CC) {
			dest_elev = dest_elev - ((dist*dist) / (2 * Re));
		}
	}
        	
    return(atan((dest_elev - viewpt_elev) / dist));
}

/************ END OF FUNCTION "FIND_INCLINATION"*****************/
