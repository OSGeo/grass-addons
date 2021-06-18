#include <stdlib.h>
#include <stdio.h>
#include <math.h>

#include "structs.h"
#include "dst.h"
#include "print.h"
#include "sets.h"
#include "garbage.h"

int times_called = 0;

/* the following functions retrieve DST values from a frame */
/* hyp is an index from 0 to no_sets-1 */
double get_bel (Shypothesis *frame, int hyp) {
	return (frame[hyp].bel);
}

double get_pl (Shypothesis *frame, int hyp) {
	return (frame[hyp].pl);
}

double get_bint (Shypothesis *frame, int hyp) {
	return (frame[hyp].bint);
}

double get_doubt (Shypothesis *frame, int hyp) {
	return (frame[hyp].doubt);
}

double get_common (Shypothesis *frame, int hyp) {
	return (frame[hyp].common);
}

double get_bpn (Shypothesis *frame, int hyp) {
	return (frame[hyp].bpn);
}

double get_minbpn (Shypothesis *frame, int hyp) {
	return (frame[hyp].minbpn);
}

double get_maxbpn (Shypothesis *frame, int hyp) {
	return (frame[hyp].maxbpn);
}

int get_minbpnev (Shypothesis *frame, int hyp) {
	return (frame[hyp].minbpnev);
}

int get_maxbpnev (Shypothesis *frame, int hyp) {
	return (frame[hyp].maxbpnev);
}

int get_isNull (Shypothesis *frame, int hyp) {
	return (frame[hyp].isNull);
}




/*=====================================================
  combine 2 sets of evidence (frames of discernment
  memory of original frames is NOT free'd
=====================================================*/
/* returns the Weight of Conflict */
/* WOC is a measure of agreement between to frames */
/* the closer it is to 0, the less disagreement of evidence */
/* there is. */
double combine_bpn(Shypothesis *frame1, Shypothesis *frame2, BOOL **garbage, int MODE)
{
	Uint A, B, C, no_of_sets, i;
	double empty_set_bpn;
	Shypothesis *combined_frames;
	Shypothesis intersectionSet;
	double woc;
	struct Cell_head region;	
		
	G_get_window (&region);			
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	/** set up the initial frame of discernment **/
	combined_frames = frame_discernment( garbage );
	
	for(A=0; A<no_of_sets; A++) /** check that frames are combinable **/			
		for(B=0; B<no_of_sets; B++)
			for(C=0; C<no_of_sets; C++) {
				intersectionSet = set_intersection(frame1[B], frame2[C]);
				if(set_equal(intersectionSet, combined_frames[A])) {
					combined_frames[A].bpn += (frame1[B].bpn * frame2[C].bpn);					
				}					
				G_free (intersectionSet.type);
			}
				
	if(combined_frames[0].bpn >= 1) 
	{
		if ( MODE == CONST_MODE ) {
			G_warning ("Sets do not combine to < 1 (%.5f).\n",combined_frames[0].bpn);	
		}
		if ( MODE == RAST_MODE ) {
			G_warning ("Sets do not combine to < 1 (%.5f) at %.2f, %.2f.\n",
						combined_frames[0].bpn,
						G_col_to_easting ((double) ReadX,&region),
						G_row_to_northing ((double) ReadY,&region));
			fprintf (lp,"%.2f\t%.2f\tWARNING %i: Sets do not combine to < 1 (%.5f)\n",												
						G_col_to_easting ((double) ReadX,&region),
						G_row_to_northing ((double) ReadY,&region),
						WARN_NOT_ONE,
						combined_frames[0].bpn );
			if ( warn != NULL ) {
				/* user wants to store coordinates of problems in a site file */
			}				
		}
	}
	
	/** weight by the empty set total **/ 
	/* the weighting measure (1-empty set)  shows how much conflict */
	/* there is between the pieces of evidence */ 	
	empty_set_bpn = combined_frames[0].bpn;
	/* woc = fabs (log10 (1-empty_set_bpn)); */
	
	for(A=0; A<no_of_sets; A++)
		combined_frames[A].bpn /= (1 - empty_set_bpn); /** empty set is at [0] **/
	
	/** This way is easier for combining (this func) lots of data sets within a loop **/
	/** if you want to change it just return the 'combined_frames' and don't free, obviously **/
	for(i=0;i<no_of_sets;i++) /** swap the combined set back to frame1 of the arg **/
		frame1[i] =  combined_frames[i];
	/** empty_set_bpn is the weight of conflict 'k' **/
	woc = (empty_set_bpn);
	/** reset the empty set to 0 so it doesn't go into the next one when the func is called in loops**/	
	frame1[0].bpn = 0; 			
	
	G_free (combined_frames);
	
	/* UPDATE GLOBAL MIN AND MAX */
	if (woc > WOC_MAX) {
		WOC_MAX=woc;
	}
	if (woc < WOC_MIN) {
		WOC_MIN=woc;
	}
	
	return (woc);
}

/*===========================================================
  set the beliefs in a frame of discernment from the bpn's
===========================================================*/
/* Calculate Belief value */

void set_beliefs(Shypothesis *frame)
{
	Uint B, no_of_sets, A;
	double *temp;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);

	/** sets all to zero **/
	temp = (double*) G_calloc ((unsigned) no_of_sets, sizeof(double));
	
	for(A=0; A<no_of_sets; A++)
		for(B=0; B<no_of_sets; B++) /** empty set is always first in frame of discernment **/
			if(subset(frame[B], frame[A]))
				temp[A] += frame[B].bpn;
	
	/** swap values to the frame **/
	for(A=0; A<no_of_sets; A++)
		frame[A].bel = temp[A];
		
	G_free(temp);
}

