#include "local_proto.h"

Point_List *list_array;

void list_init(int count, int rows, int cols)
{
    int i;

    /* allocate memory */
    list_array = (Point_List *)G_malloc(count * sizeof(Point_List));

    for (i = 0; i < count; i++) {
        /* allocate point lists */
        list_array[i].list = (Point *)G_malloc(rows * cols * sizeof(Point));
        list_array[i].count = 0;
    }
}

int list_count(int patch)
{
    return list_array[patch].count;
}

Point *list_patch(int patch)
{
    return list_array[patch].list;
}

void list_add(int patch, int x, int y)
{
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;

    list[cnt].x = x;
    list[cnt].y = y;
    list_array[patch].count++;
}

Point list_get(int patch, int pos)
{
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;
    Point res;

    memset(&res, 0, sizeof(Point));

    if (pos >= 0 && pos < cnt) {
        res.x = list[pos].x;
        res.y = list[pos].y;
    }

    return res;
}

void list_set(int patch, int pos, int x, int y)
{
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;

    if (pos >= 0 && pos < cnt) {
        list[pos].x = x;
        list[pos].y = y;
    }
}

void list_insert(int patch, int pos, int x, int y)
{
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;

    if (pos >= 0 && pos < cnt) {
        memmove(list + pos + 1, list + pos, (cnt - pos) * sizeof(Point));
        list[pos].x = x;
        list[pos].y = y;
        list_array[patch].count++;
    }
    else {
        list_add(patch, x, y);
    }
}

void list_remove(int patch, int pos)
{
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;

    if (pos >= 0 && pos < cnt) {
        list_array[patch].count--;
        cnt--;
        memmove(list + pos, list + pos + 1, (cnt - pos) * sizeof(Point));
    }
}

int list_indexOf(int patch, int x, int y)
{
    int i;
    int cnt = list_array[patch].count;
    Point *list = list_array[patch].list;

    for (i = 0; i < cnt; i++) {
        if (list[i].x == x && list[i].y == y)
            return i;
    }

    return -1;
}
