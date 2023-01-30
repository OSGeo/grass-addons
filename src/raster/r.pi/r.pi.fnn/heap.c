#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include "local_proto.h"

static void exchange(int p1, int p2)
{
    Path_Coords tmp = heap[p1];

    heap[p1] = heap[p2];
    heap[p2] = tmp;
}

void upheap(int pos)
{
    int i = pos;

    while (i > 0 && heap[i].f < heap[(i - 1) / 2].f) {
        exchange(i, (i - 1) / 2);
        i = (i - 1) / 2;
    }
}

void downheap(int pos)
{
    int son = pos * 2 + 1;

    /* actual element has left son */
    if (son < heapsize) {
        /* actual element has right son, which is the smaller son */
        if (son + 1 < heapsize && heap[son + 1].f < heap[son].f)
            son++;
        /* son is now the smaller son */
        /* if son smaller then actual element */
        if (heap[pos].f > heap[son].f) {
            exchange(pos, son);
            downheap(son);
        }
    }
}

void heap_alloc(int size)
{
    heap = (Path_Coords *)G_malloc(size * sizeof(Path_Coords));
}

void heap_free()
{
    G_free(heap);
}

Path_Coords heap_delete(int pos)
{
    Path_Coords res = heap[pos];

    heap[pos] = heap[--heapsize];
    if (pos > 0 && heap[pos].f < heap[(pos - 1) / 2].f)
        upheap(pos);
    else
        downheap(pos);
    return res;
}

void heap_insert(int x, int y, DCELL f, DCELL g)
{
    Path_Coords *pc = heap + heapsize;

    /* heapsize++; look down */
    pc->x = x;
    pc->y = y;
    pc->f = f;
    pc->g = g;
    upheap(heapsize++);
}

int heap_search(int x, int y)
{
    int i;

    for (i = 0; i < heapsize; i++) {
        Path_Coords *act = heap + i;

        if (act->x == x && act->y == y)
            return i;
    }
    return -1;
}
