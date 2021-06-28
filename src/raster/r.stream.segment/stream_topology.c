#include "local_proto.h"

double get_distance(int r, int c, int d)
{
    double northing, easting, next_northing, next_easting;
    int next_r, next_c;

    next_r = NR(d);
    next_c = NC(d);
    northing = window.north - (r + .5) * window.ns_res;
    easting = window.west + (c + .5) * window.ew_res;
    next_northing = window.north - (next_r + .5) * window.ns_res;
    next_easting = window.west + (next_c + .5) * window.ew_res;

    return G_distance(easting, northing, next_easting, next_northing);
}

int ram_trib_nums(int r, int c, CELL ** streams, CELL ** dirs)
{				/* calculate number of tributaries */

    int trib_num = 0;
    int i, j;
    int next_r, next_c;
    int streams_cell;
    int same_id;

    streams_cell = streams[r][c];
    same_id = 0;
    for (i = 1; i < 9; ++i) {
	if (NOT_IN_REGION(i))
	    continue;

	j = DIAG(i);
	next_r = NR(i);
	next_c = NC(i);

	if (streams[next_r][next_c] > 0 && dirs[next_r][next_c] == j) {
	    trib_num++;
	    if (streams[next_r][next_c] == streams_cell)
		same_id++;
	}
    }

    if (trib_num > 5)
	G_fatal_error(_("Error finding inits. Stream and direction maps probably do not match"));
    if (trib_num > 3)
	G_warning(_("Stream network may be too dense"));

    if (same_id > 1)
	G_warning(_("Too many stream segments with the same ID %d"), streams_cell);
    else if (same_id == 1)
	trib_num = 1;

    return trib_num;
}				/* end trib_num */


int seg_trib_nums(int r, int c, SEGMENT *streams, SEGMENT *dirs)
{				/* calculate number of tributaries */

    int trib_num = 0;
    int i, j;
    int next_r, next_c;
    int streams_cell, streams_next_cell, dirs_next_cell;
    int same_id;

    Segment_get(streams, &streams_cell, r, c);
    same_id = 0;
    for (i = 1; i < 9; ++i) {
	if (NOT_IN_REGION(i))
	    continue;

	j = DIAG(i);
	next_r = NR(i);
	next_c = NC(i);

	Segment_get(streams, &streams_next_cell, next_r, next_c);
	Segment_get(dirs, &dirs_next_cell, next_r, next_c);

	if (streams_next_cell > 0 && dirs_next_cell == j) {
	    trib_num++;
	    if (streams_next_cell == streams_cell)
		same_id++;
	}
    }

    if (trib_num > 5)
	G_fatal_error(_("Error finding inits. Stream and direction maps probably do not match"));
    if (trib_num > 3)
	G_warning(_("Stream network may be too dense"));


    if (same_id > 1)
	G_warning(_("Too many stream segments with the same ID %d"), streams_cell);
    else if (same_id == 1)
	trib_num = 1;

    return trib_num;
}				/* end trib_num */


int ram_number_of_streams(CELL **streams, CELL **dirs, int *ordered)
{
    int r, c;
    int stream_num = 0;
    int one = 0, two = 0;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c] > 0) {
		if (ram_trib_nums(r, c, streams, dirs) != 1) {
		    stream_num++;
		    if (streams[r][c] == 1)
			one++;
		    if (streams[r][c] == 2)
			two++;
		}
	    }
	}
    }
    *ordered = (one > 1 || two > 1) ? 1 : 0;
    /* if there is more than 1 stream with identifier 1 or 2  network is ordered */

    return stream_num;
}

