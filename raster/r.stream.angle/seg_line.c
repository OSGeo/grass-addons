#include <grass/glocale.h>
#include "global.h"

/* the idea of algorithm 
 * 
 */

int do_segments(SEGMENTS * segments, int ordering)
{
    int nextr[9] = { 0, -1, -1, -1, 0, 1, 1, 1, 0 };
    int nextc[9] = { 0, 1, 0, -1, -1, -1, 0, 1, 1 };
    int i, j, k, s;
    int done, in_loop;		/*flags */
    int r, c;
    int init, out, cur_stream, next_stream, cell_num;
    int cur_order, next_order;
    DIRCELLS *cells;
    /* variables for line segmentation */
    int small_seg_length;
    int cell_down, cell_up, small_cell_down, small_cell_up;
    float dir_down, dir_up, small_dir_down, small_dir_up;
    int out_segs, cat_num;
    int local_minimum_point;
    float local_minimum = PI;
    int seg_nums = 0;
    int prev_index = 0;
    int cells_in_segment = 1;
    int seg_cats = 0;
    double north_offset, west_offset, ns_res, ew_res;

    ns_res = window.ns_res;
    ew_res = window.ew_res;
    north_offset = window.north - 0.5 * ns_res;
    west_offset = window.west + 0.5 * ew_res;

    /* the rest of vector code is in function close_vect in io.c file */

    Segments = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    if (Vect_open_new(&Out, out_vector, 0) < 0)
	G_fatal_error(_("Unable to create new vector map <%s>"), out_vector);

    /* global variables: 
     * seg_length
     * seg_outlet
     * seg_treshold
     */

    /* for STRAHLER ordering only */
    if (ordering == STRAHLER) {
	for (i = 1; i < stream_num + 1; ++i) {
	    if (s_streams[i].strahler > 1) {
		done = 1;
		for (j = 0; j < s_streams[i].trib_num; ++j) {
		    if (s_streams[s_streams[i].trib[j]].strahler ==
			s_streams[i].strahler) {
			done = 0;
			break;
		    }
		}
		if (done)
		    springs[springs_num++] = s_streams[i].stream;
	    }
	}
    }

    /* for NONE ordering only */
    if (ordering == NONE) {
	for (i = 1; i < stream_num + 1; ++i) {
	    if (s_streams[i].strahler > 1)
		springs[springs_num++] = s_streams[i].stream;
	}
    }

    /* end for strahler and none ordering only */

    for (s = 0; s < springs_num; ++s) {

	init = springs[s];
	cur_stream = init;
	next_stream = s_streams[cur_stream].next_stream;
	cell_num = s_streams[cur_stream].cell_num;

	/* find outlet stream */
	while (cur_orders(cur_stream, ordering) ==
	       cur_orders(next_stream, ordering)) {
	    cur_stream = next_stream;
	    next_stream = s_streams[cur_stream].next_stream;
	    cell_num += s_streams[cur_stream].cell_num;
	}

	/* reset */

	out = cur_stream;
	/* s_streams[init].out_stream=out; */
	cur_stream = init;
	next_stream = s_streams[cur_stream].next_stream;

	while (cur_orders(cur_stream, ordering) ==
	       cur_orders(next_stream, ordering)) {
	    segments[cur_stream].init_stream = init;
	    segments[cur_stream].out_stream = out;
	    cur_stream = next_stream;
	    next_stream = s_streams[cur_stream].next_stream;
	}

	segments[cur_stream].init_stream = init;
	segments[cur_stream].out_stream = cur_stream;
	segments[cur_stream].cell_num = cell_num;

	r = s_streams[cur_stream].out_r;
	c = s_streams[cur_stream].out_c;

	cells = (DIRCELLS *) G_malloc((cell_num + 1) * sizeof(DIRCELLS));

	for (j = 0; j < cell_num; ++j) {

	    cells[j].r = r;
	    cells[j].c = c;
	    cells[j].dir_diff = -1;
	    cells[j].small_dir_diff = -1;
	    cells[j].candidate = 0;
	    cells[j].tunning = 0;
	    cells[j].decision = 0;


	    for (i = 1; i < 9; ++i) {
		if (r + nextr[i] < 0 || r + nextr[i] > (nrows - 1)
		    || c + nextc[i] < 0 || c + nextc[i] > (ncols - 1))
		    continue;

		k = (i + 4) > 8 ? i - 4 : i + 4;

		if (streams[r + nextr[i]][c + nextc[i]] > 0 &&
		    dirs[r + nextr[i]][c + nextc[i]] == k) {

		    cur_order = cur_orders(streams[r][c], ordering);
		    next_order =
			cur_orders(streams[r + nextr[i]][c + nextc[i]],
				   ordering);

		    if (next_order == cur_order) {

			r += nextr[i];
			c += nextc[i];
			break;
		    }
		}
	    }
	}			/* end for j, cells initialized! */

	if (cell_num < seg_outlet + 1) {

	    segments[cur_stream].dir_full =
		calc_dir(cells[cell_num - 1].r, cells[cell_num - 1].c,
			 cells[0].r, cells[0].c);
	}
	else {

	    segments[cur_stream].dir_init =
		calc_dir(cells[seg_outlet].r, cells[seg_outlet].c,
			 cells[0].r, cells[0].c);

	    segments[cur_stream].dir_full =
		calc_dir(cells[cell_num - 1].r, cells[cell_num - 1].c,
			 cells[0].r, cells[0].c);

	    segments[cur_stream].dir_middle =
		calc_dir(cells[(cell_num / 2) + (seg_outlet / 2)].r,
			 cells[(cell_num / 2) + (seg_outlet / 2)].c,
			 cells[(cell_num / 2) - (seg_outlet / 2)].r,
			 cells[(cell_num / 2) - (seg_outlet / 2)].c);

	    segments[cur_stream].dir_last =
		calc_dir(cells[cell_num - 1].r, cells[cell_num - 1].c,
			 cells[(cell_num - 1) - seg_outlet].r,
			 cells[(cell_num - 1) - seg_outlet].c);
	}

	small_seg_length = seg_length / 3;

	for (i = (seg_outlet + 1); i < (cell_num - seg_outlet); ++i) {

	    cell_down = (i < seg_length) ? i : seg_length;
	    cell_up =
		(i >
		 ((cell_num - 1) - seg_length)) ? ((cell_num - 1) -
						   i) : seg_length;

	    dir_down =
		calc_dir(cells[i].r, cells[i].c,
			 cells[i - cell_down].r, cells[i - cell_down].c);

	    dir_up =
		calc_dir(cells[i + cell_up].r, cells[i + cell_up].c,
			 cells[i].r, cells[i].c);

	    dir_up = (dir_up >= PI) ? dir_up - PI : dir_up + PI;	/* dir_up: direction upstream */

	    cells[i].dir_diff =
		fabs(dir_down - dir_up) > PI ?
		(PI * 2) - fabs(dir_down - dir_up) : fabs(dir_down - dir_up);

	    small_cell_down = (i < small_seg_length) ? i : small_seg_length;

	    small_cell_up = (i > ((cell_num - 1) - small_seg_length)) ?
		((cell_num - 1) - i) : small_seg_length;

	    small_dir_down =
		calc_dir(cells[i].r, cells[i].c,
			 cells[i - small_cell_down].r,
			 cells[i - small_cell_down].c);

	    small_dir_up =
		calc_dir(cells[i + small_cell_up].r,
			 cells[i + small_cell_up].c, cells[i].r, cells[i].c);

	    small_dir_up = (small_dir_up >= PI) ? small_dir_up - PI : small_dir_up + PI;	/* small_dir_up: direction upstream */

	    cells[i].small_dir_diff =
		fabs(small_dir_down - small_dir_up) > PI ?
		(PI * 2) - fabs(small_dir_down - small_dir_up) :
		fabs(small_dir_down - small_dir_up);

	    cells[i].candidate = (cells[i].dir_diff < seg_treshold) ? 1 : 0;
	    cells[i].tunning =
		(cells[i].small_dir_diff < (seg_treshold * 0.8)) ? 1 : 0;
	}			/* end for i */

	/* decision system: prototype */

	/* fine tunning */
	local_minimum = PI;
	cat_num = 0;
	in_loop = 0;
	out_segs = 0;

	for (i = 0; i < cell_num; ++i) {
	    if (cells[i].candidate) {

		out_segs = 0;
		if (local_minimum > cells[i].small_dir_diff) {
		    local_minimum = cells[i].small_dir_diff;
		    local_minimum_point = i;
		    in_loop = 1;
		}		/* end local minimum */

	    }
	    else if (!cells[i].candidate && in_loop) {

		out_segs++;
		if (out_segs == (seg_length / 5)) {
		    cells[local_minimum_point].decision = 1;
		    local_minimum = PI;
		    in_loop = 0;
		}
	    }
	}			/* end for: fine tunning */

	/* cleaning */
	for (i = 0, out_segs = 0; i < cell_num; ++i, out_segs++) {

	    if (cells[i].decision) {

		if (out_segs < seg_outlet && i > seg_outlet) {	/* was: seg_length/5 */
		    cells[i].decision = 0;
		    i = local_minimum_point;
		}
		else {
		    local_minimum_point = i;
		}
		out_segs = 0;
	    }
	}

	seg_nums = 0;
	prev_index = 0;
	cells_in_segment = 1;

	for (i = 0; i < cell_num; ++i) {
	    if (cells[i].decision == 1 || i == (cell_num - 1))
		seg_nums++;
	}

	segments[cur_stream].seg_num = seg_nums;
	segments[cur_stream].angles =
	    (float *)G_malloc(seg_nums * sizeof(float));
	segments[cur_stream].lengths =
	    (float *)G_malloc(seg_nums * sizeof(float));
	segments[cur_stream].drops =
	    (float *)G_malloc(seg_nums * sizeof(float));
	segments[cur_stream].cellnums =
	    (int *)G_malloc(seg_nums * sizeof(int));
	segments[cur_stream].cats = (int *)G_malloc(seg_nums * sizeof(int));

	seg_nums = 0;

	/* we go from segment outlet upstream */
	for (i = 0; i < cell_num; ++i) {
	    if (cells[i].decision == 1 || i == (cell_num - 1)) {

		segments[cur_stream].angles[seg_nums] =
		    calc_dir(cells[i].r, cells[i].c,
			     cells[prev_index].r, cells[prev_index].c);

		segments[cur_stream].lengths[seg_nums] =
		    calc_length(cells[i].r, cells[i].c,
				cells[prev_index].r, cells[prev_index].c);

		if (extended) {
		    segments[cur_stream].drops[seg_nums] =
			calc_drop(cells[i].r, cells[i].c,
				  cells[prev_index].r, cells[prev_index].c);

		    segments[cur_stream].cellnums[seg_nums] =
			cells_in_segment;
		}
		segments[cur_stream].cats[seg_nums++] = ++seg_cats;

		cells_in_segment = 0;

		if (i < (cell_num - 1))
		    prev_index = i + 1;
	    }
	    cells_in_segment++;
	}

	Vect_reset_line(Segments);
	Vect_reset_cats(Cats);

	for (i = cell_num - 1; i > -1; --i) {
	    Vect_append_point(Segments, west_offset + cells[i].c * ew_res,
			      north_offset - cells[i].r * ns_res, 0);

	    if (cells[i].decision == 1 || i == 0) {	/* start new line */

		if (dirs[cells[i].r][cells[i].c] > 0)
		    /*add point to create network */
		    Vect_append_point(Segments, west_offset +
				      (cells[i].c +
				       nextc[dirs[cells[i].r][cells[i].c]]) *
				      ew_res,
				      north_offset - (cells[i].r +
						      nextr[dirs[cells[i].r]
							    [cells[i].c]]) *
				      ns_res, 0);

		Vect_cat_set(Cats, 1, segments[cur_stream].cats[--seg_nums]);

		Vect_write_line(&Out, GV_LINE, Segments, Cats);
		Vect_reset_line(Segments);
		Vect_reset_cats(Cats);
	    }
	}
	G_free(cells);
    }

    return 0;
}
