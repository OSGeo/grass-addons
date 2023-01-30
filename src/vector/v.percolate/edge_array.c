/***********************************************************************/
/*
   edge_array.c

   Revised by Mark Lake, 20/02/2018, for r.percolate in GRASS 7.x
   Written by Mark Lake and Theo Brown

   NOTES

 */

/***********************************************************************/

#include "edge_array.h"

/***********************************************************************/
/* Private functions                                                    */

/***********************************************************************/

void shellSortEdgeArray(edge *, int);

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

edge *initialiseEdgeArray(long int numpoints)
{
    edge *edges;
    long int nEdges;

    nEdges =
        ((numpoints * numpoints) - numpoints) / 2; /* Half the
                                                      distance matrix,
                                                      omitting the diagonal */
    edges = (edge *)malloc(nEdges * sizeof(edge));
    if (!edges) {
        G_fatal_error(_("\n\nFATAL ERROR - failure to allocate memory for "
                        "edgeList in constructEdgeArray()\n\n"));
    }

    return (edges);
}

/***********************************************************************/

long int constructEdgeArray(edge *edges, float **DistanceMatrix,
                            long int numpoints)
{
    int i;
    int j;
    long int e = -1;

    for (i = 0; i < (numpoints - 1); i++) {
        for (j = i + 1; j < numpoints; j++) {
            e++;
            edges[e].id = e + 1;
            edges[e].from = i;
            edges[e].to = j;
            edges[e].dist = DistanceMatrix[i][j];
        }
    }

    /* if (nEdges != ( e + 1)) { */
    /* Because 1st edge has index (thus e) = zero */
    /*  G_fatal_error(_("\n\nFATAL ERROR: nEdges != e in
     * constructEdgeArray()\n\n")); */

    G_message(_("Constructed edge array with %ld edges"), e + 1);
    return e + 1;
}

/***********************************************************************/

void copyEdgeArrayItem(edge *from, edge *to)
{
    to->id = from->id;
    to->from = from->from;
    to->to = from->to;
    to->dist = from->dist;
}

/***********************************************************************/

void printEdgeArrayWithNodeIndices(edge *edges, long int nEdges)
{
    int e;

    for (e = 0; e < nEdges; e++) {
        fprintf(stderr, "\nEdge %4d  from %4d  to %4d  dist %6.1f", edges[e].id,
                edges[e].from, edges[e].to, edges[e].dist);
    }
    fprintf(stderr, "\n");
    fflush(stderr);
}

/***********************************************************************/

void printEdgeArrayWithNodeCats(edge *edges, long int nEdges, node *nodes)
{
    int e;

    for (e = 0; e < nEdges; e++) {
        fprintf(stderr, "\nEdge %4d  from %4d  to %4d  dist %6.1f", edges[e].id,
                nodes[edges[e].from].cat, nodes[edges[e].to].cat,
                edges[e].dist);
    }
    fprintf(stderr, "\n");
    fflush(stderr);
}

/***********************************************************************/

void printEdgeArrayWithNodeNames(edge *edges, long int nEdges, node *nodes)
{
    int e;

    for (e = 0; e < nEdges; e++) {
        fprintf(stderr, "\nEdge %4d  from %s  to %s  dist %6.1f", edges[e].id,
                nodes[edges[e].from].name, nodes[edges[e].to].name,
                edges[e].dist);
    }
    fprintf(stderr, "\n");
    fflush(stderr);
}

/***********************************************************************/

void sortEdgeArray(edge *edges)
{
    G_message(_("Sorting edge array by distance between points (please wait)"));
    shellSortEdgeArray(edges, nEdges);
    /*mergesort (edges, nEdges); */
}

/***********************************************************************/
/* Private functions                                                   */

/***********************************************************************/

/* void mergesort (edge* a, int n) { */
/*     int i; */
/*     for (i = 0; i < n; i++) */
/*         printf("%d%s", a[i], i == n - 1 ? "\n" : " "); */
/*     merge_sort(a, n); */
/*     for (i = 0; i < n; i++) */
/*         printf("%d%s", a[i], i == n - 1 ? "\n" : " "); */
/*     return (a); */
/* } */

/***********************************************************************/

void shellSortEdgeArray(edge *a, int N)
{
    /* Shellsort algorithm from Sedgewick, R. 1990. Algorithms in
       C. Addison-Wesley. p.109 */
    long int i, j, h;

    edge v;

    /* This is adjusted to sort array a[0] - a[N-1] */
    for (h = 1; h <= N / 9; h = 3 * h + 1)
        ;
    for (; h > 0; h /= 3) {
        for (i = h + 1; i <= N; i += 1) { /* less than N */
            /* fprintf (stderr, "\n h=%d, i=%d", h, i); */
            /* v = a[i-1].dist; */
            copyEdgeArrayItem(&a[i - 1], &v);
            j = i;
            while (j > h && a[j - h - 1].dist > v.dist) {
                /* a[j-1].dist = a[j-h-1].dist; */
                copyEdgeArrayItem(&a[j - h - 1], &a[j - 1]);
                j -= h;
            }
            /* a[j-1].dist = v; */
            copyEdgeArrayItem(&v, &a[j - 1]);
        }
    }
}