int seg_number_of_streams(SEGMENT *streams, SEGMENT *dirs, int *ordered)
{
    int r, c;
    int stream_num = 0;
    int one = 0, two = 0;
    int streams_cell;

    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    Segment_get(streams, &streams_cell, r, c);
	    if (streams_cell > 0) {
		if (seg_trib_nums(r, c, streams, dirs) != 1) {
		    stream_num++;
		    if (streams_cell == 1)
			one++;
		    if (streams_cell == 2)
			two++;
		}
	    }
	}
    }
    *ordered = (one > 1 || two > 1) ? 1 : 0;
    /* if there is more than 1 stream with identifier 1 or 2  network is ordered */

    return stream_num;
}

int ram_build_streamlines(CELL **streams, CELL **dirs, FCELL **elevation,
			  int number_of_streams)
{
    int r, c, i;
    int d, next_d;
    int prev_r, prev_c;
    int stream_num = 1, cell_num = 0;
    int contrib_cell;
    STREAM *SA;
    int border_dir;

    stream_attributes =
	(STREAM *) G_malloc(number_of_streams * sizeof(STREAM));

    G_message(_("Finding inits..."));
    SA = stream_attributes;
    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    if (streams[r][c]) {
		if (ram_trib_nums(r, c, streams, dirs) != 1) {	/* adding inits */
		    if (stream_num > number_of_streams)
			G_fatal_error(_("Error finding inits. Stream and direction maps probably do not match"));

		    SA[stream_num].stream = stream_num;
		    SA[stream_num].init = INDEX(r, c);
		    stream_num++;
		}
	    }
	}
    }

    for (i = 1; i < stream_num; ++i) {

	r = (int)(SA[i].init / ncols);
	c = (int)(SA[i].init % ncols);
	SA[i].order = streams[r][c];
	SA[i].number_of_cells = 0;
	do {

	    SA[i].number_of_cells++;
	    d = abs(dirs[r][c]);
	    if (NOT_IN_REGION(d) || d == 0)
		break;
	    r = NR(d);
	    c = NC(d);
	} while (streams[r][c] == SA[i].order && ram_trib_nums(r, c, streams, dirs) == 1);

	SA[i].number_of_cells += 2;	/* add two extra points for init+ and outlet+ */
    }

    for (i = 1; i < number_of_streams; ++i) {

	SA[i].points = (long int *)
	    G_malloc((SA[i].number_of_cells) * sizeof(long int));
	SA[i].elevation = (float *)
	    G_malloc((SA[i].number_of_cells) * sizeof(float));
	SA[i].distance = (double *)
	    G_malloc((SA[i].number_of_cells) * sizeof(double));

	r = (int)(SA[i].init / ncols);
	c = (int)(SA[i].init % ncols);
	contrib_cell = ram_find_contributing_cell(r, c, dirs, elevation);
	prev_r = NR(contrib_cell);
	prev_c = NC(contrib_cell);

	/* add one point contributing to init to calculate parameters */
	/* what to do if there is no contributing points? */
	SA[i].points[0] = (contrib_cell == 0) ? -1 : INDEX(prev_r, prev_c);
	SA[i].elevation[0] = (contrib_cell == 0) ? -99999 :
	    elevation[prev_r][prev_c];
	d = (contrib_cell == 0) ? dirs[r][c] : dirs[prev_r][prev_c];
	SA[i].distance[0] = (contrib_cell == 0) ? get_distance(r, c, d) :
	    get_distance(prev_r, prev_c, d);

	SA[i].points[1] = INDEX(r, c);
	SA[i].elevation[1] = elevation[r][c];
	d = abs(dirs[r][c]);
	SA[i].distance[1] = get_distance(r, c, d);

	cell_num = 2;
	do {
	    d = abs(dirs[r][c]);

	    if (NOT_IN_REGION(d) || d == 0) {
		SA[i].points[cell_num] = -1;
		SA[i].distance[cell_num] = SA[i].distance[cell_num - 1];
		SA[i].elevation[cell_num] =
		    2 * SA[i].elevation[cell_num - 1] -
		    SA[i].elevation[cell_num - 2];
		border_dir = convert_border_dir(r, c, dirs[r][c]);
		SA[i].last_cell_dir = border_dir;
		break;
	    }
	    r = NR(d);
	    c = NC(d);
	    SA[i].last_cell_dir = dirs[r][c];
	    SA[i].points[cell_num] = INDEX(r, c);
	    SA[i].elevation[cell_num] = elevation[r][c];
	    next_d = (abs(dirs[r][c]) == 0) ? d : abs(dirs[r][c]);
	    SA[i].distance[cell_num] = get_distance(r, c, next_d);
	    cell_num++;
	    if (cell_num > SA[i].number_of_cells)
		G_fatal_error(_("To many points in stream line"));
	} while (streams[r][c] == SA[i].order && ram_trib_nums(r, c, streams, dirs) == 1);

	if (SA[i].elevation[0] == -99999)
	    SA[i].elevation[0] = 2 * SA[i].elevation[1] - SA[i].elevation[2];
    }

    return 0;
}


