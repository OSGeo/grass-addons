#include "local_proto.h"

inline void swap(int *a, int *b)
{
    int zw = *a;

    *a = *b;
    *b = zw;
}

void draw_point(int *map, int val, int x, int y, int sx, int sy, int width)
{
    if (width <= 0) {
	return;
    }

    if (width == 1) {
	map[y * sx + x] = val;
    }
    else {
    }
}

void draw_line(int *map, int val, int x1, int y1, int x2, int y2, int sx,
	       int sy, int width)
{
    int steep = abs(y2 - y1) > abs(x2 - x1);

    if (steep) {
	swap(&x1, &y1);
	swap(&x2, &y2);
    }

    if (x1 > x2) {
	swap(&x1, &x2);
	swap(&y1, &y2);
    }

    int deltax = x2 - x1;
    int deltay = abs(y2 - y1);
    int error = deltax / 2;
    int ystep = y1 < y2 ? 1 : -1;
    int x;
    int y = y1;

    for (x = x1; x <= x2; x++) {
	if (steep) {
	    draw_point(map, val, y, x, sx, sy, width);
	}
	else {
	    draw_point(map, val, x, y, sx, sy, width);
	}

	error -= deltay;
	if (error < 0) {
	    y += ystep;
	    error += deltax;
	}
    }
}

void flood_fill(int *map, int val, int x, int y, int sx, int sy)
{
    /* exit if the position is already set to this value */
    if (map[y * sx + x] == val) {
	return;
    }

    /* setup list of positions to fill */
    Position *list = (Position *) G_malloc(sx * sy * sizeof(Position));
    Position *begin = list;
    Position *end = list + 1;

    /* set first position */
    begin->x = x;
    begin->y = y;
    map[y * sx + x] = val;

    /* while there are still positions to fill do */
    while (begin < end) {
	if (end - list >= sx * sy) {
	    G_message("fill list count: %d", end - list);
	    break;
	}

	int cur_x = begin->x;
	int cur_y = begin->y;

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
