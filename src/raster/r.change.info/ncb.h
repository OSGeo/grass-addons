#include <grass/raster.h>

struct input {
    int fd;
    const char *name;
    CELL **buf; /* for reading raster map */
};

struct ncb /* neighborhood control block */
{
    int nsize; /* radius * 2 + 1 */
#if 0
    double dist;                /* radius of the neighborhood */
#endif
    int n; /* number of unmasked cells */
    char **mask;
    struct Categories cats;
    int nin; /* number of input maps */
    struct input *in;
};

extern struct ncb ncb;