int seg_build_streamlines(SEGMENT *streams, SEGMENT *dirs,
			  SEGMENT *elevation, int number_of_streams)
{
    int r, c, i;
    int d, next_d;
    int prev_r, prev_c;
    int stream_num = 1, cell_num = 0;
    int contrib_cell;
    STREAM *SA;
    int border_dir;
    int streams_cell, dirs_cell;
    int dirs_prev_cell;
    float elevation_cell, elevation_prev_cell;

    stream_attributes =
	(STREAM *) G_malloc(number_of_streams * sizeof(STREAM));

    G_message(_("Finding inits..."));
    SA = stream_attributes;
    for (r = 0; r < nrows; ++r) {
	for (c = 0; c < ncols; ++c) {
	    Segment_get(streams, &streams_cell, r, c);

	    if (streams_cell) {
		if (seg_trib_nums(r, c, streams, dirs) != 1) {	/* adding inits */
		    if (stream_num > number_of_streams)
			G_fatal_error(_("Error finding inits. Stream and direction maps probably do not match"));

		    SA[stream_num].stream = stream_num;
		    SA[stream_num].init = INDEX(r, c);
		    stream_num++;
		}
	    }
	}
    }

    for (i = 1; i < stream_num; ++i) {

	r = (int)(SA[i].init / ncols);
	c = (int)(SA[i].init % ncols);
	Segment_get(streams, &streams_cell, r, c);
	SA[i].order = streams_cell;
	SA[i].number_of_cells = 0;

	do {
	    SA[i].number_of_cells++;
	    Segment_get(dirs, &dirs_cell, r, c);

	    d = abs(dirs_cell);
	    if (NOT_IN_REGION(d) || d == 0)
		break;
	    r = NR(d);
	    c = NC(d);
	    Segment_get(streams, &streams_cell, r, c);
	} while (streams_cell == SA[i].order && seg_trib_nums(r, c, streams, dirs) == 1);

	SA[i].number_of_cells += 2;	/* add two extra points for point before init and after outlet */
    }

    for (i = 1; i < number_of_streams; ++i) {

	SA[i].points = (long int *)
	    G_malloc((SA[i].number_of_cells) * sizeof(long int));
	SA[i].elevation = (float *)
	    G_malloc((SA[i].number_of_cells) * sizeof(float));
	SA[i].distance = (double *)
	    G_malloc((SA[i].number_of_cells) * sizeof(double));

	r = (int)(SA[i].init / ncols);
	c = (int)(SA[i].init % ncols);
	contrib_cell = seg_find_contributing_cell(r, c, dirs, elevation);
	prev_r = NR(contrib_cell);
	prev_c = NC(contrib_cell);

	/* add one point contributing to init to calculate parameters */
	/* what to do if there is no contributing points? */

	Segment_get(dirs, &dirs_cell, r, c);
	Segment_get(dirs, &dirs_prev_cell, prev_r, prev_c);
	Segment_get(elevation, &elevation_prev_cell, prev_r, prev_c);
	Segment_get(elevation, &elevation_cell, r, c);

	SA[i].points[0] = (contrib_cell == 0) ? -1 : INDEX(prev_r, prev_c);
	SA[i].elevation[0] = (contrib_cell == 0) ? -99999 :
	    elevation_prev_cell;
	d = (contrib_cell == 0) ? dirs_cell : dirs_prev_cell;
	SA[i].distance[0] = (contrib_cell == 0) ? get_distance(r, c, d) :
	    get_distance(prev_r, prev_c, d);

	SA[i].points[1] = INDEX(r, c);
	SA[i].elevation[1] = elevation_cell;
	d = abs(dirs_cell);
	SA[i].distance[1] = get_distance(r, c, d);

	cell_num = 2;
	do {
	    Segment_get(dirs, &dirs_cell, r, c);
	    d = abs(dirs_cell);

	    if (NOT_IN_REGION(d) || d == 0) {
		SA[i].points[cell_num] = -1;
		SA[i].distance[cell_num] = SA[i].distance[cell_num - 1];
		SA[i].elevation[cell_num] =
		    2 * SA[i].elevation[cell_num - 1] -
		    SA[i].elevation[cell_num - 2];
		border_dir = convert_border_dir(r, c, dirs_cell);
		SA[i].last_cell_dir = border_dir;
		break;
	    }
	    r = NR(d);
	    c = NC(d);
	    Segment_get(dirs, &dirs_cell, r, c);
	    SA[i].last_cell_dir = dirs_cell;
	    SA[i].points[cell_num] = INDEX(r, c);
	    Segment_get(elevation, &SA[i].elevation[cell_num], r, c);
	    next_d = (abs(dirs_cell) == 0) ? d : abs(dirs_cell);
	    SA[i].distance[cell_num] = get_distance(r, c, next_d);
	    cell_num++;
	    if (cell_num > SA[i].number_of_cells)
		G_fatal_error(_("To much points in stream line"));
	    Segment_get(streams, &streams_cell, r, c);
	} while (streams_cell == SA[i].order && seg_trib_nums(r, c, streams, dirs) == 1);

	if (SA[i].elevation[0] == -99999)
	    SA[i].elevation[0] = 2 * SA[i].elevation[1] - SA[i].elevation[2];
    }

    return 0;
}

