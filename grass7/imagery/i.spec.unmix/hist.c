#include <stdio.h>
#include <grass/gis.h>
#include <grass/raster.h>


void make_history (char *name, char *group, char *matrixfile)
{
    struct History hist;

    if (Rast_read_history (name, G_mapset(), &hist) >= 0)
    {
	sprintf (hist.fields[1], "Group: %s", group);
	sprintf (hist.fields[2], "Matrix file: %s", matrixfile);
	Rast_write_history (name, &hist);
    }
}
