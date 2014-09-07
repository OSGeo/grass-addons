#include "gis.h"
#include <grass/display>
#include <grass/D.h>
int 
set_colors (struct Colors *colors)
{
    D_set_colors (colors);

    return 0;
}
