/* File: set_raster.c
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

#define NTSC(r,g,b) (.30*(double)r + .59*(double)g + .11*(double)b)
#define GREY(r,g,b) ((double)(r + g + b)/3.)


/* the PS file can be reduced to half if don't use ASCIIHexDecode filter and writing
   directly with %c, not with %02X, but the PS file is less friendly and this is not important
   when after all the PS file is transformed to PDF */

int set_raster(void)
{
    int i;

    /* starting */
    if (PS.need_mask && PS.rst.do_mask) {
	fprintf(PS.fp,
		"currentfile /ASCIIHexDecode filter /ReusableStreamDecode filter\n");
    }
    else {
	fprintf(PS.fp, "GS\n");
	/* Map Dictionary when no mask needed, no reusable stream */
	fprintf(PS.fp, "/Device%s setcolorspace\n",
		PS.rst.do_grey ? "Gray" : "RGB");
	fprintf(PS.fp, "%.2f %.2f translate\n", PS.map_x, PS.map_y);
	fprintf(PS.fp, "%.1f %.1f scale\n", PS.map_w, PS.map_h);
	fprintf(PS.fp, "<< /ImageType 1\n");
	fprintf(PS.fp, "   /Width %d\n", PS.map.cols);
	fprintf(PS.fp, "   /Height %d\n", PS.map.rows);
	fprintf(PS.fp, "   /BitsPerComponent 8\n");
	/* fprintf(PS.fp, "   /Interpolate true\n"); */
	fprintf(PS.fp, "   /Decode [%s]\n",
		PS.rst.do_grey ? "0 1" : "0 1 0 1 0 1");
	fprintf(PS.fp, "   /ImageMatrix [%d 0 0 %d 0 %d]\n", PS.map.cols,
		-PS.map.rows, PS.map.rows);
	fprintf(PS.fp, "   /DataSource currentfile /ASCIIHexDecode filter\n");
	fprintf(PS.fp, ">> ");
	fprintf(PS.fp, "image\n");
    }
    /* split loading stream for some better speed */
    if (PS.rst.do_rgb) {
	set_raster_rgb();
    }
    else if (PS.rst.do_mask) {
	if (PS.rst.fd[2] < 0)
	    set_raster_maskcolor();
	else
	    set_raster_maskcell();
    }
    else {
	set_raster_cell();
    }
    /* ending */
    if (PS.need_mask && PS.rst.do_mask) {
	fprintf(PS.fp, "\n> ");
	fprintf(PS.fp, "/mapstream exch def\n");
	/* Map Dictionary when mask needed, reusable stream */
	fprintf(PS.fp, "/MapDictionary \n");
	fprintf(PS.fp, "<< /ImageType 1\n");
	fprintf(PS.fp, "   /Width %d\n", PS.map.cols);
	fprintf(PS.fp, "   /Height %d\n", PS.map.rows);
	fprintf(PS.fp, "   /BitsPerComponent 8\n");
	/* fprintf(PS.fp, "   /Interpolate true\n"); */
	fprintf(PS.fp, "   /Decode [%s]\n",
		PS.rst.do_grey ? "0 1" : "0 1 0 1 0 1");
	fprintf(PS.fp, "   /ImageMatrix [%d 0 0 %d 0 %d]\n", PS.map.cols,
		-PS.map.rows, PS.map.rows);
	fprintf(PS.fp, "   /DataSource mapstream\n");
	fprintf(PS.fp, ">> store\n");
	fprintf(PS.fp, "gsave\n");
	fprintf(PS.fp, "  /Device%s setcolorspace\n",
		PS.rst.do_grey ? "Gray" : "RGB");
	fprintf(PS.fp, "  %.2f %.2f translate\n", PS.map_x, PS.map_y);
	fprintf(PS.fp, "  %.1f %.1f scale\n", PS.map_w, PS.map_h);
	fprintf(PS.fp, "  mapstream resetfile\n");
	fprintf(PS.fp, "  MapDictionary image\n");
    }
    else {
	fprintf(PS.fp, ">\n");
    }
    fprintf(PS.fp, "GR\n");

    return 0;
}

