#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <time.h>
#include <grass/gis.h>
#include <grass/glocale.h>


struct input
{
    char *name, *mapset;
    int fd;
    CELL *buf;
};
