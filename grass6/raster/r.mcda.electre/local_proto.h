#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/config.h>


struct input
{
    char *name, *mapset;	/* input raster name  and mapset name */
    int infd;
    void *inrast;		/* input buffer */
};
