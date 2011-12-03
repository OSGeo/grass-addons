
#include <string.h>
#include "colors.h"
#include "conversion.h"
#include "ps_info.h"
#include "local_proto.h"


/* scan dimensions on the map */
int scan_easting(char *buf, double *f)
{
    if (scan_percent(buf, f, PS.map.west, PS.map.east))
	return 1;
    return G_scan_easting(buf, f, PS.map.proj);
}

int scan_northing(char *buf, double *f)
{
    if (scan_percent(buf, f, PS.map.south, PS.map.north))
	return 1;
    return G_scan_northing(buf, f, PS.map.proj);
}

int scan_percent(char *buf, double *f, double min, double max)
{
    char percent[3];

    *percent = 0;
    if (sscanf(buf, "%lf%2s", f, percent) != 2)
	return 0;
    if (strcmp(percent, "%") != 0)
	return 0;
    *f = min + (max - min) * (*f / 100.0);
    return 1;
}

/* scan references */
int scan_ref(char *buf, int *xref, int *yref)
{
    char refx[10], refy[10];

    *xref = *yref = CENTER;
    if (sscanf(buf, "%9s %9s", refx, refy) != 2)
	return 0;

    if (strcmp(refx, "LEFT") == 0 || strcmp(refx, "left") == 0)
	*xref = LEFT;
    else if (strcmp(refx, "CENTER") == 0 || strcmp(refx, "center") == 0)
	*xref = CENTER;
    else if (strcmp(refx, "RIGHT") == 0 || strcmp(refx, "right") == 0)
	*xref = RIGHT;

    if (strcmp(refy, "UPPER") == 0 || strcmp(refy, "upper") == 0)
	*yref = UPPER;
    else if (strcmp(refy, "CENTER") == 0 || strcmp(refy, "center") == 0)
	*yref = CENTER;
    else if (strcmp(refy, "LOWER") == 0 || strcmp(refy, "lower") == 0)
	*yref = LOWER;

    return 1;
}

/* */
int scan_yesno(char *key, char *data)
{
    char buf;

    if (sscanf(data, "%c", &buf) != 1)
	return 1;
    if (buf == 'y' || buf == 'Y' || buf == 't' || buf == 'T')
	return 1;
    if (buf == 'n' || buf == 'N' || buf == 'f' || buf == 'F')
	return 0;

    error(key, data, "illegal yes/no option");
    return 0;
}

int scan_color(char *data, PSCOLOR * color)
{
    int ret;
    char name[20];
    double alpha;

    ret = sscanf(data, "%[^$]$%lf", name, &alpha);

    if (set_color_name(color, name)) {
	color->a = (ret == 2) ? alpha : 1.;
	return 1;
    }
    return 0;
}



int scan_dimen(char *data, double *d)
{
    int ret;
    char unit = ' ';

    ret = sscanf(data, "%lf%c", d, &unit);

    if (ret == 1)
	unit = ' ';
    else if (ret != 2) {
	*d = 0.;
	return 0;
    }

    switch (unit) {
	/* metric to points */
    case 'i':
	*d *= INCH_TO_POINT;
	break;
    case 'm':
	*d *= MM_TO_POINT;
	break;
    case 'c':
	*d *= CM_TO_POINT;
	break;
	/* special : percent */
    case '%':
	return 2;
    }

    return (*d < 0 ? -1 : 1);
}


int scan_second(char *data, double *d)
{
    int ret;
    char unit = ' ';

    ret = sscanf(data, "%lf%c", d, &unit);

    if (ret == 1)
	unit = ' ';
    else if (ret != 2 || *d < 0.) {
	*d = 0.;
	return 0;
    }

    if (unit == '\'' || unit == 'm')
	*d *= 60.;
    else if (unit == 'º' || unit == 'd')
	*d *= 3600.;

    return 1;
}
