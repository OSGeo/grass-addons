#include "local_proto.h"

void insert_rectangle(int dim, int i, struct points *pnts)
{
  struct RTree_Rect *rect; // rectangle
  double *r;               // pointer to the input coordinates
  r = &pnts->r[3 * i];

  switch (dim) {
  case 3: // 3D:
    rect = RTreeAllocRect(pnts->R_tree); // allocate the rectangle
    RTreeSetRect3D(rect, pnts->R_tree, 
		   *r, *r, 
		   *(r+1), *(r+1), 
		   *(r+2), *(r+2)); // set 3D coordinates
    RTreeInsertRect(rect, i + 1, pnts->R_tree); // insert rectangle to the spatial index
    break;
  case 2: // 2D:
    rect = RTreeAllocRect(pnts->Rtree_hz); // allocate the rectangle
    RTreeSetRect2D(rect, pnts->Rtree_hz, 
		   *r, *r, 
		   *(r+1), *(r+1)); // set 2D coordinates
    RTreeInsertRect(rect, i + 1, pnts->Rtree_hz); // insert rectangle to the spatial index
    break;
  case 1: // 1D
    rect = RTreeAllocRect(pnts->Rtree_vert); // allocate the rectangle
    RTreeSetRect1D(rect, pnts->Rtree_vert, 
		   *(r+2), *(r+2)); // set 1D coordinates
    RTreeInsertRect(rect, i + 1, pnts->Rtree_vert); // insert rectangle to the spatial index
    break;
  } 
   
  RTreeFreeRect(rect); // free rectangle memory
}

/* find neighbors in cubic (square) surroundings */
struct ilist *find_NNs_within(int dim, double *search_pt, struct points *pnts, double max_dist, double max_dist_vert)
{
  // local variables
  double *r;                         // pointer to vector of the coordinates
  r = &search_pt[0];

  int NN_sum = 0;                    // # of NN
  double dist_step = max_dist; // distance iteration in case of empty closest surrounding of search point
  double dist_step_vert = 0.1 * max_dist_vert; // vertical distance iteration
  struct RTree_Rect *search;         // search rectangle
  struct ilist *list;
  list = G_new_ilist();

  while (NN_sum < 2) { // TODO: this might be tricky - what # (density) is optimal?
    switch (dim) {
    case 3: // 3D:
      search = RTreeAllocRect(pnts->R_tree); // allocate new rectangle
      RTreeSetRect3D(search, pnts->R_tree, 
		   *r - max_dist, *r + max_dist, 
		   *(r+1) - max_dist, *(r+1) + max_dist, 
		     *(r+2) - max_dist_vert, *(r+2) + max_dist_vert); // set up searching rectangle
      RTreeSearch2(pnts->R_tree, search, list);   // search the nearest rectangle
      break;
    case 2: // 2D:
      search = RTreeAllocRect(pnts->Rtree_hz); // allocate new rectangle
      RTreeSetRect2D(search, pnts->Rtree_hz, 
		   *r - max_dist, *r + max_dist, 
		   *(r+1) - max_dist, *(r+1) + max_dist);           // set up searching rectangle
      RTreeSearch2(pnts->Rtree_hz, search, list);   // search the nearest rectangle
      break;
    case 1: // 1D:   
      search = RTreeAllocRect(pnts->Rtree_vert); // allocate new rectangle
      RTreeSetRect1D(search, pnts->Rtree_vert, 
		   *(r+2) - max_dist_vert, *(r+2) + max_dist_vert); // set up searching rectangle

      RTreeSearch2(pnts->Rtree_vert, search, list);   // search the nearest rectangle
      break;
    }
    RTreeFreeRect(search);

    NN_sum = list->n_values;
    max_dist += dist_step;
    max_dist_vert += dist_step_vert;
  } // end while: nonzero # of NNs

  return list;
}

/* find neighbors in spherical (circular) surroundings */
struct ilist *find_n_NNs(int dim, int i, struct points *pnts, int n)
{
  // local variables
  double max_dist0 = pnts->max_dist; // initial maximum distance
  struct ilist *list;                        // list of selected rectangles (points)

  int n_vals = 0;              // # of the nearest neighbours (NN)
  int iter = 1;                // iteration number (searching NN)
  double max_dist = max_dist0; // iterated search radius
  double *search;
  search = &pnts->r[3 * i];

  while (n_vals < n) { // until some NN is found (2 points: identical and NN)
    list = find_NNs_within(dim, search, pnts, max_dist, -1);
    n_vals = list->n_values;                 // set up control variable
    
    if (n_vals < n) {
      iter += 1;                             // go to the next iteration
      max_dist = iter * max_dist0;           // enlarge search radius
    }
  }

  // check spherical (circular) surrounding
  list = find_NNs_within(dim, search, pnts, sqrt(2.) * max_dist, -1);

  return list;
}