/** Process one file with colors */
int set_raster_cell(void)
{
    int row, col, br, R, G, B;
    void *cbuf, *cptr;
    RASTER_MAP_TYPE map_type;


    /* let user know what's happenning */
    G_message(_("Reading raster map <%s in %s> ..."), PS.rst.name[0],
	      PS.rst.mapset[0]);

    /* storing the bytes of the image */
    map_type = G_get_raster_map_type(PS.rst.fd[0]);
    cbuf = G_allocate_raster_buf(map_type);
    for (br = 0, row = 0; row < PS.map.rows; row++) {
	G_get_raster_row(PS.rst.fd[0], cbuf, row, map_type);
	cptr = cbuf;
	for (col = 0; col < PS.map.cols; col++) {
	    /* get the map colors */
	    G_get_raster_color(cptr, &R, &G, &B, &(PS.rst.colors[0]),
			       map_type);
	    cptr = G_incr_void_ptr(cptr, G_raster_size(map_type));
	    /* processing data to the postscript file */
	    if (PS.rst.do_grey) {
		fprintf(PS.fp, "%02X", (int)NTSC(R, G, B));
	    }
	    else {
		fprintf(PS.fp, "%02X%02X%02X", R, G, B);
	    }
	    if (br++ == 15) {
		br = 0;
		fprintf(PS.fp, "\n");
	    }
	}
    }
    G_free(cbuf);

    return 1;
}

/** Process three files as RGB color */
int set_raster_rgb(void)
{
    int i, row, col, br;
    int R[3], G[3], B[3];
    void *cbuf[3], *cptr[3];
    RASTER_MAP_TYPE map_type[3];


    /* let user know what's happenning */
    G_message(_("Reading raster maps in group <%s> ..."), PS.rst.title);

    /* storing the bytes of the image */
    for (i = 0; i < 3; i++) {
	map_type[i] = G_get_raster_map_type(PS.rst.fd[i]);
	cbuf[i] = G_allocate_raster_buf(map_type[i]);
    }
    for (br = 0, row = 0; row < PS.map.rows; row++) {
	for (i = 0; i < 3; i++) {
	    G_get_raster_row(PS.rst.fd[i], cbuf[i], row, map_type[i]);
	    cptr[i] = cbuf[i];
	}
	for (col = 0; col < PS.map.cols; col++) {
	    /* get the map colors */
	    G_get_raster_color(cptr[0], &(R[0]), &(G[0]), &(B[0]),
			       &(PS.rst.colors[0]), map_type[0]);
	    G_get_raster_color(cptr[1], &(R[1]), &(G[1]), &(B[1]),
			       &(PS.rst.colors[1]), map_type[1]);
	    G_get_raster_color(cptr[2], &(R[2]), &(G[2]), &(B[2]),
			       &(PS.rst.colors[2]), map_type[2]);
	    /* processing data to the postscript file */
	    if (PS.rst.do_grey) {
		fprintf(PS.fp, "%02X", (int)NTSC(R[0], G[1], B[2]));
	    }
	    else {
		fprintf(PS.fp, "%02X%02X%02X", R[0], G[1], B[2]);
	    }
	    if (br++ == 15) {
		br = 0;
		fprintf(PS.fp, "\n");
	    }
	    /* pointer to next column */
	    cptr[0] = G_incr_void_ptr(cptr[0], G_raster_size(map_type[0]));
	    cptr[1] = G_incr_void_ptr(cptr[1], G_raster_size(map_type[1]));
	    cptr[2] = G_incr_void_ptr(cptr[2], G_raster_size(map_type[2]));
	}
    }
    for (i = 0; i < 3; i++) {
	G_free(cbuf[i]);
	G_close_cell(PS.rst.fd[i]);
	G_free_colors(&(PS.rst.colors[i]));
	PS.rst.fd[i] = -1;
    }

    return 3;
}


