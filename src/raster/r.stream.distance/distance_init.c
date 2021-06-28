#include "local_proto.h"

int ram_find_outlets(CELL ** streams, int number_of_streams, CELL ** dirs,
		     int subs, int outs)
{
    int d;			/* d: direction */
    int r, c;
    int next_stream = -1, cur_stream;
    int out_max = ncols + nrows;
    int outlets_num;

    G_debug(3, "ram_find_outlets(): number_of_streams=%d", number_of_streams);

    G_message(_("Finding nodes..."));
    outlets = (OUTLET *) G_malloc((out_max) * sizeof(OUTLET));

    outlets_num = 0;

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c)
	    if (streams[r][c] > 0) {
		if (outlets_num > (out_max - 1)) {
		    if (outlets_num > 4 * (out_max - 1))
                        G_fatal_error(_("Stream and direction maps probably do not match"));
		    out_max *= 4;
		    outlets =
			(OUTLET *) G_realloc(outlets,
					     (out_max) * sizeof(OUTLET));
		}

		d = abs(dirs[r][c]);	/* r.watershed */

		if (NOT_IN_REGION(d)) {
		    next_stream = -1;
		}
		else {
		    next_stream = streams[NR(d)][NC(d)];
		    if (next_stream < 1)
			next_stream = -1;
		}

		if (d == 0)
		    next_stream = -1;

		cur_stream = streams[r][c];

		if (subs && outs) {	/* in stream mode subs is ignored */
		    if (cur_stream != next_stream) {	/* is outlet or node! */
			outlets[outlets_num].r = r;
			outlets[outlets_num++].c = c;
		    }
		}
		else {
		    if (next_stream < 0) {	/* is outlet! */
			outlets[outlets_num].r = r;
			outlets[outlets_num++].c = c;
		    }
		}		/* end lasts */
	    }			/* end if streams */

    return outlets_num;
}


int seg_find_outlets(SEGMENT * streams, int number_of_streams, SEGMENT * dirs,
		     int subs, int outs)
{
    int d;			/* d: direction */
    int r, c;
    int next_stream = -1;
    int out_max = ncols + nrows;
    int outlets_num;
    CELL streams_cell;
    CELL dirs_cell;

    G_debug(3, "ram_find_outlets(): number_of_streams=%d", number_of_streams);

    G_message(_("Finding nodes..."));
    outlets = (OUTLET *) G_malloc((out_max) * sizeof(OUTLET));

    outlets_num = 0;

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c) {
	    Segment_get(streams, &streams_cell, r, c);

	    if (streams_cell > 0) {
		if (outlets_num > (out_max - 1)) {
		    if (outlets_num > 4 * (out_max - 1))
			G_fatal_error(_("Stream and direction maps probably do not match"));
		    out_max *= 4;
		    outlets =
			(OUTLET *) G_realloc(outlets,
					     (out_max) * sizeof(OUTLET));
		}

		Segment_get(dirs, &dirs_cell, r, c);
		d = abs(dirs_cell);	/* r.watershed */

		if (NOT_IN_REGION(d)) {
		    next_stream = -1;
		}
		else {
		    Segment_get(streams, &next_stream, NR(d), NC(d));
		    if (next_stream < 1)
			next_stream = -1;
		}

		if (d == 0)
		    next_stream = -1;

		if (subs && outs) {	/* in stream mode subs is ignored */
		    if (streams_cell != next_stream) {	/* is outlet or node! */
			outlets[outlets_num].r = r;
			outlets[outlets_num++].c = c;
		    }
		}
		else {
		    if (next_stream < 0) {	/* is outlet! */
			outlets[outlets_num].r = r;
			outlets[outlets_num++].c = c;
		    }
		}		/* end lasts */
	    }			/* end if streams */
	}			/* end for c */
    return outlets_num;
}

int ram_init_distance(CELL ** streams, DCELL ** distance, int outlets_num,
		      int outs)
{
    int r, c, i;
    /* size_t data_size; 

    data_size = Rast_cell_size(DCELL_TYPE);
    */

    if (!outs) {		/* stream mode */
	for (r = 0; r < nrows; ++r)
	    for (c = 0; c < ncols; ++c)
		distance[r][c] = (streams[r][c]) ? 0 : -1;
    }
    else {			/* outlets mode */
	for (r = 0; r < nrows; ++r)
	    for (c = 0; c < ncols; ++c)
		distance[r][c] = -1;

	for (i = 0; i < outlets_num; ++i)
	    distance[outlets[i].r][outlets[i].c] = 0;
    }

    return 0;
}

int seg_init_distance(SEGMENT * streams, SEGMENT * distance, int outlets_num,
		      int outs)
{
    int r, c, i;
    CELL streams_cell;
    DCELL distance_cell;
    DCELL minus_one_cell = -1;
    DCELL zero_cell = 0;

    if (!outs) {		/* stream mode */
	for (r = 0; r < nrows; ++r)
	    for (c = 0; c < ncols; ++c) {
		Segment_get(streams, &streams_cell, r, c);
		distance_cell = (streams_cell) ? 0 : -1;
		Segment_put(distance, &distance_cell, r, c);
	    }
    }
    else {			/* outlets mode */
	for (r = 0; r < nrows; ++r)
	    for (c = 0; c < ncols; ++c)
		Segment_put(distance, &minus_one_cell, r, c);

	for (i = 0; i < outlets_num; ++i)
	    Segment_put(distance, &zero_cell, outlets[i].r, outlets[i].c);
    }
    return 0;
}

int ram_prep_null_elevation(DCELL ** distance, DCELL ** elevation)
{

    int r, c;

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c)
	    if (distance[r][c] == -1) {
		elevation[r][c] = -1;
	    }

    return 0;
}


int seg_prep_null_elevation(SEGMENT * distance, SEGMENT * elevation)
{
    int r, c;
    DCELL distance_cell;

    for (r = 0; r < nrows; ++r)
	for (c = 0; c < ncols; ++c) {
	    Segment_get(distance, &distance_cell, r, c);
	    if (distance_cell == -1)
		Segment_put(elevation, &distance_cell, r, c);
	}

    return 0;
}
