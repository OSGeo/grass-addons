#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

/* need elevation map, do A* search on elevation like for r.watershed */

int ele_round(double x)
{
    int n;

    if (x >= 0.0)
	n = x + .5;
    else {
	n = -x + .5;
	n = -n;
    }

    return n;
}

/*
 * loads elevation and optional flow accumulation map to memory and
 * gets start points for A* Search
 * start points are edges
 */
int load_maps(int ele_fd, int acc_fd, int depr_fd)
{
    int r, c, thisindex;
    char asp_value, *aspp;
    void *ele_buf, *ptr, *acc_buf = NULL, *acc_ptr = NULL;
    CELL *loadp, ele_value;
    CELL *depr_buf;
    DCELL dvalue;
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    int r_nbr, c_nbr, ct_dir;
    int is_worked;
    size_t ele_size, acc_size = 0;
    int ele_map_type, acc_map_type = 0;
    DCELL *accp;

    if (acc_fd < 0)
	G_message(_("Load elevation map and get start points..."));
    else
	G_message(_("Load input maps and get start points..."));

    n_search_points = n_points = 0;

    G_debug(1, "get buffers");
    ele_map_type = G_get_raster_map_type(ele_fd);
    ele_size = G_raster_size(ele_map_type);
    ele_buf = G_allocate_raster_buf(ele_map_type);

    if (ele_buf == NULL) {
	G_warning(_("Could not allocate memory"));
	return -1;
    }

    if (acc_fd >= 0) {
	acc_map_type = G_get_raster_map_type(acc_fd);
	acc_size = G_raster_size(acc_map_type);
	acc_buf = G_allocate_raster_buf(acc_map_type);
	if (acc_buf == NULL) {
	    G_warning(_("Could not allocate memory"));
	    return -1;
	}
    }

    ele_scale = 1;
    if (ele_map_type == FCELL_TYPE || ele_map_type == DCELL_TYPE)
	ele_scale = 1000;	/* should be enough to do the trick */

    worked = flag_create(nrows, ncols);
    in_list = flag_create(nrows, ncols);

    loadp = ele;
    accp = acc;
    aspp = asp;

    G_debug(1, "start loading %d rows, %d cols", nrows, ncols);
    for (r = 0; r < nrows; r++) {

	G_percent(r, nrows, 2);

	if (G_get_raster_row(ele_fd, ele_buf, r, ele_map_type) < 0) {
	    G_warning(_("Could not read raster maps at row <%d>"), r);
	    return -1;
	}
	ptr = ele_buf;

	if (acc_fd >= 0) {
	    if (G_get_raster_row(acc_fd, acc_buf, r, acc_map_type) < 0) {
		G_warning(_("Could not read raster maps at row <%d>"), r);
		return -1;
	    }
	    acc_ptr = acc_buf;
	}

	for (c = 0; c < ncols; c++) {

	    FLAG_UNSET(worked, r, c);
	    FLAG_UNSET(in_list, r, c);

	    /* check for masked and NULL cells */
	    if (G_is_null_value(ptr, ele_map_type)) {
		if (acc_fd >= 0) {
		    if (!G_is_null_value(acc_ptr, acc_map_type))
			G_fatal_error(_("Accumulation map does not match elevation map!"));
		}

		FLAG_SET(worked, r, c);
		FLAG_SET(in_list, r, c);
		G_set_c_null_value(loadp, 1);
		*accp = 0;
	    }
	    else {
		if (ele_map_type == CELL_TYPE) {
		    *loadp = *((CELL *) ptr);
		}
		else if (ele_map_type == FCELL_TYPE) {
		    dvalue = *((FCELL *) ptr);
		    dvalue *= ele_scale;
		    *loadp = ele_round(dvalue);
		}
		else if (ele_map_type == DCELL_TYPE) {
		    dvalue = *((DCELL *) ptr);
		    dvalue *= ele_scale;
		    *loadp = ele_round(dvalue);
		}
		if (acc_fd < 0)
		    *accp = 1;
		else {
		    if (G_is_null_value(acc_ptr, acc_map_type)) {
			/* can this be ok after weighing ? */
			G_fatal_error(_("Accumulation map does not match elevation map!"));
		    }

		    switch (acc_map_type) {
		    case CELL_TYPE:
			*accp = *((CELL *) acc_ptr);
			break;
		    case FCELL_TYPE:
			*accp = *((FCELL *) acc_ptr);
			break;
		    case DCELL_TYPE:
			*accp = *((DCELL *) acc_ptr);
			break;
		    }
		}

		n_points++;
	    }

	    loadp++;
	    accp++;
	    ptr = G_incr_void_ptr(ptr, ele_size);
	    *aspp = 0;
	    aspp++;
	    if (acc_fd >= 0)
		acc_ptr = G_incr_void_ptr(acc_ptr, acc_size);
	}
    }
    G_percent(nrows, nrows, 1);	/* finish it */

    G_close_cell(ele_fd);
    G_free(ele_buf);

    if (acc_fd >= 0) {
	G_close_cell(acc_fd);
	G_free(acc_buf);
    }

    astar_pts =
	(unsigned int *)G_malloc((n_points + 1) *
				     sizeof(unsigned int));

    /* astar_heap will track astar_pts in ternary min-heap */
    /* astar_heap is one-based */
    astar_added =
	(unsigned int *)G_malloc((n_points + 1) * sizeof(unsigned int));

    nxt_avail_pt = heap_size = 0;

    /* load edge cells and real depressions to A* heap */
    if (depr_fd >= 0)
	depr_buf = G_allocate_raster_buf(CELL_TYPE);
    else
	depr_buf = NULL;

    G_message(_("Set edge points..."));
    loadp = ele;
    for (r = 0; r < nrows; r++) {
	G_percent(r, nrows, 2);

	if (depr_fd >= 0) {
	    if (G_get_raster_row(depr_fd, depr_buf, r, CELL_TYPE) < 0) {
		G_warning(_("Could not read raster map at row <%d>"), r);
		return -1;
	    }
	}

	for (c = 0; c < ncols; c++) {

	    is_worked = FLAG_GET(worked, r, c);

	    if (is_worked)
		continue;

	    if (r == 0 || r == nrows - 1 || c == 0 || c == ncols - 1) {

		asp_value = 0;
		if (r == 0 && c == 0)
		    asp_value = -7;
		else if (r == 0 && c == ncols - 1)
		    asp_value = -5;
		else if (r == nrows - 1 && c == 0)
		    asp_value = -1;
		else if (r == nrows - 1 && c == ncols - 1)
		    asp_value = -3;
		else if (r == 0)
		    asp_value = -2;
		else if (c == 0)
		    asp_value = -4;
		else if (r == nrows - 1)
		    asp_value = -6;
		else if (c == ncols - 1)
		    asp_value = -8;

		thisindex = INDEX(r, c);
		ele_value = ele[thisindex];
		asp[thisindex] = asp_value;
		heap_add(r, c, ele_value, asp_value);
		continue;
	    }

	    /* any neighbour NULL ? */
	    asp_value = 0;
	    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		/* get r, c (r_nbr, c_nbr) for neighbours */
		r_nbr = r + nextdr[ct_dir];
		c_nbr = c + nextdc[ct_dir];

		is_worked = FLAG_GET(worked, r_nbr, c_nbr);

		if (is_worked) {
		    asp_value = -drain[r - r_nbr + 1][c - c_nbr + 1];
		    thisindex = INDEX(r, c);
		    ele_value = ele[thisindex];
		    asp[thisindex] = asp_value;
		    heap_add(r, c, ele_value, asp_value);

		    break;
		}
	    }
	    if (asp_value) /* some neighbour was NULL, point added to list */
		continue;
	    
	    /* real depression ? */
	    if (depr_fd >= 0) {
		if (!G_is_c_null_value(&depr_buf[c]) && depr_buf[c] != 0) {
		    thisindex = INDEX(r, c);
		    ele_value = ele[thisindex];
		    asp[thisindex] = 0;
		    heap_add(r, c, ele_value, 0);
		}
	    }
	}
    }
    G_percent(nrows, nrows, 2);	/* finish it */

    if (depr_fd >= 0) {
	G_close_cell(depr_fd);
	G_free(depr_buf);
    }

    G_debug(1, "%d edge (and depression) cells", heap_size);
    G_debug(1, "%d non-NULL cells", n_points);

    return 1;
}
