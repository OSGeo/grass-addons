#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include "structs.h"
#include "sets.h"


/** are 2 sets the same? **/

BOOL set_equal(Shypothesis A, Shypothesis B)
{
	Uint type;
	
	for(type=0;type<NO_SINGLETONS;type++)
		if(A.type[type] != B.type[type])
		  	return 0;
	return 1;
}


/** return set index **/

Uint set_index(Shypothesis A, Shypothesis *frame)
{
	Uint no_of_sets, set;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	for(set=0;set<no_of_sets;set++)
		if(set_equal(A, frame[set]))
			return set;
	
	return 666;
}


/** A a subset of B? **/

BOOL subset(Shypothesis A, Shypothesis B)
{
	Uint type;
	
	for(type=0;type<NO_SINGLETONS;type++)
		if((A.type[type] == TRUE) && (B.type[type] == FALSE))
			return 0;
	
	return 1;
}


/**union of two sets **/
/* caller must free Shypothesis.type ! */

Shypothesis set_union(Shypothesis A, Shypothesis B)
{
	Uint type;
	Shypothesis union_set;

	union_set.type = (BOOL*) G_malloc((signed) (NO_SINGLETONS * sizeof(BOOL)));
	
	for(type=0;type<NO_SINGLETONS;type++)
		if((A.type[type] == TRUE) || (B.type[type] == TRUE))
			union_set.type[type] = TRUE;
		else
		union_set.type[type] = FALSE;
		
	return union_set;	
}

/** intersection of two sets **/
/* caller must free Shypothesis.type ! */

Shypothesis set_intersection(Shypothesis A, Shypothesis B)
{
	Uint type;
	Shypothesis intersection_set;
	
	intersection_set.type = (BOOL*) G_malloc((signed) (NO_SINGLETONS * sizeof(BOOL)));
	
	for(type=0;type<NO_SINGLETONS;type++)
		if((A.type[type] == TRUE) && (B.type[type] == TRUE))
			intersection_set.type[type] = TRUE;
		else
			intersection_set.type[type] = FALSE;
		
	return intersection_set;
}
