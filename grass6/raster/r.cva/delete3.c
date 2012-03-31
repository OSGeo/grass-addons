/****************************************************************/
/*								*/
/*	delete3.c	 	                                */
/*								*/
/*	This function detaches a point data structure from	*/
/*	the linked list and frees memory allocated for it.	*/
/*								*/
/****************************************************************/

/* Modified from r.los by MWL on 14/12/95 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Detach a point structure from the linked list.
 *
 * Version 3.0, differs from v.1.0 as follows:-
 *
 * 1) Recieves cell_no and writes to segment file at deleted point.
 *    This ensures that make_point3.c can differentiate between a
 *    point that has been deleted during the current los analysis,
 *    and one which was deleted or counted during los
 *    analysis from a preceeding viewpoint.
 *
 * Implicated files:-
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:-
 *
 * 1) Writes cell_no to seg_out_p instead of value 1.
 *
 * Called by:-
 * 
 * 1) hidden_point_elimination()
 *
 * Calls:-
 *
 * 1)  None. */

#include <stdlib.h>

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "point.h"

#define  PT_TO_DELETE_X		  PT_TO_DELETE->x
#define  PT_TO_DELETE_Y		  PT_TO_DELETE->y
#define  PT_NEXT_TO_DELETED	  PT_TO_DELETE->next	
#define  PT_PREVIOUS_TO_DELETED	  PT_TO_DELETE->previous
#define  NEXT_PT_BACK_PTR	  PT_TO_DELETE->next->previous
#define	 PREVIOUS_PT_NEXT_PTR     PT_TO_DELETE->previous->next	

struct point *delete(struct point *PT_TO_DELETE, struct point *head,
                     SEGMENT *seg_out_p, int row_viewpt, int col_viewpt,
                     CELL cell_no)
{
        CELL data;
        char *value;

        data = cell_no;
        value = (char *) &data;
        segment_put(seg_out_p,value,
	   row_viewpt-PT_TO_DELETE_Y,PT_TO_DELETE_X+col_viewpt);


	/* If first and last point.  This fixes a bug in r.los.
	   See pts_elim3.c for details */

        if((PT_TO_DELETE==head) && (PT_NEXT_TO_DELETED == NULL))   
        {
                head = PT_NEXT_TO_DELETED;
                free(PT_TO_DELETE); 
                return(head);
        }

        if(PT_TO_DELETE==head)   /*  first one ?  */
        {
                NEXT_PT_BACK_PTR = NULL;
                head = PT_NEXT_TO_DELETED;
                free(PT_TO_DELETE); 
                return(head);
        }


	/* If last point.  This fixes a bug in r.los.
	   See pts_elim3.c for details */

	if (PT_NEXT_TO_DELETED == NULL) 
	  {
	    PREVIOUS_PT_NEXT_PTR = PT_NEXT_TO_DELETED;
	    free(PT_TO_DELETE);
	    return (head);
	  }

	/*  otherwise  */
	
	NEXT_PT_BACK_PTR = PT_PREVIOUS_TO_DELETED;
	PREVIOUS_PT_NEXT_PTR = PT_NEXT_TO_DELETED;
	free(PT_TO_DELETE); 
	
	return(head);
    }

/************* END OF FUNCTION "DELETE" *************************/
