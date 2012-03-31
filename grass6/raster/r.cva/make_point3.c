/****************************************************************/
/*								*/
/*	make_point3.c	                                	*/
/*								*/
/*	This function allocates memory space for a new point,	*/
/*	initializes the various fields using the values of	*/
/*	the parameters passed and returns the address of this	*/
/*	new point so that it can be attached in the linked	*/
/*	list.							*/
/*								*/
/****************************************************************/

/* Modified from r.los by Mark Lake on 14/12/95 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Create a new point on a segment list.
 *
 * Version 3.0, differs from v.1.0 as follows:-
 *
 * 1) Receives cell_no and uses it to determine whether or not 
 *    to initialise segment file with value 0.  Allows main3.c
 *    to count only those cells on a list which have the value 0.
 *    Since main3.c writes cell_no once a cell has been counted, 
 *    this ensures that cells which occur on more than one list 
 *    are counted only once.  If the segment file already contains
 *    the current cell_no then the cell has already been deleted
 *    during the current los analysis and should not be 
 *    reinitialised.
 *
 * Implicated files:-
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:-
 *
 * 1) Initialises segment file with value zero if not already
 *    deleted during the the current los analysis.  
 *
 * Called by:
 * 
 * 1) make_list
 *
 * Calls:
 *
 * 1)  None.
 */

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "point.h"
#define NULL_HERE 0

#define		NEW_PT_X		NEW_PT->x	
#define		NEW_PT_Y		NEW_PT->y
#define		NEW_PT_ORIENTATION	NEW_PT->orientation
#define		NEW_PT_INCLINATION	NEW_PT->inclination
#define		NEXT_NEW_PT		NEW_PT->next

struct point *make_point( double orientation, double inclination,
			  int y, int x, int row_viewpt, int col_viewpt, 
			  SEGMENT *seg_out_p, CELL cell_no)
{
    struct point *NEW_PT;
    CELL data_read, data_to_write;
    char *value_read, *value_to_write;
    
    NEW_PT = (struct point *) G_malloc(sizeof(struct point));
    NEW_PT_ORIENTATION = orientation;
    NEW_PT_INCLINATION = inclination;
    NEW_PT_Y           = y;
    NEW_PT_X           = x;
    NEXT_NEW_PT        = NULL_HERE;
    
    value_read = (char*) &data_read;
    value_to_write = (char*) &data_to_write;
    data_to_write = 0;
    segment_get (seg_out_p, value_read,
		 row_viewpt - y, x + col_viewpt);
    if (data_read != cell_no)
	segment_put (seg_out_p, value_to_write,
		     row_viewpt - y, x + col_viewpt);
    return(NEW_PT);
}

/********* END OF FUNCTION "MAKE_POINT" *************************/
