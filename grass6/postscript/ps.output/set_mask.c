/* File: set_mask.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
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


int set_mask(void)
{
    int i, byte, row, col, br;
    void *cbuf, *cptr;
    RASTER_MAP_TYPE map_type;
    static int bit[] = { 128, 64, 32, 16, 8, 4, 2, 1 };


    if (PS.rst.fd[1] < 0) {	/* there is no mask */
	G_warning(_("Any raster mask to read, don't mask!"));
	if (PS.need_mask)
	    PS.need_mask = 0;
	return 0;
    }

    fprintf(PS.fp,
	    "currentfile /ASCIIHexDecode filter /ReusableStreamDecode filter\n");

    /* storing the bytes of the mask */
    map_type = G_get_raster_map_type(PS.rst.fd[1]);
    cbuf = G_allocate_raster_buf(map_type);
    for (br = 0, row = 0; row < PS.map.rows; row++) {
	G_get_raster_row(PS.rst.fd[1], cbuf, row, map_type);
	cptr = cbuf;
	i = byte = 0;
	for (col = 0; col < PS.map.cols; col++) {
	    if (G_is_null_value(cptr, map_type)) {
		byte |= bit[i];
	    }
	    ++i;
	    if (i == 8) {
		fprintf(PS.fp, "%02x", byte);
		i = byte = 0;
	    }
	    if (br++ == 45) {
		br = 0;
		fprintf(PS.fp, "\n");
	    }
	    cptr = G_incr_void_ptr(cptr, G_raster_size(map_type));
	}
	if (i) {
	    while (i < 8)
		byte |= bit[i++];
	    fprintf(PS.fp, "%02x", byte);
	}
    }
    fprintf(PS.fp, "\n> /maskstream exch def\n");

    /* Mask Dictionary */
    /*     fprintf(PS.fp, "  /Device%s setcolorspace\n", PS.rst.do_grey ? "Gray" : "RGB"); */
    fprintf(PS.fp, "/MaskDictionary\n");
    fprintf(PS.fp, "<< /ImageType 1\n");
    fprintf(PS.fp, "   /Width %d\n", PS.map.cols);
    fprintf(PS.fp, "   /Height %d\n", PS.map.rows);
    fprintf(PS.fp, "   /BitsPerComponent 1\n");
    /* fprintf(PS.fp, "   /Interpolate true\n"); */
    fprintf(PS.fp, "   /Decode [1 0]\n");
    fprintf(PS.fp, "   /ImageMatrix [%d 0 0 %d 0 %d]\n", PS.map.cols,
	    -PS.map.rows, PS.map.rows);
    fprintf(PS.fp, "   /DataSource maskstream\n");
    fprintf(PS.fp, ">> store\n");

    /* Now draw the masked image */
    fprintf(PS.fp, "maskstream resetfile\n");
    fprintf(PS.fp, "mapstream resetfile\n");
    fprintf(PS.fp, "gsave\n");
    fprintf(PS.fp, "  /Device%s setcolorspace\n",
	    PS.rst.do_grey ? "Gray" : "RGB");
    fprintf(PS.fp, "  %.2f %.2f translate\n", PS.map_x, PS.map_y);
    fprintf(PS.fp, "  %.1f %.1f scale\n", PS.map_w, PS.map_h);
    fprintf(PS.fp, "  << /ImageType 3\n");
    fprintf(PS.fp, "     /InterleaveType 3\n");
    fprintf(PS.fp, "     /MaskDict MaskDictionary\n");
    fprintf(PS.fp, "     /DataDict MapDictionary\n");
    fprintf(PS.fp, "  >> image\n");
    fprintf(PS.fp, "grestore\n");

    /* no more needed the reusable streams */
    fprintf(PS.fp, "maskstream closefile\n");
    fprintf(PS.fp, "mapstream closefile\n");

    return 0;
}
