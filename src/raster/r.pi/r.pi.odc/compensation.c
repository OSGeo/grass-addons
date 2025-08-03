#include "local_proto.h"

DCELL none(DCELL value, int frag)
{
    return value;
}

DCELL odd_area(DCELL value, int frag)
{
    DCELL area = fragments[frag + 1] - fragments[frag];

    return value / area;
}

DCELL area_odd(DCELL value, int frag)
{
    DCELL area = fragments[frag + 1] - fragments[frag];

    return area / value;
}

DCELL odd_perim(DCELL value, int frag)
{
    DCELL perim = 0;
    Coords *fragment;

    for (fragment = fragments[frag]; fragment < fragments[frag + 1];
         fragment++) {
        if (fragment->neighbors < 4) {
            perim++;
        }
    }

    return value / perim;
}

DCELL perim_odd(DCELL value, int frag)
{
    DCELL perim = 0;
    Coords *fragment;

    for (fragment = fragments[frag]; fragment < fragments[frag + 1];
         fragment++) {
        if (fragment->neighbors < 4) {
            perim++;
        }
    }

    return perim / value;
}
