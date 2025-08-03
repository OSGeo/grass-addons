#include "globals.h"
#include "local_proto.h"

int Compute_equation(void)
{
    group.equation_stat =
        CRS_compute_georef_equations(&group.points, group.E12, group.N12,
                                     group.E21, group.N21, transform_order);

    return 0;
}
