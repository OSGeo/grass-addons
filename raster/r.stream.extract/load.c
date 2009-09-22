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
int load_maps(int ele_fd, int acc_fd, int weight_fd)
{
    int r, c, thisindex;
    char asp_value;
    void *ele_buf, *ptr, *acc_buf = NULL, *acc_ptr = NULL, *weight_buf =
	NULL, *weight_ptr = NULL;
    CELL *loadp, ele_value;
    DCELL dvalue;
    int nextdr[8] = { 1, -1, 0, 0, -1, 1, 1, -1 };
    int nextdc[8] = { 0, 0, -1, 1, 1, -1, 1, -1 };
    int r_nbr, c_nbr, ct_dir;
    int is_worked;
    size_t ele_size, acc_size = 0, weight_size = 0;
    int ele_map_type, acc_map_type = 0, weight_map_type = 0;
    CELL *streamp;
    DCELL *accp, *weightp;

    if (acc_fd < 0 && weight_fd < 0)
	G_message(_("load elevation map and get start points"));
    else
	G_message(_("load input maps and get start points"));

    n_search_points = n_points = 0;

    G_debug(1, "get buffers");
    ele_map_type = G_get_raster_map_type(ele_fd);
    ele_size = G_raster_size(ele_map_type);
    ele_buf = G_allocate_raster_buf(ele_map_type);

    if (ele_buf == NULL) {
	G_warning(_("could not allocate memory"));
	return -1;
    }

    if (acc_fd >= 0) {
	acc_map_type = G_get_raster_map_type(acc_fd);
	acc_size = G_raster_size(acc_map_type);
	acc_buf = G_allocate_raster_buf(acc_map_type);
	if (acc_buf == NULL) {
	    G_warning(_("could not allocate memory"));
	    return -1;
	}
    }

    if (weight_fd >= 0) {
	weight_map_type = G_get_raster_map_type(weight_fd);
	weight_size = G_raster_size(weight_map_type);
	weight_buf = G_allocate_raster_buf(weight_map_type);
	if (weight_buf == NULL) {
	    G_warning(_("could not allocate memory"));
	    return -1;
	}
    }

    ele_scale = 1;
    if (ele_map_type == FCELL_TYPE || ele_map_type == DCELL_TYPE)
	ele_scale = 1000;	/* should be enough to do the trick */

    worked = flag_create(nrows, ncols);
    in_list = flag_create(nrows, ncols);

    loadp = ele;
    streamp = stream;
    accp = acc;
    weightp = accweight;

    G_debug(1, "start loading %d rows, %d cols", nrows, ncols);
    for (r = 0; r < nrows; r++) {

	G_percent(r, nrows, 2);

	if (G_get_raster_row(ele_fd, ele_buf, r, ele_map_type) < 0) {
	    G_warning(_("could not read raster maps at row <%d>"), r);
	    return -1;
	}
	ptr = ele_buf;

	if (acc_fd >= 0) {
	    if (G_get_raster_row(acc_fd, acc_buf, r, acc_map_type) < 0) {
		G_warning(_("could not read raster maps at row <%d>"), r);
		return -1;
	    }
	    acc_ptr = acc_buf;
	}

	if (weight_fd >= 0) {
	    if (G_get_raster_row(weight_fd, weight_buf, r, weight_map_type) <
		0) {
		G_warning(_("could not read raster maps at row <%d>"), r);
		return -1;
	    }
	    weight_ptr = weight_buf;
	}

	for (c = 0; c < ncols; c++) {

	    FLAG_UNSET(worked, r, c);
	    FLAG_UNSET(in_list, r, c);

	    *streamp = 0;

	    /* check for masked and NULL cells */
	    if (G_is_null_value(ptr, ele_map_type)) {
		FLAG_SET(worked, r, c);
		FLAG_SET(in_list, r, c);
		G_set_c_null_value(loadp, 1);
		*accp = 0;
		if (weight_fd >= 0)
		    *weightp = 0;
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
		    if (acc_map_type == CELL_TYPE) {
			*accp = *((CELL *) acc_ptr);
		    }
		    else if (acc_map_type == FCELL_TYPE) {
			*accp = *((FCELL *) acc_ptr);
		    }
		    else if (acc_map_type == DCELL_TYPE) {
			*accp = *((DCELL *) acc_ptr);
		    }
		}
		if (weight_fd >= 0) {
		    if (weight_map_type == CELL_TYPE) {
			*weightp = *((CELL *) weight_ptr);
		    }
		    else if (weight_map_type == FCELL_TYPE) {
			*weightp = *((FCELL *) weight_ptr);
		    }
		    else if (weight_map_type == DCELL_TYPE) {
			*weightp = *((DCELL *) weight_ptr);
		    }
		}

		n_points++;
	    }

	    loadp++;
	    accp++;
	    streamp++;
	    ptr = G_incr_void_ptr(ptr, ele_size);
	    if (acc_fd >= 0)
		acc_ptr = G_incr_void_ptr(acc_ptr, acc_size);
	    if (weight_fd >= 0) {
		weight_ptr = G_incr_void_ptr(weight_ptr, weight_size);
		weightp++;
	    }
	}
    }
    G_percent(nrows, nrows, 1);	/* finish it */

    G_close_cell(ele_fd);
    G_free(ele_buf);

    if (acc_fd >= 0) {
	G_close_cell(acc_fd);
	G_free(acc_buf);
    }

    if (weight_fd >= 0) {
	G_close_cell(weight_fd);
	G_free(weight_buf);
    }

    astar_pts =
	(struct ast_point *)G_malloc((n_points + 1) *
				     sizeof(struct ast_point));

    /* astar_heap will track astar_pts in ternary min-heap */
    /* astar_heap is one-based */
    astar_added =
	(unsigned int *)G_malloc((n_points + 1) * sizeof(unsigned int));

    nxt_avail_pt = heap_size = 0;

    /* load edge cells to A* heap */
    G_message(_("set edge points"));
    loadp = ele;
    for (r = 0; r < nrows; r++) {

	G_percent(r, nrows, 2);
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
		heap_add(r, c, ele_value, asp_value);
		FLAG_SET(in_list, r, c);
		continue;
	    }

	    /* any neighbour NULL ? */
	    for (ct_dir = 0; ct_dir < sides; ct_dir++) {
		/* get r, c (r_nbr, c_nbr) for neighbours */
		r_nbr = r + nextdr[ct_dir];
		c_nbr = c + nextdc[ct_dir];

		is_worked = FLAG_GET(worked, r_nbr, c_nbr);

		if (is_worked) {
		    asp_value = drain[r - r_nbr + 1][c - c_nbr + 1];
		    thisindex = INDEX(r, c);
		    ele_value = ele[thisindex];
		    heap_add(r, c, ele_value, asp_value);
		    FLAG_SET(in_list, r, c);

		    break;
		}
	    }

	}
    }
    G_percent(nrows, nrows, 2);	/* finish it */

    G_debug(1, "%d edge cells", heap_size);
    G_debug(1, "%d non-NULL cells", n_points);

    return 1;
}
