#include "local_proto.h"

void flood_fill(int *map, int val, int x, int y, int sx, int sy)
{
    /* setup list of positions to fill */
    Position *list;
    Position *begin;
    Position *end;

    /* exit if the position is already set to this value */
    if (map[y * sx + x] == val) {
        return;
    }

    list = (Position *)G_malloc(sx * sy * sizeof(Position));
    begin = list;
    end = list + 1;

    /* set first position */
    begin->x = x;
    begin->y = y;
    map[y * sx + x] = val;

    /* while there are still positions to fill do */
    while (begin < end) {
        int cur_x = begin->x;
        int cur_y = begin->y;

        if (end - list >= sx * sy) {
            G_debug(1, "fill list count: %d", (int)(end - list));
            break;
        }

        /* set all four neighbors on the list */
        if (cur_x > 0 && map[cur_y * sx + cur_x - 1] != val) {
            map[cur_y * sx + cur_x - 1] = val;
            end->x = cur_x - 1;
            end->y = cur_y;
            end++;
        }
        if (cur_x < sx - 1 && map[cur_y * sx + cur_x + 1] != val) {
            map[cur_y * sx + cur_x + 1] = val;
            end->x = cur_x + 1;
            end->y = cur_y;
            end++;
        }
        if (cur_y > 0 && map[(cur_y - 1) * sx + cur_x] != val) {
            map[(cur_y - 1) * sx + cur_x] = val;
            end->x = cur_x;
            end->y = cur_y - 1;
            end++;
        }
        if (cur_y < sy - 1 && map[(cur_y + 1) * sx + cur_x] != val) {
            map[(cur_y + 1) * sx + cur_x] = val;
            end->x = cur_x;
            end->y = cur_y + 1;
            end++;
        }

        /* move to the next one */
        begin++;
    }

    G_free(list);
}
