#include <grass/gis.h>
#include <grass/raster.h>

void make_history(const char *name, const char *group, const char *matrixfile)
{
    struct History hist;

    if (Rast_read_history(name, G_mapset(), &hist) >= 0) {
        Rast_format_history(&hist, HIST_DATSRC_1, "Group: %s", group);
        Rast_format_history(&hist, HIST_DATSRC_2, "Matrix file: %s",
                            matrixfile);
        Rast_write_history(name, &hist);
    }
}