/** Process three files as raster, mask and background */
int set_raster_maskcell(void)
{
    int i, row, col, br;
    int r, g, b, R[3], G[3], B[3];
    double f, red, green, blue;
    void *cbuf[3], *cptr[3];
    RASTER_MAP_TYPE map_type[3];

    red = (1. - PS.rst.mask_color.r);
    green = (1. - PS.rst.mask_color.g);
    blue = (1. - PS.rst.mask_color.b);
    R[1] = (int)(255. * PS.rst.mask_color.r);
    G[1] = (int)(255. * PS.rst.mask_color.g);
    B[1] = (int)(255. * PS.rst.mask_color.b);

    /* let user know what's happenning */
    G_message(_("Reading raster map <%s in %s> ... %d rows"), PS.rst.name[0],
	      PS.rst.mapset[0], PS.map.rows);
    G_message(_("... mask raster <%s in %s>"), PS.rst.name[1],
	      PS.rst.mapset[1]);
    G_message(_("... background raster <%s in %s>"), PS.rst.name[2],
	      PS.rst.mapset[2]);

    /* storing the bytes of the image */
    for (i = 0; i < 3; i++) {
	map_type[i] = G_get_raster_map_type(PS.rst.fd[i]);
	cbuf[i] = G_allocate_raster_buf(map_type[i]);
    }
    for (br = 0, row = 0; row < PS.map.rows; row++) {
	for (i = 0; i < 3; i++) {
	    /* G_get_raster_row(PS.rst.fd[i], cbuf[i], row, map_type[i]); */
	    G_get_raster_row_nomask(PS.rst.fd[i], cbuf[i], row, map_type[i]);
	    cptr[i] = cbuf[i];
	}
	for (col = 0; col < PS.map.cols; col++) {
	    /* get the map colors */
	    G_get_raster_color(cptr[0], &(R[0]), &(G[0]), &(B[0]),
			       &(PS.rst.colors[0]), map_type[0]);
	    G_get_raster_color(cptr[2], &(R[2]), &(G[2]), &(B[2]),
			       &(PS.rst.colors[2]), map_type[2]);
	    /* select color by mask */
	    if (G_is_null_value(cptr[1], map_type[1])) {
		if (PS.rst.mask_color.none) {
		    r = R[2];
		    g = G[2];
		    b = B[2];
		}
		else {
		    f = (double)GREY(R[2], G[2], B[2]);
		    r = (int)(f * red + (double)R[1]);
		    g = (int)(f * green + (double)G[1]);
		    b = (int)(f * blue + (double)B[1]);
		}
	    }
	    else {
		r = R[0];
		g = G[0];
		b = B[0];
	    }
	    /* processing data to the postscript file */
	    if (PS.rst.do_grey) {
		fprintf(PS.fp, "%02X", (int)NTSC(r, g, b));
	    }
	    else {
		fprintf(PS.fp, "%02X%02X%02X", r, g, b);
	    }
	    if (br++ == 15) {
		fprintf(PS.fp, "\n");
		br = 0;
	    }
	    /* pointer to next column */
	    cptr[0] = G_incr_void_ptr(cptr[0], G_raster_size(map_type[0]));
	    cptr[1] = G_incr_void_ptr(cptr[1], G_raster_size(map_type[1]));
	    cptr[2] = G_incr_void_ptr(cptr[2], G_raster_size(map_type[2]));
	}
    }
    G_free(cbuf[0]);
    G_free(cbuf[1]);
    G_free(cbuf[2]);

    return 3;
}


/** Process two files as raster and mask */
int set_raster_maskcolor(void)
{
    int i, row, col, br;
    int color, r, g, b, R, G, B;
    void *cbuf[2], *cptr[2];
    RASTER_MAP_TYPE map_type[2];

    if (PS.rst.mask_color.none) {
	r = g = b = 255.;
    }
    else {
	r = (int)(255. * PS.rst.mask_color.r);
	g = (int)(255. * PS.rst.mask_color.g);
	b = (int)(255. * PS.rst.mask_color.b);
    }

    /* let user know what's happenning */
    G_message(_("Reading raster map <%s in %s> ... %d rows"), PS.rst.name[0],
	      PS.rst.mapset[0], PS.map.rows);
    G_message(_("... raster to mask <%s in %s>"), PS.rst.name[1],
	      PS.rst.mapset[1]);

    /* storing the bytes of the image */
    for (i = 0; i < 2; i++) {
	map_type[i] = G_get_raster_map_type(PS.rst.fd[i]);
	cbuf[i] = G_allocate_raster_buf(map_type[i]);
    }
    for (br = 0, row = 0; row < PS.map.rows; row++) {
	for (i = 0; i < 2; i++) {
	    G_get_raster_row(PS.rst.fd[i], cbuf[i], row, map_type[i]);
	    cptr[i] = cbuf[i];
	}
	for (col = 0; col < PS.map.cols; col++) {
	    /* get the map colors */
	    G_get_raster_color(cptr[0], &R, &G, &B, &(PS.rst.colors[0]),
			       map_type[0]);
	    /* select color by mask */
	    if (G_is_null_value(cptr[1], map_type[1])) {
		R = r;
		G = g;
		B = b;
	    }
	    /* processing data to the postscript file */
	    if (PS.rst.do_grey) {
		fprintf(PS.fp, "%02X", (int)NTSC(R, G, B));
	    }
	    else {
		fprintf(PS.fp, "%02X%02X%02X", R, G, B);
	    }
	    if (br++ == 15) {
		br = 0;
		fprintf(PS.fp, "\n");
	    }
	    /* pointer to next column */
	    cptr[0] = G_incr_void_ptr(cptr[0], G_raster_size(map_type[0]));
	    cptr[1] = G_incr_void_ptr(cptr[1], G_raster_size(map_type[1]));
	}
    }
    G_free(cbuf[0]);
    G_free(cbuf[1]);

    return 2;
}
