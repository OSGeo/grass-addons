/* File: set_draw.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */
#include <string.h>
#include <math.h>
#include <grass/symbol.h>
#include <grass/gprojects.h>
#include "frames.h"
#include "ps_info.h"
#include "local_proto.h"

#define PI   3.14159265359

#define KEY(x) (strcmp(x,key)==0)
#define CODE(x) strcmp(x,code)==0

void label_in_file(char *);

static PSCOLOR fcolor;

int set_draw(char *key, char *data)
{
    char h, label[100], buf[256];
    char e1[20], n1[20], e2[20], n2[20];
    int i, x, y, dg, mg;
    double east, north, lw, d, sg;
    PSCOLOR color;

    if (KEY("direct")) {
	fprintf(PS.fp, " %s ", data);
    }
    else if (KEY("color")) {
	if (!scan_color(data, &color))
	    error(key, data, "color: color");
	set_ps_color(&color);
    }
    else if (KEY("fcolor")) {
	scan_color(data, &fcolor);
    }
    else if (KEY("linewidth")) {
	if (sscanf(data, "%s", label) != 1 || scan_dimen(label, &lw) != 1)
	    error(key, data, "linewidth: width");
	fprintf(PS.fp, "%.1f LW ", lw);
    }
    else if (KEY("linedash")) {
	if (sscanf(data, "%[^\n]", label) != 1)
	    fprintf(PS.fp, "[] 0 LD ");
	else
	    fprintf(PS.fp, "[%s] 0 LD ", label);
    }
    else if (KEY("font")) {
	i = sscanf(data, "%s %s %lf", label, buf, &d);
	if ((i != 2 && i != 3) || (scan_dimen(buf, &lw) != 1))

	    error(key, data, "font: name, size, and [extend]");

	fprintf(PS.fp, "(%s) FN %.1f ", label, lw);
	if (i == 2)
	    fprintf(PS.fp, "FS ");
	else
	    fprintf(PS.fp, "%.2f FE ", d);
    }
    /* Drawing text */
    else if (KEY("text") ||
	     KEY("ltext") ||
	     KEY("ctext") || KEY("rtext") || KEY("xtext") || KEY("vtext")) {
	if (sscanf(data, "%s %s %[^\n]", e1, n1, label) != 3)
	    error(key, data, "text: east, north and text");

	if (atoi(e1) < 0) {
	    fprintf(PS.fp, "GS %s ROT (%s) ", n1, label);
	}
	else {
	    sprintf(buf, "M (%s) ", label);
	    set_on_paper("GS", e1, n1, buf);
	}
	switch (*key) {
	case 'x':
	    strcpy(buf, "SHCC");
	    break;
	case 'c':
	    strcpy(buf, "SHC");
	    break;
	case 'r':
	    strcpy(buf, "SHR");
	    break;
	case 'v':
	    strcpy(buf, "SVC");
	    break;
	default:
	    strcpy(buf, "TXT");
	    break;
	}
	fprintf(PS.fp, "%s GR\n", buf);
    }
    else if (KEY("-text")) {
	fprintf(PS.fp, " (%s) SHL ", data);
    }
    else if (KEY("textc")) {
	if (sscanf(data, "%s %s %[^\n]", e1, n1, label) != 3)
	    error(key, data, "ctext: east, north, and text");

	sprintf(buf, "M GS (%s) dup SHCC GR "
		"SWH 2 copy gt {pop} {exch pop} ifelse 2 div 2 add "
		"cP 3 -1 roll 0 360 NP arc CP S\n", label);
	set_on_paper("", e1, n1, buf);
    }
    else if (KEY("labels") || KEY("label")) {
	if (sscanf(data, "%s", label) != 1)
	    error(key, data, "labels: filename");
	label_in_file(label);
    }
    /* Drawing paths */
    else if (KEY("moveto")) {
	if (sscanf(data, "%s %s", e1, n1) != 2)
	    error(key, data, "moveto: east and north");
	set_on_paper("", e1, n1, "M ");
    }
    else if (KEY("lineto") || KEY("ruteto")) {
	switch (sscanf(data, "%s %s %[^\n]", e1, n1, buf)) {
	case 2:
	    set_on_paper("", e1, n1, "L ");
	    break;
	case 3:
	    set_on_paper("cP exch 2 copy", e1, n1, "L GS cP 2 copy 8 2 roll");
	    fprintf(PS.fp,
		    " 4 -1 roll add 2 div 3 1 roll add 2 div exch M"
		    " 4 1 roll sub 3 1 roll exch sub atan ROT 0 2 MR (%s) SHC S GR\n",
		    buf);
	    break;
	default:
	    error(key, data, "lineto: east, north, and [text]");
	}
    }
    else if (KEY("endline")) {
	fprintf(PS.fp, " S");
    }
    else if (KEY("line")) {
	if (sscanf(data, "%s %s %s %s", e1, n1, e2, n2) != 4)
	    error(key, data, "line: east/north east/north");

	set_on_paper("", e1, n1, "M");
	/* if e2 < 0 polares angulo y longitud */
	set_on_paper("", e2, n2, "LS\n");
    }
    else if (KEY("border")) {
	if (sscanf(data, "%s", label) != 1 || scan_dimen(label, &d) != 1)
	    error(key, data, "border: width");
	set_ps_brd(d);
    }
    else if (KEY("rect") || KEY("rectangle")) {
	switch (sscanf(data, "%s %s %s %s %s", e1, n1, e2, n2, buf)) {
	case 4:
	    set_on_paper("", e1, n1, "");
	    set_on_paper("", e2, n2, "B S\n");
	    break;
	case 5:
	    scan_color(buf, &color);
	    set_on_paper("", e1, n1, "");
	    set_on_paper("", e2, n2, "B GS ");
	    set_ps_color(&color);
	    fprintf(PS.fp, "fill GR S\n");
	    break;
	default:
	    error(key, data,
		  "rectangle: east/north and east/north [fill color])");
	}
    }
    else if (KEY("circ") || KEY("circle")) {
	if (sscanf(data, "%s %s %lf", e1, n1, &d) != 3)
	    error(key, data, "circle: x, y and radius");

	sprintf(buf, "%.1f 0 360 arc S\n",
		d * (MT_TO_POINT / (double)PS.scale));
	set_on_paper("", e1, n1, buf);
    }
    else if (KEY("arc")) {
	if (sscanf(data, "%s %s %lf %s %s", e1, n1, &d, e2, n2) != 5)
	    error(key, data, "arc need 5 parameters");

	set_on_paper("", e1, n1, "");
	sprintf(buf, "%.1f", d * (MT_TO_POINT / (double)PS.scale));
	set_on_paper(buf, e2, n2, "arc S\n");
    }
    /* Include files */
    else if (KEY("psfile") || KEY("epsfile")) {
	if (sscanf(data, "%lf %s %s %s", &d, e1, n1, label) != 4) {
	    error(key, data, "psfile: scale, east, north, and filename");
	}
	set_on_paper("GS", e1, n1, "TR ");
	fprintf(PS.fp, "%.2f dup scale ", d);
	FILE *fp;

	if ((fp = fopen(label, "r")) != NULL) {
	    G_message("Reading PostScript file <%s> ...", label);
	    fprintf(PS.fp, "\n");
	    /*
	       while (fgets(buf, 256, fp) != NULL)
	       fprintf(PS.fp, "%s", buf);
	     */
	    while (fgets(buf, 256, fp) != NULL) {
		if (strcmp(buf, "showpage\n") == 0)
		    continue;
		fprintf(PS.fp, "%s", buf);
	    }
	    fprintf(PS.fp, "\n");
	    fclose(fp);
	}
	fprintf(PS.fp, "GR\n");
    }
    /* Drawing complements */
    else if (KEY("maplimit") || KEY("maplimits")) {
	if (sscanf(data, "%s", label) != 1)
	    d = 0.;
	else
	    scan_dimen(label, &d);

	fprintf(PS.fp, "%.1f %.1f add %.1f %.1f add M ", PS.map_right, d,
		PS.map_top, d);
	format_northing(PS.map.north, buf, PS.map.proj);
	fprintf(PS.fp, "GS (%s) dup SWH ++ neg dup MR pop SHR GR\n", buf);
	format_easting(PS.map.east, buf, PS.map.proj);
	fprintf(PS.fp,
		"GS (%s) dup SWH ++ dup neg 3 1 roll add neg MR 270 ROT SHR GR\n",
		buf);

	fprintf(PS.fp, "%.1f %.1f sub %.1f %.1f sub M ", PS.map_x, d,
		PS.map_y, d);
	format_northing(PS.map.south, buf, PS.map.proj);
	fprintf(PS.fp, "GS (%s) dup SWH ++ 1 MR pop SHL GR\n", buf);
	format_easting(PS.map.west, buf, PS.map.proj);
	fprintf(PS.fp, "GS (%s) dup SWH ++ dup MR pop 90 ROT SHL GR\n", buf);
    }
    else if (KEY("northarrow") || KEY("north")) {
	switch (sscanf(data, "%s %s %s", e1, n1, buf)) {
	case 2:
	    sprintf(buf,
		    "M 5 dup neg dup 3 mul LR dup dup LR dup neg LR CP cP S M 0 2 MR (N) SHC\n");
	    set_on_paper("NP .2 mm LW", e1, n1, buf);
	    break;
	case 3:
	    sprintf(buf, "M GS "
		    "/rl {67.5 sin mul exch 67.5 cos mul exch rlineto} D "
		    "0 90 360 {ROT GS 8 8 rl -8 16 rl 0 -24 rl fill GR GS -8 8 rl 8 16 rl S GR} for "
		    "45 ROT 0 90 360 {ROT GS 8 8 rl -8 8 rl 0 -16 rl fill GR GS -8 8 rl 8 8 rl S GR} for -45 ROT "
		    "GS 0 24 MR (N) SHC GR GS 0 -24 MR (S) dup SWH neg 0 exch MR pop SHC GR GS -24 0 MR (W) SHRC GR GS 24 0 MR (E) SHLC GR "
		    "GR\n");
	    set_on_paper(".2 mm LW", e1, n1, buf);
	    break;
	default:
	    error(key, data, "northarrow: x, y and radius");
	}
    }
    else if (KEY("declination")) {
    }
    else if (KEY("compass") || KEY("rose")) {
	char h;
	int dg, mn;
	double conv, sec;

	if (sscanf(data, "%lf %lf %lf %lf", &east, &north, &d, &conv) != 4) {
	    error(key, data,
		  "compass: x, y, radius and magnetic declination");
	}
	d *= (MT_TO_POINT / (double)PS.scale);
	set_xy_where(".25 LW", east, north, "M ");
	/* exterior */
	fprintf(PS.fp, "GS 90 ROT %.2f ", d);
	fprintf(PS.fp, "0 90 270 {GS ROT dup 0 LR [1] 0 LD S GR} for ");
	fprintf(PS.fp,
		"0 -1 -359 {/i XD GS i ROT dup 0 MR i 10 mod 0 eq "
		"{-9 0 LR i neg i2s dup SW 2 div 10 exch MR 270 ROT show} "
		"{i 5 mod 0 eq {-6} {-3} ifelse 0 LR} ifelse S GR} for ");
	fprintf(PS.fp, "pop GR\n");
	format_northing(-conv, buf, PROJECTION_LL);
	/* interior */
	fprintf(PS.fp, "GS %.3f ROT FR %.2f ", conv + 90., .60 * d);
	fprintf(PS.fp, "0 90 270 {GS ROT dup 0 LR [] 0 LD S GR} for ");
	fprintf(PS.fp,
		"0 -1 -359 {/i XD GS i ROT dup 0 MR i 30 mod 0 eq "
		"{6 0 LR i neg i2s dup SW 2 div 1 exch MR 270 ROT show} "
		"{i 5 mod 0 eq {3} {1.5} ifelse 0 LR} ifelse S GR} for ");
	fprintf(PS.fp, "2 div 1 MR (%s) SHC GR\n", buf);
    }
    /* Oops ending */
    else {
	error(key, data, "not found\n");
    }

    return 0;
}


