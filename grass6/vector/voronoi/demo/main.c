#include "data_types.h"
#include "memory.h"
#include "edge.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int compare(const struct vertex **p1, const struct vertex **p2);

int main(int argc, char *argv[]){
    
    unsigned int i;
    unsigned int n;
    struct edge *l_cw, *r_ccw;
    struct vertex **sites_sorted;

    printf("Enter number of sites: ");
    if (scanf("%d", &n) != 1)
        problem("Number of sites could not be read.");
    if (n <= 0) 
        problem("Number of sites has to be positive integer.");

    alloc_memory(n);
    //read_points(n);

    srand((unsigned int)time(0));
    for (i = 0; i < n; i++){
        sites[i].x = rand() % 1260 + 10;
        sites[i].y = rand() % 780 + 10;
    }

    /* Initialise entry edge vertices. */
    for (i = 0; i < n; i++)
        sites[i].entry_pt = NULL;
    /* Sort. */
    sites_sorted = (struct vertex **) malloc((unsigned)n*sizeof(struct vertex *));
    if (sites_sorted == NULL)
        problem("Not enough memory\n");
    for (i = 0; i < n; i++)
        sites_sorted[i] = sites + i;

    qsort(sites_sorted, n, sizeof(struct vertex *), (void *)compare);

//     for (i = 0; i < n; i++)
//         printf("(%3d)  x=%3.0f y=%3.f\n", i, sites[i].x, sites[i].y);

    /* Triangulate. */
    divide(sites_sorted, 0, n-1, &l_cw, &r_ccw);

    free((char *)sites_sorted);

    draw(n);

    free_memory();

    exit(EXIT_SUCCESS);
    return 0;	/* To keep lint quiet. */
}

/* compare first according to x-coordinate, if equal then y-coordinate */
int compare(const struct vertex **p1, const struct vertex **p2){
    if ((*p1)->x == (*p2)->x) return ((*p1)->y < (*p2)->y);
    return ((*p1)->x < (*p2)->x);
}
