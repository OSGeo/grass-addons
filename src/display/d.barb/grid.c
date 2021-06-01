#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/display.h>
#include <grass/glocale.h>
#include "local_proto.h"


/* load and plot barbs from data stored in two raster maps */
void do_barb_grid(char *dir_u_map, char *mag_v_map, int is_component,
		  int color, int aspect_type, double scale, double setpeak,
		  int skip, int style, int reverse)
{
    /* from d.rast.arrow */
    struct FPRange range;
    double mag_min, mag_max;
    int dir_u_fd, mag_v_fd;
    RASTER_MAP_TYPE dir_u_raster_type, mag_v_raster_type;
    void *dir_u_raster_row, *mag_v_raster_row, *dir_u_ptr, *mag_v_ptr;
    struct Cell_head window;
    int nrows, ncols, row, col;
    int no_arrow;		/* boolean */
    double aspect_f = -1.0, theta;
    double length = -1.0, r;
    double easting, northing;

    G_debug(1, "Doing Eulerian field ...");

    /* figure out arrow scaling */
    G_init_fp_range(&range);	/* really needed? */
    if (G_read_fp_range(mag_v_map, "", &range) != 1)
	G_fatal_error(_("Problem reading range file"));
    G_get_fp_range_min_max(&range, &mag_min, &mag_max);

    if (!isnan(setpeak))
	mag_max = setpeak;

    if (style == TYPE_ARROW || style == TYPE_STRAW) {
	scale *= 1.5 / fabs(mag_max);
    }
    G_debug(3, "scaling=%.2f  rast_max=%.2f", scale, mag_max);

    // howto figure for u,v maps where max_mag is not known until combined in render step?


    /* open the direction (or u-component) raster map */
    dir_u_fd = G_open_cell_old(dir_u_map, "");
    if (dir_u_fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), dir_u_map);
    dir_u_raster_type = G_get_raster_map_type(dir_u_fd);

    /* open the magnitude (or v-component) raster map */
    mag_v_fd = G_open_cell_old(mag_v_map, "");
    if (mag_v_fd < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), mag_v_map);
    mag_v_raster_type = G_get_raster_map_type(mag_v_fd);


    /* allocate the cell array */
    dir_u_raster_row = G_allocate_raster_buf(dir_u_raster_type);
    mag_v_raster_row = G_allocate_raster_buf(mag_v_raster_type);

    /* number of rows and cols in region */
    G_get_window(&window);
    nrows = window.rows;
    ncols = window.cols;

    /* loop through cells, find value, determine direction (n,s,e,w,ne,se,sw,nw),
       and call appropriate function to draw an arrow on the cell */

    for (row = 0; row < nrows; row++) {
	G_get_raster_row(dir_u_fd, dir_u_raster_row, row, dir_u_raster_type);
	dir_u_ptr = dir_u_raster_row;

	// should magnitude be mandatory?
	if (mag_v_map) {
	    G_get_raster_row(mag_v_fd, mag_v_raster_row, row,
			     mag_v_raster_type);
	    mag_v_ptr = mag_v_raster_row;
	}

	for (col = 0; col < ncols; col++) {

	    if (row % skip != 0)
		no_arrow = TRUE;
	    else
		no_arrow = FALSE;

	    if (col % skip != 0)
		no_arrow = TRUE;

	    /* find aspect direction based on cell value */
	    if (dir_u_raster_type == CELL_TYPE)
		aspect_f = *((CELL *) dir_u_ptr);
	    else if (dir_u_raster_type == FCELL_TYPE)
		aspect_f = *((FCELL *) dir_u_ptr);
	    else if (dir_u_raster_type == DCELL_TYPE)
		aspect_f = *((DCELL *) dir_u_ptr);


	    if (mag_v_raster_type == CELL_TYPE)
		length = *((CELL *) mag_v_ptr);
	    else if (mag_v_raster_type == FCELL_TYPE)
		length = *((FCELL *) mag_v_ptr);
	    else if (mag_v_raster_type == DCELL_TYPE)
		length = *((DCELL *) mag_v_ptr);


	    if (G_is_null_value(mag_v_ptr, mag_v_raster_type)) {
		G_debug(5, "Invalid arrow length [NULL]. Skipping.");
		no_arrow = TRUE;
	    }
	    else if (length < 0 && !is_component) {	/* use fabs() or theta+=180? */
		G_debug(5, "Illegal arrow length [%.3f]. Skipping.", length);
		no_arrow = TRUE;
	    }

	    if (no_arrow) {
		dir_u_ptr =
		    G_incr_void_ptr(dir_u_ptr,
				    G_raster_size(dir_u_raster_type));
		if (mag_v_map)
		    mag_v_ptr =
			G_incr_void_ptr(mag_v_ptr,
					G_raster_size(mag_v_raster_type));
		no_arrow = FALSE;
		continue;
	    }

	    if (is_component) {
		/* convert u,v to dir,mag */
		r = sqrt(length * length + aspect_f * aspect_f);
		theta = R2D(atan2(length, aspect_f));
		length = r;
		aspect_f = theta;
		if (aspect_f < 0)
		    aspect_f += 360;
		else if (aspect_f > 360)
		    aspect_f -= 360;
	    }

	    /* convert Cartesian to compass convention */
	    if (aspect_type == TYPE_GRASS)
		aspect_f = 90 - aspect_f;

	    if (aspect_f < 0)
		aspect_f += 360;
	    else if (aspect_f > 360)
		aspect_f -= 360;

	    if (reverse)
		aspect_f += 180;
	    if (aspect_f > 360)
		aspect_f -= 360;

	    length *= scale;

	   /** Now draw the arrows **/
	    if (G_is_null_value(dir_u_ptr, dir_u_raster_type))
		continue;

	    D_raster_use_color(color);

	    easting = G_col_to_easting(col + 0.5, &window);
	    northing = G_row_to_northing(row + 0.5, &window);


	    if (aspect_f >= 0.0 && aspect_f <= 360.0) {
		if (mag_v_map) {
		    draw_barb(easting, northing, length, aspect_f,
			      color, scale, style);
		}
		else {
		    //todo   arrow_360(aspect_f);
		    draw_barb(easting, northing, 1.0, aspect_f,
			      color, scale, style);
		}
	    }
	    else {
		R_standard_color(D_parse_color("grey", 0));
		unknown_(easting, northing);
		D_raster_use_color(color);
	    }

	    dir_u_ptr =
		G_incr_void_ptr(dir_u_ptr, G_raster_size(dir_u_raster_type));
	    mag_v_ptr =
		G_incr_void_ptr(mag_v_ptr, G_raster_size(mag_v_raster_type));
	}
    }

    G_close_cell(dir_u_fd);
    G_close_cell(mag_v_fd);

    return;
}
