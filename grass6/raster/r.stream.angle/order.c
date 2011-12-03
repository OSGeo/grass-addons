#include <stdio.h>
#include <stdlib.h>
#include <grass/glocale.h>
#include "global.h"

int strahler(void)
{
    int i, j, done = 1;
    int cur_stream, next_stream;
    int max_strahler = 0, max_strahler_num;

    G_message("Calculating Strahler's stream order ...");

    for (j = 0; j < springs_num; ++j) {	/* main loop on springs */

	cur_stream = s_streams[springs[j]].stream;
	do {			/* we must go at least once, if stream is of first order and is outlet */
	    max_strahler_num = 1;
	    max_strahler = 0;
	    next_stream = s_streams[cur_stream].next_stream;

	    if (s_streams[cur_stream].trib_num == 0) {	/* assign 1 for spring stream */
		s_streams[cur_stream].strahler = 1;
		cur_stream = next_stream;
		done = 1;
	    }
	    else {
		done = 1;

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* loop for determining strahler */
		    if (s_streams[s_streams[cur_stream].trib[i]].strahler < 0) {
			done = 0;
			break;	/* strahler is not determined, break for loop */
		    }
		    else if (s_streams[s_streams[cur_stream].trib[i]].strahler
			     > max_strahler) {
			max_strahler =
			    s_streams[s_streams[cur_stream].trib[i]].strahler;
			max_strahler_num = 1;
		    }
		    else if (s_streams[s_streams[cur_stream].trib[i]].strahler
			     == max_strahler) {
			++max_strahler_num;
		    }
		}		/* end determining strahler */

		if (done == 1) {
		    s_streams[cur_stream].strahler =
			(max_strahler_num >
			 1) ? ++max_strahler : max_strahler;
		    cur_stream = next_stream;	/* if next_stream<0 we in outlet stream */
		}

	    }
	} while (done && next_stream > 0);
    }				/* end for of main loop */
    return 0;
}				/* end strahler */

int shreeve(void)
{
    int i, j, done = 1;
    int cur_stream, next_stream;
    int max_shreeve = 0;

    G_message("Calculating Shreeve's stream magnitude ...");

    for (j = 0; j < springs_num; ++j) {	/* main loop on springs */

	cur_stream = s_streams[springs[j]].stream;
	do {			/* we must go at least once, if stream is of first order and is outlet */

	    max_shreeve = 0;
	    next_stream = s_streams[cur_stream].next_stream;

	    if (s_streams[cur_stream].trib_num == 0) {	/* assign 1 for spring stream */

		s_streams[cur_stream].shreeve = 1;
		cur_stream = next_stream;
		done = 1;

	    }
	    else {
		done = 1;

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* loop for determining strahler */
		    if (s_streams[s_streams[cur_stream].trib[i]].shreeve < 0) {
			done = 0;
			break;	/* shreeve is not determined, break for loop */
		    }
		    else {
			max_shreeve +=
			    s_streams[s_streams[cur_stream].trib[i]].shreeve;
		    }
		}		/* end determining strahler */

		if (done == 1) {
		    s_streams[cur_stream].shreeve = max_shreeve;
		    cur_stream = next_stream;	/* if next_stream<0 we in outlet stream */
		}
	    }

	} while (done && next_stream > 0);
    }				/* end main loop */
    return 0;
}				/* end shreeve */

int horton(void)
{
    int *stack;
    int top, i, j;
    int cur_stream, cur_horton;
    int max_strahler;
    double max_accum;
    int up_stream = 0;

    G_message("Calculating Hortons's stream order ...");
    stack = (int *)G_malloc(stack_max * sizeof(int));

    for (j = 0; j < outlets_num; ++j) {
	cur_stream = s_streams[outlets[j]].stream;	/* outlet: init */
	cur_horton = s_streams[cur_stream].strahler;
	stack[0] = 0;
	stack[1] = cur_stream;
	top = 1;

	do {			/* on every stream */
	    max_strahler = 0;
	    max_accum = 0;

	    if (s_streams[cur_stream].trib_num == 0) {	/* spring: go back on stack */

		s_streams[cur_stream].horton = cur_horton;
		cur_stream = stack[--top];

	    }
	    else if (s_streams[cur_stream].trib_num > 1) {	/* node */

		up_stream = 0;	/* calculating up_stream */
		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {
		    if (s_streams[s_streams[cur_stream].trib[i]].horton < 0) {

			if (s_streams[s_streams[cur_stream].trib[i]].strahler
			    > max_strahler) {
			    max_strahler =
				s_streams[s_streams[cur_stream].
					  trib[i]].strahler;
			    max_accum =
				s_streams[s_streams[cur_stream].
					  trib[i]].accum;
			    up_stream = s_streams[cur_stream].trib[i];

			}
			else if (s_streams
				 [s_streams[cur_stream].trib[i]].strahler ==
				 max_strahler) {

			    if (s_streams[s_streams[cur_stream].trib[i]].accum
				> max_accum) {
				max_accum =
				    s_streams[s_streams[cur_stream].
					      trib[i]].accum;
				up_stream = s_streams[cur_stream].trib[i];
			    }
			}
		    }
		}		/* end determining up_stream */

		if (up_stream) {	/* at least one branch is not assigned */
		    if (s_streams[cur_stream].horton < 0) {
			s_streams[cur_stream].horton = cur_horton;
		    }
		    else {
			cur_horton = s_streams[up_stream].strahler;
		    }
		    cur_stream = up_stream;
		    stack[++top] = cur_stream;

		}
		else {		/* all asigned, go downstream */
		    cur_stream = stack[--top];

		}		/* end up_stream */
	    }			/* end spring/node */
	} while (cur_stream);
    }				/* end for outlets */
    G_free(stack);
    return 0;
}

int hack(void)
{
    int *stack;
    int top, i, j;
    int cur_stream, cur_hack;
    double max_accum;
    int up_stream = 0;

    G_message("Calculating Hack's main streams ...");
    stack = (int *)G_malloc(stack_max * sizeof(int));

    for (j = 0; j < outlets_num; ++j) {
	cur_stream = s_streams[outlets[j]].stream;	/* outlet: init */
	cur_hack = 1;
	stack[0] = 0;
	stack[1] = cur_stream;
	top = 1;

	do {
	    max_accum = 0;

	    if (s_streams[cur_stream].trib_num == 0) {	/* spring: go back on stack */

		s_streams[cur_stream].hack = cur_hack;
		cur_stream = stack[--top];

	    }
	    else if (s_streams[cur_stream].trib_num > 1) {	/* node */
		up_stream = 0;	/* calculating up_stream */

		for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {	/* determining upstream */
		    if (s_streams[s_streams[cur_stream].trib[i]].hack < 0) {
			if (s_streams[s_streams[cur_stream].trib[i]].accum >
			    max_accum) {
			    max_accum =
				s_streams[s_streams[cur_stream].
					  trib[i]].accum;
			    up_stream = s_streams[cur_stream].trib[i];
			}
		    }
		}		/* end determining up_stream */

		if (up_stream) {	/* at least one branch is not assigned */
		    if (s_streams[cur_stream].hack < 0) {
			s_streams[cur_stream].hack = cur_hack;
		    }
		    else {
			cur_hack = s_streams[cur_stream].hack;
			++cur_hack;
		    }
		    cur_stream = up_stream;
		    stack[++top] = cur_stream;

		}
		else {		/* all asigned, go downstream */

		    cur_stream = stack[--top];

		}		/* end up_stream */
	    }			/* end spring/node */
	} while (cur_stream);
    }				/* end for outlets */
    G_free(stack);
    return 0;
}