/* calculate commonality */
/*	commonality(A) = summed bpns for all (subset (A,B))  */
void set_commonalities (Shypothesis *frame)
{
	Uint B, no_of_sets, A;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
		
	for(A=0; A<no_of_sets; A++)
		for(B=0; B<no_of_sets; B++) /** empty set is always first in frame of discernment **/
			if(subset(frame[B], frame[A]))
				frame[B].common += frame[A].bpn;
}

/* calculate Belief Interval */
/* This acts as a measure of uncertainty ! */
/* Bel and Pl have to be calculated prior to calculating BInt */
void set_bint (Shypothesis *frame)
{
	Uint B, no_of_sets, A;
	
	B = 0;
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
		
	for(A=0; A<no_of_sets; A++)
		for(B=0; B<no_of_sets; B++) /** empty set is always first in frame of discernment **/
			frame[B].bint = fabs (frame[B].pl - frame[B].bel);
			
}

/*===================================================================
  set the plausibilities in the frame of discernment from the bpn's
===================================================================*/

void set_plausibilities(Shypothesis *frame)
{
	Uint B, no_of_sets, A;
	double *temp;
	Shypothesis emptySet;
	Shypothesis intersectionSet;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	temp = (double*) G_calloc ((unsigned) no_of_sets, sizeof(double));
	
	emptySet = empty_set();	
	
	for(A=0; A<no_of_sets; A++)
		for(B=0; B<no_of_sets; B++) {
			intersectionSet = set_intersection(frame[B], frame[A]);
			if(!set_equal(intersectionSet, emptySet))
				temp[A] += frame[B].bpn;
			G_free (intersectionSet.type);
		}			
	
	/** swap values to the frame **/
	for(A=0; A<no_of_sets; A++)
		frame[A].pl = fabs (temp[A]);
	
	
	G_free (emptySet.type);	
	G_free(temp);
}

/* calculate commonality */
/* doubt(A) = 1-Pl(A) */
void set_doubts (Shypothesis *frame)
{
	Uint B, no_of_sets, A;
	double *temp;
	Shypothesis emptySet;
	Shypothesis intersectionSet;	
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
		
	temp = (double*) G_calloc ((unsigned) no_of_sets, sizeof(double));
	
	emptySet = empty_set();
	
	for(A=0; A<no_of_sets; A++)
		for(B=0; B<no_of_sets; B++) {
			intersectionSet = set_intersection(frame[B], frame[A]);
			if(!set_equal(intersectionSet, emptySet))
				temp[A] += frame[B].bpn;
			G_free (intersectionSet.type);
		}			
	
	/** swap values to the frame **/
	for(A=0; A<no_of_sets; A++)
		frame[A].doubt = fabs (1-temp[A]);
	
	G_free (emptySet.type);	
	G_free(temp);
}


/*==============================================================
 total the bpns in a frame of discernment, for error checking
==============================================================*/

double get_bpn_sum(Shypothesis *frame)
{
	Uint set, no_of_sets;
	double bpn_total=0;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	for(set=0;set<no_of_sets; set++)
		bpn_total += frame[set].bpn;
		
	return( fabs (bpn_total) );	
}


/*=====================================================================
  create a frame of discernment given the no of singleton hypothesis.
  relate to types in def.h
  Memory must be free'd by caller!
=====================================================================*/

Shypothesis* frame_discernment( BOOL **garbage )
{	
	Shypothesis *frame;
	Uint x, no_of_sets, set, i;
	Ushort *counter;
	long offset, max_offset;
	
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	offset = no_of_sets * times_called;
	max_offset = N+(N-1);
	times_called ++;
	if (times_called == max_offset ) {
		times_called = 0;
	}
	
	frame = (Shypothesis*) G_malloc ((unsigned) no_of_sets * (signed) sizeof(Shypothesis));
	counter = (Ushort*) G_malloc ((unsigned) NO_SINGLETONS * (signed) sizeof(Ushort));
		
	/** init counter array */
	for(x=0;x<NO_SINGLETONS;x++)
		counter[x] = TRUE;
		
	for(set=0;set<no_of_sets;set++)
	{
		/* set the binary states in the counter representing the on/off 
		of each type in the hypothesis */	
		for(x=0;x<NO_SINGLETONS;x++) 
		{
			if(counter[x] == FALSE)
			{
				counter[x] = TRUE;
				break;
			}
			else
				counter[x] = FALSE;
		}		
		/* transfer the binary states to the frame of discernment, and 
		init values */
		frame[set].type = (BOOL*) G_malloc((unsigned) NO_SINGLETONS * (signed) sizeof(BOOL));
		for(i=0;i<NO_SINGLETONS;i++) {
			frame[set].type[i] = counter[i];
 		}
		/* keep pointers in a BOOL array to free later */				
		garbage_throw (garbage, (signed)offset + (signed) set, frame[set].type);
			
		no_assigns ++;
		frame[set].pl = 0;
		frame[set].bel = 0;
		frame[set].bpn = 0;
		frame[set].common = 0;
		frame[set].doubt = 0;
	}	
	G_free(counter);	
	
	return frame;
}


/** return an empty set **/
Shypothesis empty_set(void)
{
	Shypothesis empty_set;
	int i;
	
	empty_set.type = (BOOL*) G_malloc((unsigned) NO_SINGLETONS * (signed) sizeof(BOOL));
	for ( i = 0; i < NO_SINGLETONS; i++)
		empty_set.type[i] = FALSE;
	return empty_set;
}
