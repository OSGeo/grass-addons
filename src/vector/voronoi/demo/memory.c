#include "data_types.h"
#include <stdlib.h>

struct vertex *sites;
static struct edge *edges;
static struct edge **free_list_e;

static unsigned int n_free_e;

void alloc_memory(unsigned int n){
    struct edge *e;
    int i;

    /* Point storage. */
    sites = (struct vertex *) calloc(n, sizeof(struct vertex));
    if (sites == NULL) 
        problem("Not enough memory\n");

    /* Edges. */
    /* Euler's formula - at most 3n edges on a set of n sites */
    n_free_e = 3 * n;
    edges = e = (struct edge *) calloc(n_free_e, sizeof(struct edge));
    if (edges == NULL)
        problem("Not enough memory\n");
    free_list_e = (struct edge **) calloc(n_free_e, sizeof(struct edge *));
    if (free_list_e == NULL)
        problem("Not enough memory\n");
    for (i = 0; i < n_free_e; i++, e++)
        free_list_e[i] = e;
}

void free_memory(){
    free(sites);
    free(edges);
    free(free_list_e);
}

struct edge *get_edge(){
    if (n_free_e < 1) problem("All allocated edges have been used\n");
    return (free_list_e[--n_free_e]);
}

void free_edge(struct edge *e){
    free_list_e[n_free_e++] = e;
}
