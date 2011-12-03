/* File: set_ps.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */
#include <string.h>
#include <grass/symbol.h>
#include "vareas.h"
#include "vpoints.h"
#include "ps_info.h"
#include "local_proto.h"


void set_ps_rect(double x, double y, double w, double h)
{
    fprintf(PS.fp, "%.3f %.3f %.3f %.3f RO\n", x, y, w, h);
    return;
}

void set_ps_brd(double margin)
{
    fprintf(PS.fp, "%.3f %.3f %.3f %.3f RO\n",
	    PS.map_x - margin, PS.map_y - margin, PS.map_w + 2. * margin,
	    PS.map_h + 2. * margin);
    return;
}

void set_ps_brd2(double lwidth, double margin)
{
    fprintf(PS.fp, "%.3f LW %.3f %.3f %.3f %.3f RO\n",
	    lwidth, PS.map_x - margin, PS.map_y - margin,
	    PS.map_w + 2. * margin, PS.map_h + 2. * margin);
    return;
}

/* GEOGRAPHIC */
/* geographic coordinates to paper coordinates */
int set_ps_where(char action, double east, double north)
{
    int x, y;
    double dx, dy;

    G_plot_where_xy(east, north, &x, &y);

    dx = ((double)x) / 10.;
    dy = ((double)y) / 10.;

    fprintf(PS.fp, "%.1f %.1f %c ", dx, dy, action);
    return 0;
}


/* GEOGRAPHIC */
/* geographic coordinates to paper coordinates */
int set_xy_where(char *pre, double east, double north, char *post)
{
    int x, y;
    double dx, dy;

    G_plot_where_xy(east, north, &x, &y);

    dx = ((double)x) / 10.;
    dy = ((double)y) / 10.;

    fprintf(PS.fp, "%s %.1f %.1f %s", pre, dx, dy, post);
    return 0;
}

int is_xy_outside(double east, double north)
{
    int x, y;
    double dx, dy;

    G_plot_where_xy(east, north, &x, &y);

    dx = ((double)x) / 10.;
    dy = ((double)y) / 10.;

    if (dx < PS.map_x || dx > PS.map_right || dy < PS.map_y ||
	dy > PS.map_top)
	return 1;

    return 0;
}


/* PATTERNS */
/* store a pattern for posterior reference by number */
int set_ps_pattern(int code, char *eps, VAREAS * va)
{
    FILE *fp;
    char buf[1024];
    int ret = 0;
    double llx, lly, urx, ury;

    if ((fp = fopen(eps, "r")) == NULL) {
	G_message("File <%s> not found!\n", eps);
	return 0;
    }

    /* find the bounding box in EPS */
    llx = lly = urx = ury = 0.;
    while (fgets(buf, 128, fp) != NULL && ret != 4) {
	ret =
	    sscanf(buf, "%%%%BoundingBox: %lf %lf %lf %lf", &llx, &lly, &urx,
		   &ury);
    }
    if (llx == 0. && lly == 0. && urx == 0. && ury == 0.) {
	fclose(fp);
	error(eps, "", "ERROR: Bounding box in <%s> was not found");
    }

    llx *= va->sc_pat;
    lly *= va->sc_pat;
    urx *= va->sc_pat;
    ury *= va->sc_pat;

    fprintf(PS.fp, "/PATTERN%d\n", code);
    fprintf(PS.fp, "<< /PatternType 1\n   /PaintType %d\n   /TilingType 1\n",
	    va->type_pat);
    fprintf(PS.fp, "   /BBox [%.4f %.3f %.4f %.4f]\n", llx, lly, urx, ury);
    fprintf(PS.fp, "   /XStep %.4f\n   /YStep %.4f\n", (urx - llx),
	    (ury - lly));
    fprintf(PS.fp, "   /PaintProc\n");
    fprintf(PS.fp, "   { begin\n");
    fprintf(PS.fp, "     %.4f dup scale\n", va->sc_pat);
    if (va->type_pat == 1) {
	fprintf(PS.fp, "     ");
	set_ps_color(&(va->fcolor));
	fprintf(PS.fp, "\n");
    }
    fprintf(PS.fp, "     [] 0 LD %.4f LW\n", va->lw_pat);
    while (fgets(buf, 1024, fp) != NULL)
	fprintf(PS.fp, "     %s", buf);
    fprintf(PS.fp, "     end }\n");
    fprintf(PS.fp, ">> matrix makepattern def\n");

    fclose(fp);
    return 1;
}

/* SYMBOLS */

/* store a eps symbol */
int set_ps_symbol_eps(int code, char *eps)
{
    FILE *fp;
    char buf[1024];

    if ((fp = fopen(eps, "r")) == NULL) {
	G_message("File <%s> not found!\n", eps);
	return 0;
    }

    fprintf(PS.fp, "/SYMBOL%d {\n", code);
    while (fgets(buf, 1024, fp) != NULL) {
	if (strncmp(buf, "%!PS-Adobe", 10) == 0 ||
	    strncmp(buf, "%%BoundingBox", 13) == 0)
	    continue;
	fprintf(PS.fp, "     %s", buf);
    }
    fprintf(PS.fp, "\n} def\n");

    fclose(fp);
    return 1;
}
