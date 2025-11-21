#include "local_proto.h"

struct RTree *create_spatial_index(struct nna_par *xD)
{
    struct RTree *R_tree;    // spatial index
    struct RTree_Rect *rect; // rectangle

    if (xD->i3 == true) {                   // 3D NNA:
        R_tree = RTreeCreateTree(-1, 0, 3); // create 3D spatial index
    }
    if (xD->i3 == false) {                  // 2D NNA:
        R_tree = RTreeCreateTree(-1, 0, 2); // create 3D spatial index
    }

    return (R_tree);
}

void insert_rectangle(int i3, int i, struct points *pnts)
{
    struct RTree *R_tree;    // spatial index
    struct RTree_Rect *rect; // rectangle
    double *r;               // pointer to the input coordinates

    r = &pnts->r[3 * i];
    rect = RTreeAllocRect(pnts->R_tree); // allocate the rectangle

    if (i3 == true) { // 3D NNA:
        RTreeSetRect3D(rect, pnts->R_tree, *r, *r, *(r + 1), *(r + 1), *(r + 2),
                       *(r + 2)); // set 3D coordinates
    }

    if (i3 == false) { // 2D NNA:
        RTreeSetRect2D(rect, pnts->R_tree, *r, *r, *(r + 1),
                       *(r + 1)); // set 2D coordinates
    }

    RTreeInsertRect(rect, i + 1,
                    pnts->R_tree); // insert rectangle to the spatial index
    RTreeFreeRect(rect);           // free rectangle memory

    return;
}

/* find neighbors in cubic (square) surroundings */
struct ilist *spatial_search(int i3, int i, struct points *pnts,
                             double max_dist)
{
    // local variables
    struct RTree *R_tree = pnts->R_tree; // spatial index
    double *r;                           // pointer to vector of the coordinates

    r = &pnts->r[3 * i];

    struct ilist *list;
    struct RTree_Rect *search; // search rectangle

    list = G_new_ilist();            // create new list
    search = RTreeAllocRect(R_tree); // allocate new rectangle

    if (i3 == true) { // 3D NNA:
        RTreeSetRect3D(search, R_tree, *r - max_dist, *r + max_dist,
                       *(r + 1) - max_dist, *(r + 1) + max_dist,
                       *(r + 2) - max_dist,
                       *(r + 2) + max_dist); // set up searching rectangle
    }

    if (i3 == false) { // 2D NNA
        RTreeSetRect2D(search, R_tree, *r - max_dist, *r + max_dist,
                       *(r + 1) - max_dist,
                       *(r + 1) + max_dist); // set up searching rectangle
    }

    RTreeSearch2(R_tree, search, list); // search the nearest rectangle
    RTreeFreeRect(search);

    return list;
}

/* find neighbors in spherical (circular) surroundings */
struct ilist *find_NNs(int i3, int i, struct points *pnts)
{
    // local variables
    double max_dist0 = 0.005 * pnts->max_dist; // initial search radius
    struct ilist *list; // list of selected rectangles (points)

    int n_vals = 0;              // # of the nearest neighbours (NN)
    int iter = 1;                // iteration number (searching NN)
    double max_dist = max_dist0; // iterated search radius

    while (n_vals < 2) { // until some NN is found (2 points: identical and NN)
        list = spatial_search(i3, i, pnts, max_dist);
        n_vals = list->n_values; // set up control variable

        if (n_vals < 2) {
            iter += 1;                   // go to the next iteration
            max_dist = iter * max_dist0; // enlarge search radius
        }
    }

    // check spherical (circular) surrounding
    list = spatial_search(i3, i, pnts, sqrt(2.) * max_dist);

    return list;
}

/* sum of the distances between nearest neighbors */
double sum_NN(int i3, int i, struct ilist *list, struct points *pnts)
{
    int j;
    int n_vals = list->n_values; // # of selected points
    int *value;                  // pointer to indices of selected points

    value = &list->value[0];
    *value -= 1; // decrease index of selected point by 1 (because rectangle IDs
                 // start by 1, not by 0 like point IDs)

    double *r0 = &pnts->r[3 * i]; // pointer to search point coordinates
    double *r =
        &pnts->r[3 * *value]; // pointer to the coordinates of selected point
    double dx, dy,
        dz; // coordinate differences between search and selected point
    double dist, *sqDist, *d; // vector of squared distances

    sqDist = (double *)G_malloc(n_vals * sizeof(double));
    d = &sqDist[0]; // pointer to vector of squared distances

    for (j = 0; j < n_vals; j++) { // for each rectangle:
        dx = *r0 - *r;
        dy = *(r0 + 1) - *(r + 1);

        if (i3 == true) {              // 3D NNA:
            dz = *(r0 + 2) - *(r + 2); // compute also 3rd difference
        }

        *d = dx * dx + dy * dy; // squared distance

        if (i3 == true) {  // 3D NNA:
            *d += dz * dz; // use also the difference in z
        }

        d++; // go to the next distance

        value++;     // go to the index of the next selected point
        *value -= 1; // decrease the index by 1
        r += 3 * (*value - *(value - 1)); // go to the next selected point
    }

    qsort(&sqDist[0], n_vals, sizeof(double),
          cmpVals);         // sort squared distances
    dist = sqrt(sqDist[1]); // save the second one (1st NN is identical to the
                            // search point)

    G_free(sqDist);     // free memory of the vector of squared distances
    G_free_ilist(list); // free list of selected points

    return dist;
}