int ram_find_contributing_cell(int r, int c, CELL **dirs, FCELL **elevation)
{
    int i, j = 0;
    int next_r, next_c;
    float elev_min = 9999;

    for (i = 1; i < 9; ++i) {
	if (NOT_IN_REGION(i))
	    continue;
	next_r = NR(i);
	next_c = NC(i);
	if (dirs[next_r][next_c] == DIAG(i) &&
	    elevation[next_r][next_c] < elev_min) {
	    elev_min = elevation[next_r][next_c];
	    j = i;
	}
    }

    return j;
}

int seg_find_contributing_cell(int r, int c, SEGMENT *dirs,
			       SEGMENT *elevation)
{
    int i, j = 0;
    int next_r, next_c;
    float elev_min = 9999;
    int dirs_next_cell;
    float elevation_next_cell;

    for (i = 1; i < 9; ++i) {
	if (NOT_IN_REGION(i))
	    continue;
	next_r = NR(i);
	next_c = NC(i);
	Segment_get(elevation, &elevation_next_cell, next_r, next_c);
	Segment_get(dirs, &dirs_next_cell, next_r, next_c);

	if (dirs_next_cell == DIAG(i) && elevation_next_cell < elev_min) {
	    elev_min = elevation_next_cell;
	    j = i;
	}
    }
    return j;
}

