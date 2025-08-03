#include "local_proto.h"

int is_less(Position p1, Position p2, Position ref)
{
    int dx1 = p1.x - ref.x;
    int dy1 = p1.y - ref.y;
    int dx2 = p2.x - ref.x;
    int dy2 = p2.y - ref.y;

    int cross = dx1 * dy2 - dx2 * dy1;

    return cross > 0 ||
           (cross == 0 && (abs(dx1) + abs(dy1)) > (abs(dx2) + abs(dy2)));
}

int concave(Position p1, Position p2, Position p3)
{
    int dx1 = p2.x - p1.x;
    int dx2 = p3.x - p1.x;
    int dy1 = p2.y - p1.y;
    int dy2 = p3.y - p1.y;
    int cross = dx1 * dy2 - dx2 * dy1;

    return cross < 0;
}

/* quicksort */
void sort_vertices(Position *list, int begin, int end, Position ref)
{
    int b = begin + 1;
    int e = end;
    Position piv;
    Position tmp;

    if (begin >= end)
        return;

    piv = list[begin];

    /*
    G_message("begin=(%d,%d), end=(%d,%d), piv=(%d,%d), ref=(%d,%d)", list[b].x,
    list[b].y, list[e].x, list[e].y, piv.x, piv.y, ref.x, ref.y);
    */

    while (b <= e) {
        /*
        G_message("begin=%d, end=%d, piv=(%d,%d), ref=(%d,%d)", b, e, piv.x,
        piv.y, ref.x, ref.y);

        G_message("is_less(%d, %d) = %d", list[b].x, list[b].y, is_less(list[b],
        piv, ref));
        */
        while (is_less(list[b], piv, ref)) {
            b++;
        }
        /*
        G_message("is_bigger(%d, %d) = %d", list[e].x, list[e].y, is_less(piv,
        list[e], ref));
        */
        while (is_less(piv, list[e], ref)) {
            e--;
        }
        if (b <= e) {
            /* G_message("swap %d with %d", b, e); */

            tmp = list[b];

            list[b] = list[e];
            list[e] = tmp;
        }
    }

    /* put piveau element to its place */
    /* G_message("swap %d with %d", begin, e); */
    tmp = list[begin];

    list[begin] = list[e];
    list[e] = tmp;

    if (begin < e)
        sort_vertices(list, begin, e - 1, ref);
    if (b < end)
        sort_vertices(list, b, end, ref);
}

void convex_hull_cluster(int *map, int cluster, int nrows, int ncols)
{
    int i;
    int *p;
    int area = 0;
    Position *vertices;
    Position tmp;
    Position centroid = {0, 0};
    int vertexcount = 0;

    /* calculate sum of the patch areas */
    for (p = clusters[cluster]; p < clusters[cluster + 1]; p++) {
        area += fragments[*p + 1] - fragments[*p];
    }

    /* G_message("Cluster%d area = %d", cluster, area); */

    /* allocate memory for the vertex list */
    vertices = (Position *)G_malloc((area + 1) * sizeof(Position));

    /* fill vertex list */

    /* for each patch in the cluster */
    for (p = clusters[cluster]; p < clusters[cluster + 1]; p++) {
        /* G_message("Analyzing Patch%d", *p); */

        Coords *c;

        /* for each cell in the patch */
        for (c = fragments[*p]; c < fragments[*p + 1]; c++) {
            /* write border cells to the list */
            if (c->neighbors < 4) {
                vertices[vertexcount].x = c->x;
                vertices[vertexcount].y = c->y;
                vertexcount++;
            }
        }
    }

    /* skip hull building for 1-cell-patches */
    if (vertexcount > 1) {
        /* find the top-left cell */
        int min = 0;
        int k;

        for (i = 0; i < vertexcount; i++) {
            if (vertices[i].y < vertices[min].y ||
                (vertices[i].y == vertices[min].y &&
                 vertices[i].x < vertices[min].x)) {
                min = i;
            }
        }

        /* put min at the first position */
        tmp = vertices[0];

        vertices[0] = vertices[min];
        vertices[min] = tmp;

        /*G_message("Vertex list:");
           for(i = 0; i < vertexcount; i++) {
           fprintf(stderr, " (%d,%d)", vertices[i].x, vertices[i].y);
           }
           fprintf(stderr, "\n"); */

        /* sort cells by the polar angle with the top-left cell */
        sort_vertices(vertices, 1, vertexcount - 1, vertices[0]);

        /* copy min to the last position */
        /* vertices[vertexcount] = vertices[0]; */
        /* vertexcount++; */

        /*G_message("Vertex list:");
           for(i = 0; i < vertexcount; i++) {
           fprintf(stderr, " (%d,%d)", vertices[i].x, vertices[i].y);
           }
           fprintf(stderr, "\n"); */

        /* process points and bridge concave angles */
        /* first h cells of the result are the hull cells */
        i = 2;

        for (k = 2; k < vertexcount; k++, i++) {
            /* swap cells i and k */
            tmp = vertices[i];
            vertices[i] = vertices[k];
            vertices[k] = tmp;

            /* while next angle is concave */
            while (concave(vertices[i - 2], vertices[i - 1], vertices[i])) {
                /* swap cells i-1 and i */
                tmp = vertices[i - 1];
                vertices[i - 1] = vertices[i];
                vertices[i] = tmp;

                /* bridge concave angle */
                i--;
            }
        }

        vertexcount = i;
    }

    /*G_message("Vertex list:");
       for(i = 0; i < vertexcount; i++) {
       fprintf(stderr, " (%d,%d)", vertices[i].x, vertices[i].y);
       }
       fprintf(stderr, "\n"); */

    for (i = 0; i < vertexcount; i++) {
        Position p1 = vertices[i];
        Position p2 = vertices[(i + 1) % vertexcount];

        /* calculate centroid */
        centroid.x += p1.x;
        centroid.y += p1.y;

        /* draw borders */
        draw_line(map, 1, p1.x, p1.y, p2.x, p2.y, ncols, nrows, 1);
    }

    /* finish calculating centroid and fill the hull */
    centroid.x = (int)((double)centroid.x / (double)vertexcount);
    centroid.y = (int)((double)centroid.y / (double)vertexcount);

    G_message("Centroid is at (%d, %d)", centroid.x, centroid.y);
    flood_fill(map, 1, centroid.x, centroid.y, ncols, nrows);
    G_message("finished");

    /* free memory */
    G_free(vertices);
}

void convex_hull(int *map, int nrows, int ncols)
{
    int cluster;

    for (cluster = 0; cluster < clustercount; cluster++) {
        convex_hull_cluster(map, cluster, nrows, ncols);
    }
}
