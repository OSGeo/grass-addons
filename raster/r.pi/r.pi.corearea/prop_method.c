#include "local_proto.h"

DCELL linear(DCELL value, DCELL propcost)
{
    value -= propcost;
    return value >= 0.0 ? value : 0.0;
}

DCELL exponential(DCELL value, DCELL propcost)
{
    if (propcost == 0.0) {
	return MAX_DOUBLE;
    }
    else {
	return value / propcost;
    }
}
