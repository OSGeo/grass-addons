/* File: format.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado, and the GRASS Development Team
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdio.h>
#include <string.h>
#include <grass/gis.h>
#include "ps_info.h"
#include "local_proto.h"

void format_northing(double north, char *buf, int map_proj)
{
    char h;
    int d, m;
    double s;

    if (map_proj == PROJECTION_LL) {
	G_lon_parts(north, &d, &m, &s, &h);
	if (s < 0.1)
	    s = 0.0;
	if (s > 59.9) {
	    s = 0.0;
	    ++m;
	}

	if (s != 0.0)
	    sprintf(buf, "%dº%d'%.1f\"%c", d, m, s, h);
	else {
	    if (m != 0)
		sprintf(buf, "%dº%d'%c", d, m, h);
	    else
		sprintf(buf, "%dº%c", d, h);
	}
    }
    else {
	sprintf(buf, "%0.8f", north);
	G_trim_decimal(buf);
    }
}

void format_easting(double east, char *buf, int map_proj)
{
    char h;
    int d, m;
    double s;

    if (map_proj == PROJECTION_LL) {
	G_lat_parts(east, &d, &m, &s, &h);
	if (s < 0.1)
	    s = 0.0;
	if (s > 59.9) {
	    s = 0.0;
	    ++m;
	}

	if (s != 0.0)
	    sprintf(buf, "%dº%d'%.1f\"%c", d, m, s, h);
	else {
	    if (m != 0)
		sprintf(buf, "%dº%d'%c", d, m, h);
	    else
		sprintf(buf, "%dº%c", d, h);
	}
    }
    else {
	sprintf(buf, "%0.8f", east);
	G_trim_decimal(buf);
    }
}


void format_iho(double value, char *buf)
{
    char h;
    int d, m;
    double s;

    if (PS.map.proj == PROJECTION_LL) {
	G_lon_parts(value, &d, &m, &s, &h);
	if (s < 0.1)
	    s = 0.0;
	if (s > 59.9) {
	    s = 0.0;
	    ++m;
	}

	if (s != 0.0)
	    //             sprintf(buf, "%dº|%d'%.8f\"", d, m, s);
	    sprintf(buf, "%dº|%.1f'", d, (double)m + s / 60.);
	else {
	    if (m != 0)
		sprintf(buf, "%dº|%d'", d, m);
	    else
		sprintf(buf, "%dº|", d);
	}
    }
    else {
	sprintf(buf, "%d|%03d", (int)(value / 1000), (int)value % 1000);
    }
}
