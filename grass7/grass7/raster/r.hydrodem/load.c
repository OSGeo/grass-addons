#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

int ele_round(double x)
{
    return (x > 0.0 ? x + .5 : x - .5);
}

/*
 * loads elevation map to segment file and gets start points for A* Search,
 * start points are edges
 */
int load_map(int ele_fd)
{
    int r, c;
    char flag_value, asp_value = 0;
    void *ele_buf, *ptr;
    CELL ele_value;
    DCELL dvalue;
    int ele_size;
    int ele_map_type;

    G_message(_("Load elevation map"));

    n_search_points = n_points = 0;

    ele_map_type = Rast_get_map_type(ele_fd);
    ele_size = Rast_cell_size(ele_map_type);
    ele_buf = Rast_allocate_buf(ele_map_type);

    if (ele_buf == NULL) {
	G_warning(_("Could not allocate memory"));
	return -1;
    }

    ele_scale = 1;
    if (ele_map_type == FCELL_TYPE || ele_map_type == DCELL_TYPE)
	ele_scale = 1000;	/* should be enough to do the trick */

    G_debug(1, "start loading %d rows, %d cols", nrows, ncols);
    for (r = 0; r < nrows; r++) {

	G_percent(r, nrows, 2);

	Rast_get_row(ele_fd, ele_buf, r, ele_map_type);
	ptr = ele_buf;

	for (c = 0; c < ncols; c++) {

	    flag_value = 0;

	    /* check for masked and NULL cells */
	    if (Rast_is_null_value(ptr, ele_map_type)) {
		FLAG_SET(flag_value, NULLFLAG);
		FLAG_SET(flag_value, INLISTFLAG);
		FLAG_SET(flag_value, WORKEDFLAG);
		FLAG_SET(flag_value, WORKED2FLAG);
		Rast_set_c_null_value(&ele_value, 1);
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

		n_points++;
	    }

	    cseg_put(&ele, &ele_value, r, c);
	    bseg_put(&draindir, &asp_value, r, c);
	    bseg_put(&bitflags, &flag_value, r, c);

	    ptr = G_incr_void_ptr(ptr, ele_size);
	}
    }
    G_percent(nrows, nrows, 1);	/* finish it */

    Rast_close(ele_fd);
    G_free(ele_buf);

    G_debug(1, "%d non-NULL cells", n_points);

    return 1;
}