void label_in_file(char *name)
{
    FILE *in = NULL;
    char buf[1024], code[1024], data[1024];
    int x, y;
    double n;
    PSFRAME frame;
    PSFONT font;

    frame.xref = CENTER;
    frame.yref = CENTER;

    if (*name) {
	in = fopen(name, "r");
	if (in == NULL) {
	    G_message("Labels file <%s> can't open", name);
	    return;
	}
    }

    while (fgets(buf, sizeof(buf), in)) {
	*code = 0;
	*data = 0;
	if (sscanf(buf, "%[^:]:%[^\n]", code, data) < 1)
	    continue;

	G_strip(data);
	if (CODE("text")) {

	    G_plot_where_xy(frame.x, frame.y, &x, &y);
	    frame.x = ((double)x) / 10.;
	    frame.y = ((double)y) / 10.;
	    if (strcmp(font.name, "Standard") != 0)
		set_ps_font(&font);
	    fprintf(PS.fp, "GS\n");
	    fprintf(PS.fp, "/ARo [(%s)] def\n", data);
	    fprintf(PS.fp, "/ARw [ARo SWx] def ");
	    fprintf(PS.fp, "/ARh [FS0] def\n");
	    set_box_auto(&frame, &font, 0.25);
	    fprintf(PS.fp, "(%s) READJUST ", data);
	    set_box_draw(&frame);
	    fprintf(PS.fp, "GR\n");
	    fprintf(PS.fp, "(%s) xo wd 2 div add yo hg 2 div sub M SHCC\n",
		    data);
	}
	/* Option to modify the text */
	else if (CODE("east")) {
	    frame.x = atof(data);
	}
	else if (CODE("north")) {
	    frame.y = atof(data);
	}
	else if (CODE("xoffset")) {
	    frame.xset = atof(data);
	}
	else if (CODE("yoffset")) {
	    frame.yset = atof(data);
	}
	else if (CODE("ref")) {
	    scan_ref(data, &(frame.xref), &(frame.yref));
	}
	else if (CODE("font")) {
	    get_font(data);
	    strcpy(font.name, data);
	}
	else if (CODE("fontsize")) {
	    if (scan_dimen(data, &(font.size)) != 1)
		font.size = 10.;
	}
	else if (CODE("size")) {
	    n = atof(data);
	    font.size = (n * MT_TO_POINT) / PS.scale;
	}
	else if (CODE("color")) {
	    if (!scan_color(data, &(font.color))) {
		set_color_rgb(&(font.color), 0, 0, 0);
	    }
	}
	else if (CODE("space")) {
	}
	else if (CODE("rotation")) {
	    frame.rotate = atof(data);
	}
	else if (CODE("width")) {
	    if (scan_dimen(data, &(frame.border)) != 1) {
		frame.border = -1;
	    }
	}
	else if (CODE("hcolor")) {
	}
	else if (CODE("hwidth")) {
	}
	else if (CODE("background")) {
	    if (!scan_color(data, &(frame.fcolor))) {
		unset_color(&(frame.fcolor));
	    }
	}
	else if (CODE("border")) {
	    if (!scan_color(data, &(frame.color))) {
		unset_color(&(frame.color));
	    }
	}
	else if (CODE("opaque")) {
	}
    }
    fclose(in);

    return;
}


int set_on_paper(char *pre, char *c_x, char *c_y, char *post)
{
    char xunit, yunit;
    int xret, yret, x, y;
    double dx, dy;

    xret = sscanf(c_x, "%lf%c", &dx, &xunit);
    yret = sscanf(c_y, "%lf%c", &dy, &yunit);

    /* east | north */
    if (xret == 1 && yret == 1) {
	G_plot_where_xy(dx, dy, &x, &y);
	dx = ((double)x) / 10.;
	dy = ((double)y) / 10.;
    }
    /* x | y */
    else if (xret == 2 && yret == 2) {
	xret = scan_dimen(c_x, &dx);
	yret = scan_dimen(c_y, &dy);
	/* percent */
	if (xret == 2)
	    dx *= (PS.page.width / 100.);
	if (yret == 2)
	    dy *= (PS.page.height / 100.);
	if (xret < 0)
	    dx = (PS.page.width + dx);
	if (yret < 0)
	    dy = (PS.page.height + dy);
	/* margen inferior */
	dy = PS.page.height - dy;
    }
    fprintf(PS.fp, "%s %.1f %.1f %s", pre, dx, dy, post);
    return xret;
}
