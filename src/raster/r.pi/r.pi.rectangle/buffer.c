#include "local_proto.h"

void set_buffer(CELL *buffer, int x, int y, int width, int height, int sx,
                int sy, int align)
{
    int l, r, t, b;

    int i, j;

    int dx, dy;

    switch (align) {
    case 0: /* center */
        dx = width / 2;
        dy = height / 2;
        l = x - dx;
        r = x + dx;
        t = y - dy;
        b = y + dy;
        break;
    case 1: /* top-left */
        l = x;
        r = x + width - 1;
        t = y;
        b = y + height - 1;
        break;
    case 2: /* top-right */
        l = x - width + 1;
        r = x;
        t = y;
        b = y + height - 1;
        break;
    case 3: /* bottom-left */
        l = x;
        r = x + width - 1;
        t = y - height + 1;
        b = y;
        break;
    case 4: /* bottom-right */
        l = x - width + 1;
        r = x;
        t = y - height + 1;
        b = y;
        break;
    default:
        l = t = 0;
        r = b = 1;
        break;
    }

    l = l < 0 ? 0 : l;
    r = r >= sx ? sx - 1 : r;
    t = t < 0 ? 0 : t;
    b = b >= sy ? sy - 1 : b;

    /* fill buffer */
    for (j = t; j <= b; j++) {
        for (i = l; i <= r; i++) {
            buffer[j * sx + i] = 1;
        }
    }
}
