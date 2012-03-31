/****************************************************************/
/*								*/
/*	delete_list.c	                                        */
/*								*/
/*	This function frees the memory used in a segment list.	*/
/*								*/
/****************************************************************/

/* Modified from r.los by MWL on 14/12/95 to:-
 * 
 * Updated by Mark Lake on 17/8/01 for GRASS 5.x
 * 
 * 1) Free the memory used in a single segment list.
 *
 * Implicated files:-
 *
 * 1) See main3.c.
 *
 * Modifications to r.los:-
 *
 * 1) r.los does not perform this function.
 *
 * Called by:-
 * 
 * 1) delete_lists()
 *
 * Calls:-
 *
 * 1)  None. */

#include <stdlib.h>

#include <grass/gis.h>
#include <grass/segment.h>

#include "config.h"
#include "point.h"


#define  PT_NEXT_TO_DELETED	  PT_TO_DELETE->next	
#define  PT_PREVIOUS_TO_DELETED	  PT_TO_DELETE->previous
#define  NEXT_PT_BACK_PTR	  PT_TO_DELETE->next->previous
#define	 PREVIOUS_PT_NEXT_PTR     PT_TO_DELETE->previous->next	

void delete_one_list (struct point *head)
{
    struct point *PT_TO_DELETE;

/*    PT_TO_DELETE = head;
    while (PT_TO_DELETE != NULL)
    {
	printf ("\nPOINT = %d ", PT_TO_DELETE); fflush (stdout);
	PT_TO_DELETE = PT_NEXT_TO_DELETED;
    }*/

    PT_TO_DELETE = head;
    while (PT_TO_DELETE != NULL)
    {
/*printf ("\nPT_TO_DELETE = %d ", PT_TO_DELETE); fflush (stdout);*/
        if (PT_NEXT_TO_DELETED != NULL)
	    NEXT_PT_BACK_PTR = NULL;
/*printf ("\nPT_NEXT = %d ", PT_NEXT_TO_DELETED); fflush (stdout);*/
	head = PT_NEXT_TO_DELETED;
	free(PT_TO_DELETE);
/*printf ("\nDELETED");*/
	PT_TO_DELETE = head;
    }
}
    
/************* END OF FUNCTION "DELETE_LIST" *************************/

