#include <math.h>
#include <stdio.h>

#include "structs.h"
#include "print.h"

void print_sample (Shypothesis *sample)
{
	Uint no_sets, i, j;
	
	no_sets = (Uint) pow((float) 2, (float)NO_SINGLETONS);
	fprintf (stderr,"\n");	
	/* print entire sample */
	for (i=0;i<no_sets;i++) {
		fprintf (stderr,"\tSAMPLE NR %i:\n",i);
		fprintf (stderr,"\t\tBPN: %1.2f\n",sample[i].bpn);
		fprintf (stderr,"\t\tBEL: %1.2f\n",sample[i].bel);
		fprintf (stderr,"\t\tPL: %1.2f\n",sample[i].pl);
		for (j=0;j<NO_SINGLETONS;j++) {
			fprintf (stderr," %i ",sample[i].type[j]);
		}		
		fprintf (stderr,"\n");
	}
}

/*=======================================================
  print the values contained in a frame of discernment
=======================================================*/
/* *frame points to the first set in the frame of discernment */
void print_frame(Shypothesis *frame, char **hyps)
{
	Uint set, type, no_of_sets;
	BOOL comma;
	
	comma = FALSE;
	no_of_sets = (Uint) pow((float) 2, (float) NO_SINGLETONS);
	
	/* now step through all subsets in the FOD, sequentially */
	for(set=0;set<no_of_sets;set++)
	{
		fprintf(lp, "{");			
		/* there is one 'type' entry for every singleton */
		/* that indicates whether a singleton is part */
		/* of the current subset */
		for(type=0;type<NO_SINGLETONS;type++) {
			if((frame[set].type[type] == TRUE) && (type == 0)) {
				fprintf (lp, "%s",hyps[type+1]);
				comma = TRUE;
			}				
			if((frame[set].type[type] == TRUE) && (type > 0) && (type < (NO_SINGLETONS-1))) {
				if(comma == TRUE) {
					fprintf(lp, ", %s",hyps[type+1]);
				} 
				else {
					fprintf(lp, "%s",hyps[type+1]);
					comma = TRUE;
				}
			}			
			if((frame[set].type[type] == TRUE) && (type == (NO_SINGLETONS-1))) {
				if(comma) {
					fprintf(lp, ", %s",hyps[type+1]);
				}
				else {
					fprintf(lp, "%s",hyps[type+1]);
				}
			}
		}		
		fprintf(lp, "}\n");
		fprintf(lp, "Bel %.3f Pl %.3f bpn %.3f common %.3f doubt %.3f BInt %.3f\n\n", 
				frame[set].bel, frame[set].pl, frame[set].bpn, frame[set].common,
				frame[set].doubt, frame[set].bint);
		comma = FALSE;
	}
}