int ram_fill_streams(CELL **unique_streams, int number_of_streams)
{
    int r, c;
    int i, j;
    STREAM *SA;

    SA = stream_attributes;

    for (i = 1; i < number_of_streams; ++i) {
	for (j = 1; j < SA[i].number_of_cells - 1; ++j) {
	    r = (int)(SA[i].points[j] / ncols);
	    c = (int)(SA[i].points[j] % ncols);
	    unique_streams[r][c] = SA[i].stream;
	}
    }
    return 0;
}

int seg_fill_streams(SEGMENT *unique_streams, int number_of_streams)
{
    int r, c;
    int i, j;
    STREAM *SA;

    SA = stream_attributes;

    for (i = 1; i < number_of_streams; ++i) {
	for (j = 1; j < SA[i].number_of_cells - 1; ++j) {
	    r = (int)(SA[i].points[j] / ncols);
	    c = (int)(SA[i].points[j] % ncols);
	    Segment_put(unique_streams, &SA[i].stream, r, c);
	}
    }
    return 0;
}

int ram_identify_next_stream(CELL **streams, int number_of_streams)
{
    int i, j, k, n;
    STREAM *SA;

    SA = stream_attributes;

    for (i = 1; i < number_of_streams; ++i) {
	SA[i].next_stream = -1;
	SA[i].outlet = SA[i].points[SA[i].number_of_cells - 1];

	if (SA[i].outlet >= 0) {
	    /* go through all streams
	     * do not use raster stream ID because it might not be unique */
	    for (j = 1; j < number_of_streams; ++j) {
		/* skip first point = contributing cell and 
		 * last point = outlet (next stream of next stream) */
		n = SA[j].number_of_cells - 1;
		for (k = 1; k < n; k++) {
		    if (SA[j].points[k] == SA[i].outlet) {
			SA[i].next_stream = j;
			break;
		    }
		}
		if (SA[i].next_stream > 0)
		    break;
	    }
	}
    }

    return 0;
}

int seg_identify_next_stream(SEGMENT *streams, int number_of_streams)
{
    int i, j, k, n;
    STREAM *SA;

    SA = stream_attributes;

    for (i = 1; i < number_of_streams; ++i) {
	SA[i].next_stream = -1;
	SA[i].outlet = SA[i].points[SA[i].number_of_cells - 1];

	if (SA[i].outlet >= 0) {
	    /* go through all streams
	     * do not use raster stream ID because it might not be unique */
	    for (j = 1; j < number_of_streams; ++j) {
		/* skip first point = contributing cell and 
		 * last point = outlet (next stream of next stream) */
		n = SA[j].number_of_cells - 1;
		for (k = 1; k < n; k++) {
		    if (SA[j].points[k] == SA[i].outlet) {
			SA[i].next_stream = j;
			break;
		    }
		}
		if (SA[i].next_stream > 0)
		    break;
	    }
	}
    }

    return 0;
}


int free_attributes(int number_of_streams)
{
    int i;
    STREAM *SA;

    SA = stream_attributes;

    for (i = 1; i < number_of_streams; ++i) {
	G_free(SA[i].points);
	G_free(SA[i].elevation);
	G_free(SA[i].distance);
	G_free(SA[i].sector_breakpoints);
	G_free(SA[i].sector_cats);
	G_free(SA[i].sector_directions);
	G_free(SA[i].sector_lengths);
	G_free(SA[i].sector_drops);
    }
    G_free(stream_attributes);
    return 0;
}


int convert_border_dir(int r, int c, int dir)
{
    /* this function must be added to other modules */
    /* this is added to fix r.stream.extract issue with broader cell direction */
    if (dir)
	return dir;

    if (r == 0 && c == 0)
	return -3;
    else if (r == 0 && c == ncols - 1)
	return -1;
    else if (r == nrows - 1 && c == ncols - 1)
	return -7;
    else if (r == nrows - 1 && c == 0)
	return -5;
    else if (r == 0)
	return -2;
    else if (r == nrows - 1)
	return -6;
    else if (c == 0)
	return -4;
    else if (c == ncols - 1)
	return -8;
    else
	return 0;
}
