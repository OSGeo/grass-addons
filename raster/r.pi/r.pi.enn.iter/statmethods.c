#include "local_proto.h"

DCELL sum(DCELL * vals, int count)
{
    if (count <= 0)
	return 0;

    int i;
    DCELL res = 0;

    for (i = 0; i < count; i++)
	res += vals[i];

    return res;
}

DCELL average(DCELL * vals, int count)
{
    if (count <= 0)
	return 0;

    int i;
    DCELL res = 0;

    for (i = 0; i < count; i++)
	res += vals[i];

    return res / count;
}
