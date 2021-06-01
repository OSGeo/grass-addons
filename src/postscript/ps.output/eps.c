/* File: eps.c
 *
 *  COPYRIGHT: (c) GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <math.h>
#include <string.h>
#include "ps_info.h"
#include "local_proto.h"

/*  test if file is realy EPS file and find bbox
 *  returns  1 if OK
 *           0 on error
 */
int eps_bbox(char *eps, double *llx, double *lly, double *urx, double *ury)
{
    char buf[201];
    FILE *fp;
    int v1, v2, v3, v4;

    /* test if file is realy eps and find bbox */
    if ((fp = fopen(eps, "r")) == NULL) {
	fprintf(stderr, "can't open eps file <%s>\n", eps);
	return (0);
    }
    /* test if first row contains '%!PS-Adobe-m.n EPSF-m.n' string */
    fgets(buf, 200, fp);
    if (sscanf(buf, "%%!PS-Adobe-%d.%d EPSF-%d.%d", &v1, &v2, &v3, &v4) < 4) {
	fprintf(stderr, "file <%s> is not in EPS format\n", eps);
	fclose(fp);
	return (0);
    }
    /* looking for bbox */
    while (fgets(buf, 200, fp) != NULL) {
	if (sscanf
	    (buf, "%%%%BoundingBox: %lf %lf %lf %lf", llx, lly, urx,
	     ury) == 4) {
	    fclose(fp);
	    return (1);
	}
    }
    fprintf(stderr, "Bounding box in eps file <%s> was not found\n", eps);
    fclose(fp);
    return (0);
}

/* calculate translation for EPS file
 * rotate is in degrees
 */
int eps_trans(double llx, double lly, double urx, double ury,
	      double x, double y, double scale, double rotate, double *xt,
	      double *yt)
{
    double xc, yc, angle;

    xc = (llx + urx) / 2;
    yc = (lly + ury) / 2;

    angle = M_PI * rotate / 180;
    *xt = x + scale * (yc * sin(angle) - xc * cos(angle));
    *yt = y - scale * (yc * cos(angle) + xc * sin(angle));

    return (1);
}

/* save EPS file into PS file for later use */
int eps_save(FILE * fp, char *epsf, char *name)
{
    char buf[1024];
    FILE *epsfp;

    if ((epsfp = fopen(epsf, "r")) == NULL)
	return (0);

    fprintf(fp, "\n/%s {\n", name);
    while (fgets(buf, 1024, epsfp) != NULL)
	fprintf(fp, "%s", buf);
    fprintf(fp, "} def\n");
    fclose(epsfp);

    return (1);
}

/* draw EPS file saved by eps_save */
int eps_draw_saved(FILE * fp, char *name, double x, double y, double scale,
		   double rotate)
{
    fprintf(PS.fp, "\nBeginEPSF\n");
    fprintf(PS.fp, "%.5f %.5f translate\n", x, y);
    fprintf(PS.fp, "%.5f rotate\n", rotate);
    fprintf(PS.fp, "%.5f %.5f scale\n", scale, scale);
    fprintf(PS.fp, "%%BeginDocument: %s\n", name);

    fprintf(PS.fp, "%s\n", name);

    fprintf(PS.fp, "%%EndDocument\n");
    fprintf(PS.fp, "EndEPSF\n");

    return (1);
}


/* write EPS file into PS file */
int eps_draw(FILE * fp, char *eps, double x, double y, double scale,
	     double rotate)
{
    char buf[1024];
    FILE *epsfp;

    if ((epsfp = fopen(eps, "r")) == NULL)
	return (0);

    fprintf(PS.fp, "\nBeginEPSF\n");
    fprintf(PS.fp, "%.5f %.5f translate\n", x, y);
    fprintf(PS.fp, "%.5f rotate\n", rotate);
    fprintf(PS.fp, "%.5f %.5f scale\n", scale, scale);
    fprintf(PS.fp, "%%BeginDocument: %s\n", eps);

    while (fgets(buf, 1024, epsfp) != NULL)
	fprintf(fp, "%s", buf);

    fprintf(PS.fp, "%%EndDocument\n");
    fprintf(PS.fp, "EndEPSF\n");
    fclose(epsfp);

    return (1);
}

/* save EPS patter file into PS file for later use */
/* For pattern we have to remove header comments */
int pat_save(FILE * fp, char *epsf, char *name)
{
    char buf[1024];
    FILE *epsfp;

    if ((epsfp = fopen(epsf, "r")) == NULL)
	return (0);

    fprintf(fp, "\n/%s {\n", name);
    while (fgets(buf, 1024, epsfp) != NULL) {
	if (strncmp(buf, "%!PS-Adobe", 10) == 0 ||
	    strncmp(buf, "%%BoundingBox", 13) == 0)
	    continue;
	fprintf(fp, "%s", buf);
    }
    fprintf(fp, "} def\n");
    fclose(epsfp);

    return (1);
}
