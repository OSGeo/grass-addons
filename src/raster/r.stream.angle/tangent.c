#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/glocale.h>
#include "global.h"



/* avg_direction calculate direction of stream in the confluence point as
 * avaraged direction  of current segment and previous segment of the same order 
 * the number of cell used for this can be determinde by user by parameter step_num */

int calc_tangent(int ordering)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int cur_stream;
    int prev_stream = 0;
    int cur_order, prev_order;
    int r, c, d;
    int rn, cn;			/* row, col cur stream */
    int next_rn, next_cn;
    int rp, cp;			/* row, col prev stream */
    int i, j, k;
    int step_num;
    int *tribstack;
    int top = 1;
    int done;

    tribstack = (int *)G_malloc(stack_max * sizeof(int));

    for (j = 0; j < outlets_num; ++j) {
	cur_stream = s_streams[outlets[j]].stream;
	tribstack[0] = 0;
	top = 1;

	do {
	    /* prev streams and tribs */
	    prev_stream = 0;
	    cur_order = cur_orders(cur_stream, ordering);

	    for (i = 0; i < s_streams[cur_stream].trib_num; ++i) {
		prev_order =
		    cur_orders(s_streams[cur_stream].trib[i], ordering);
		if (prev_order == cur_order) {
		    prev_stream = s_streams[cur_stream].trib[i];	/* is continuation */
		}
		else {
		    tribstack[top++] = s_streams[cur_stream].trib[i];

		}		/* end else */

	    }			/* for i */

	    if (!prev_stream) {
		cur_stream = tribstack[--top];
		if (cur_stream)	/* what to do with the stack */
		    continue;
		else
		    break;
	    }

	    rn = r = s_streams[cur_stream].init_r;
	    cn = c = s_streams[cur_stream].init_c;

	    for (i = 1; i < 9; ++i) {
		if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1)
		    || c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		    continue;
		if (streams[r + nextr[i]][c + nextc[i]] == prev_stream) {
		    rp = r + nextr[i];
		    cp = c + nextc[i];
		}
	    }			/* for i */

	    /* calculate direction for cur_stream */
	    step_num = seg_length;

	    while (step_num) {

		step_num--;

		/* downstream */
		d = dirs[rn][cn];
		next_rn = rn + nextr[d];
		next_cn = cn + nextc[d];

		if (d < 1 ||	/* no more cells */
		    next_rn < 0 || next_rn > (nrows - 1) ||
		    next_cn < 0 || next_cn > (ncols - 1))

		    break;	/* leave internal while */

		rn = next_rn;
		cn = next_cn;

		/* upstream */
		prev_order = 0;
		done = 0;

		for (i = 1; i < 9; ++i) {
		    if (rp + nextr[i] < 0 || rp + nextr[i] > (nrows - 1)
			|| cp + nextc[i] < 0 || cp + nextc[i] > (ncols - 1))
			continue;

		    k = (i + 4) > 8 ? i - 4 : i + 4;

		    if (streams[rp + nextr[i]][cp + nextc[i]] > 0 &&
			dirs[rp + nextr[i]][cp + nextc[i]] == k) {
			prev_order =
			    cur_orders(streams[rp + nextr[i]][cp + nextc[i]],
				       ordering);

			if (prev_order == cur_order) {
			    rp += nextr[i];
			    cp += nextc[i];
			    done = 1;
			    break;	/* leave for */
			}
		    }
		}		/* end for i */

		if (!done)
		    break;	/* leave internal while */
	    }			/* end internal while */

	    s_streams[cur_stream].tangent_dir = calc_dir(rp, cp, rn, cn);

	    cur_stream = prev_stream;
	} while (top);

    }				/* for j */
    G_free(tribstack);
    return 0;
}

/* for strahler and none ordering 
 * add missing dirs for streams of higher order
 */

int add_missing_dirs(int ordering)
{
    int j;
    int out;
    int seg_num;
    float last_angle, pre_last_angle;
    float last_angle_diff;
    int last_length;

    for (j = 1; j <= stream_num; ++j) {

	if (s_streams[j].strahler == 1 || seg_common[j].init_stream != j)
	    continue;

	out = seg_common[j].out_stream;
	seg_num = seg_common[out].seg_num;

	if (seg_num == 1) {
	    s_streams[j].tangent_dir = seg_common[out].angles[0];
	    continue;
	}

	last_angle = seg_common[out].angles[seg_num - 1];
	last_length = seg_common[out].lengths[seg_num - 1];

	if (last_length > seg_outlet) {
	    s_streams[j].tangent_dir = seg_common[out].angles[seg_num - 1];
	    continue;
	}

	pre_last_angle = seg_common[out].angles[seg_num - 2];

	last_angle_diff = (abs(pre_last_angle - last_angle) > PI) ?
	    2 * PI - abs(pre_last_angle - last_angle) : abs(pre_last_angle -
							    last_angle);

	if (last_angle_diff > PI - seg_outlet) {
	    s_streams[j].tangent_dir = seg_common[out].angles[seg_num - 2];
	}
	else {
	    s_streams[j].tangent_dir =
		calc_dir(s_streams[j].init_r,
			 s_streams[j].init_c,
			 s_streams[s_streams[j].next_stream].out_r,
			 s_streams[s_streams[j].next_stream].out_c);


	}
	/* calc stream direction using coordinates 
	 * of two last segments of current stream segment */

    }				/* for j */
    return 0;
}
