#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

/* need elevation map, do A* search on elevation like for r.watershed */

int ele_round(double x)
{
    if (x >= 0.0)
	return x + .5;
    else
	return x - .5;
}

/*
 * loads elevation and optional flow accumulation map to memory and
 * gets start points for A* Search
 * start points are edges
 */
int load_maps(int ele_fd, int acc_fd)
{
    int r, c;
    void *ele_buf, *ptr, *acc_buf = NULL, *acc_ptr = NULL;
    CELL ele_value, *stream_id;
    DCELL dvalue, acc_value;
    size_t ele_size, acc_size = 0;
    int ele_map_type, acc_map_type = 0;
    WAT_ALT *wabuf;
    char *flag_value_buf, *aspect;

    if (acc_fd < 0)
	G_message(_("Load elevation map..."));
    else
	G_message(_("Load input maps..."));

    n_search_points = n_points = 0;

    G_debug(1, "get buffers");
    ele_map_type = Rast_get_map_type(ele_fd);
    ele_size = Rast_cell_size(ele_map_type);
    ele_buf = Rast_allocate_buf(ele_map_type);

    if (ele_buf == NULL) {
	G_warning(_("Could not allocate memory"));
	return -1;
    }

    if (acc_fd >= 0) {
	acc_map_type = Rast_get_map_type(acc_fd);
	acc_size = Rast_cell_size(acc_map_type);
	acc_buf = Rast_allocate_buf(acc_map_type);
	if (acc_buf == NULL) {
	    G_warning(_("Could not allocate memory"));
	    return -1;
	}
    }

    ele_scale = 1;
    if (ele_map_type == FCELL_TYPE || ele_map_type == DCELL_TYPE)
	ele_scale = 1000;	/* should be enough to do the trick */

    wabuf = G_malloc(ncols * sizeof(WAT_ALT));
    flag_value_buf = G_malloc(ncols * sizeof(char));
    stream_id = G_malloc(ncols * sizeof(CELL));
    aspect = G_malloc(ncols * sizeof(char));

    G_debug(1, "start loading %d rows, %d cols", nrows, ncols);
    for (r = 0; r < nrows; r++) {

	G_percent(r, nrows, 2);

	Rast_get_row(ele_fd, ele_buf, r, ele_map_type);
	ptr = ele_buf;

	if (acc_fd >= 0) {
	    Rast_get_row(acc_fd, acc_buf, r, acc_map_type);
	    acc_ptr = acc_buf;
	}

	for (c = 0; c < ncols; c++) {

	    flag_value_buf[c] = 0;
	    aspect[c] = 0;
	    stream_id[c] = 0;

	    /* check for masked and NULL cells */
	    if (Rast_is_null_value(ptr, ele_map_type)) {
		FLAG_SET(flag_value_buf[c], NULLFLAG);
		FLAG_SET(flag_value_buf[c], INLISTFLAG);
		FLAG_SET(flag_value_buf[c], WORKEDFLAG);
		FLAG_SET(flag_value_buf[c], WORKED2FLAG);
		Rast_set_c_null_value(&ele_value, 1);
		/* flow accumulation */
		Rast_set_d_null_value(&acc_value, 1);
	    }
	    else {
		switch (ele_map_type) {
		case CELL_TYPE:
		    ele_value = *((CELL *) ptr);
		    break;
		case FCELL_TYPE:
		    dvalue = *((FCELL *) ptr);
		    dvalue *= ele_scale;
		    ele_value = ele_round(dvalue);
		    break;
		case DCELL_TYPE:
		    dvalue = *((DCELL *) ptr);
		    dvalue *= ele_scale;
		    ele_value = ele_round(dvalue);
		    break;
		}
		if (acc_fd < 0)
		    acc_value = 1;
		else {
		    if (Rast_is_null_value(acc_ptr, acc_map_type))
			G_fatal_error(_("Accumulation map does not match elevation map!"));

		    switch (acc_map_type) {
		    case CELL_TYPE:
			acc_value = *((CELL *) acc_ptr);
			break;
		    case FCELL_TYPE:
			acc_value = *((FCELL *) acc_ptr);
			break;
		    case DCELL_TYPE:
			acc_value = *((DCELL *) acc_ptr);
			break;
		    }
		}

		n_points++;
	    }

	    wabuf[c].wat = acc_value;
	    wabuf[c].ele = ele_value;
	    ptr = G_incr_void_ptr(ptr, ele_size);
	    if (acc_fd >= 0)
		acc_ptr = G_incr_void_ptr(acc_ptr, acc_size);
	}
	seg_put_row(&watalt, (char *) wabuf, r);
	bseg_put_row(&asp, aspect, r);
	cseg_put_row(&stream, stream_id, r);
	bseg_put_row(&bitflags, flag_value_buf, r);
    }
    G_percent(nrows, nrows, 1);	/* finish it */

    Rast_close(ele_fd);
    G_free(ele_buf);
    G_free(wabuf);
    G_free(flag_value_buf);
    G_free(stream_id);
    G_free(aspect);

    if (acc_fd >= 0) {
	Rast_close(acc_fd);
	G_free(acc_buf);
    }
    
    G_debug(1, "%d non-NULL cells", n_points);

    return n_points;
}
