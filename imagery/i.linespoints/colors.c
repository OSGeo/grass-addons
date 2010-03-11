#include "gis.h"
#include "display.h"
#include "D.h"
int 
set_colors (struct Colors *colors)
{
    D_set_colors (colors);

    return 0;
}
