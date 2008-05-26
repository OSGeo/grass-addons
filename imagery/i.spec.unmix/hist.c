#include <grass/gis.h>

void make_history(name, group, matrixfile)
    char *name, *group, *matrixfile;
{
    struct History hist;

    if(G_read_history (name, G_mapset(), &hist) >= 0)
    {
	sprintf (hist.datsrc_1, "Group: %s", group);
	sprintf (hist.datsrc_2, "Matrix file: %s", matrixfile);
	G_write_history (name, &hist);
    }
}
