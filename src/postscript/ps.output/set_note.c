/* File: set_note.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <grass/gis.h>
#include <grass/glocale.h>
#include "conversion.h"
#include "notes.h"
#include "ps_info.h"
#include "local_proto.h"


int note_in_file(char *name);

int set_note(int i)
{
    int rows, type;
    double x, y, dy, fontsize;
    char *chr, *str, txt[1024];

    rows = 0;			/* useful to decide if write it */
    fontsize = set_ps_font(&(PS.note[i].font));

    if (strncmp(PS.note[i].text, ":file", 5) == 0) {
	str = PS.note[i].text + 6;
	rows = note_in_file(str);
	type = -1;
    }
    else if (strncmp(PS.note[i].text, ":maplim", 7) == 0) {
	char label[50];

	/* get north, south, east and west strings */
	fprintf(PS.fp, "/ARo [\n");
	G_format_northing(PS.map.north, label, PS.map.proj);
	fprintf(PS.fp, "(North: %s)\n", label);
	G_format_easting(PS.map.west, label, PS.map.proj);
	fprintf(PS.fp, "(West: %s)\n", label);
	G_format_easting(PS.map.east, label, PS.map.proj);
	fprintf(PS.fp, "(East: %s)\n", label);
	G_format_northing(PS.map.south, label, PS.map.proj);
	fprintf(PS.fp, "(South: %s)\n", label);
	fprintf(PS.fp, "] def\n");
	rows = 4;
	type = 0;
    }
    else if (strncmp(PS.note[i].text, ":dimen", 6) == 0) {
	fprintf(PS.fp, "/ARo [\n");
	fprintf(PS.fp, "(Map Area)");
	fprintf(PS.fp, "(Position: %.1f mm x %.1f mm)\n",
		POINT_TO_MM * PS.map_x, POINT_TO_MM * PS.map_y);
	fprintf(PS.fp, "(Dimension: %.1f mm x %.1f mm)\n",
		POINT_TO_MM * PS.map_w, POINT_TO_MM * PS.map_h);
	fprintf(PS.fp, "] def\n");
	rows = 3;
	type = 1;
    }
    else if (strncmp(PS.note[i].text, ":scale", 6) == 0) {
	str = PS.note[i].text + 7;
	fprintf(PS.fp, "/ARo [(%s 1 : %d)] def\n", str, PS.scale);
	rows = 1;
	type = 2;
    }
    else {			/* free line of text with "|" to cut lines */
	fprintf(PS.fp, "/ARo [\n");
	chr = str = PS.note[i].text;
	while (*chr) {
	    while (*str && *str != '|')
		str++;
	    *str++ = '\0';
	    fprintf(PS.fp, "(%s)\n", chr);
	    chr = str;
	    ++rows;
	}
	fprintf(PS.fp, "] def\n");
	type = 4;
    }

    if (rows > 0) {
	/* Define ARw */
	if (PS.note[i].width > 0.) {
	    x = PS.note[i].box.margin;
	    if (x < 0.)
		x = 0.4 * PS.note[i].font.size;

	    fprintf(PS.fp, "/ARw [%.3f] def\n", PS.note[i].width - 2 * x);
	}
	else
	    fprintf(PS.fp, "/ARw [ARo SWx] def\n");
	//fprintf(PS.fp, "/ARw 1 array def ARw 0 ARo SWx put\n");

	/* Define ARh: todas de igual altura */
	fprintf(PS.fp, "/ARh ARo length array def ");
	fprintf(PS.fp, "0 1 ARo length -- {ARh exch %.2f put} for\n",
		fontsize);

	/* Make de frame */
	set_box_orig(&(PS.note[i].box));
	set_box_auto(&(PS.note[i].box), &(PS.note[i].font), 0.25);
	set_box_draw(&(PS.note[i].box));
	set_ps_color(&(PS.note[i].font.color));

	/* Draw the content */
	fprintf(PS.fp, "RESET ");

	fprintf(PS.fp,
		"0 1 ARo length 1 sub {dup ROW ARo exch get x y ARh row get sub M ");
	switch (type) {
	case 0:
	    fprintf(PS.fp,
		    "GS dup SW ARw 0 get exch sub 0 32 4 -1 roll widthshow GR");
	    break;

	case 2:
	    fprintf(PS.fp, "GS dup SWH exch pop 0 MR %.2f ROT show GR",
		    PS.note[i].angle);
	    break;

	default:
	    fprintf(PS.fp,
		    "(.) anchorsearch {GS pop %.3f 2 div 0 MR SHC GR} {SHL} ifelse",
		    PS.note[i].width);
	    break;
	}
	fprintf(PS.fp, "} for\n");
    }

    return 0;
}

int note_in_file(char *name)
{
    FILE *in = NULL;
    char buf[1024];
    int r = 0;

    if (*name) {
	in = fopen(name, "r");
	if (in == NULL) {
	    G_message(_("Comment file <%s> can't open"), name);
	    return 0;
	}
    }
    fprintf(PS.fp, "/ARo [\n");
    while (fgets(buf, sizeof(buf), in)) {	/* TODO don't read end-of-line */
	fprintf(PS.fp, "(%s)\n", buf);
	++r;
    }
    fprintf(PS.fp, "] def\n");
    fclose(in);

    return r;
}
