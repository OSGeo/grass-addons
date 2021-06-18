/* File: set_outline.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "raster.h"
#include "ps_info.h"
#include "local_proto.h"

int set_outline(void)
{
    int row, col;
    double nrow, n_rw, erow, e_rw;
    void *rbuf, *nbuf, *rptr, *nptr, *next;
    RASTER_MAP_TYPE map_type;

    /* let user know what's happenning */
    G_message(_("Reading raster map <%s in %s> ..."), PS.rst.name[0],
	      PS.rst.mapset[0]);

    /* set the outline color and width */
    set_ps_line(&(PS.rst.outline));

    fprintf(PS.fp, "GS 1 setlinejoin\n");	/* lines with linejoin = round */

    /* buffers of the image */
    map_type = G_get_raster_map_type(PS.rst.fd[0]);
    rbuf = G_allocate_raster_buf(map_type);
    nbuf = G_allocate_raster_buf(map_type);
    for (row = 0; row < PS.map.rows - 1; row++) {
	nrow = G_row_to_northing((double)row, &(PS.map));
	n_rw = G_row_to_northing((double)row + 1, &(PS.map));
	/* load buffers */
	G_get_raster_row(PS.rst.fd[0], rbuf, row, map_type);
	G_get_raster_row(PS.rst.fd[0], nbuf, row + 1, map_type);
	/* set pointers */
	rptr = rbuf;
	nptr = nbuf;
	for (col = 0; col < PS.map.cols - 1; col++) {
	    erow = G_col_to_easting((double)col + 1, &(PS.map));
	    e_rw = G_col_to_easting((double)col, &(PS.map));
	    /* check right outline */
	    next = G_incr_void_ptr(rptr, G_raster_size(map_type));
	    if (G_raster_cmp(rptr, next, map_type) != 0) {
		set_ps_where('M', erow, nrow);
		set_ps_where('L', erow, n_rw);
		fprintf(PS.fp, "S\n");
	    }
	    /* check bottom outline */
	    if (G_raster_cmp(rptr, nptr, map_type) != 0) {
		set_ps_where('M', e_rw, n_rw);
		set_ps_where('L', erow, n_rw);
		fprintf(PS.fp, "S\n");
	    }
	    /* next column */
	    rptr = G_incr_void_ptr(rptr, G_raster_size(map_type));
	    nptr = G_incr_void_ptr(nptr, G_raster_size(map_type));
	}
    }
    G_free(rbuf);
    G_free(nbuf);

    fprintf(PS.fp, "GR\n");
    return 0;
}
