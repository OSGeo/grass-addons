/* 

   Copyright (C) 2006 Thomas Hazel, Laura Toma, Jan Vahrenhold and
   Rajiv Wickremesinghe

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License as
   published by the Free Software Foundation; either version 2 of the
   License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful, but
   WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   General Public License for more details.

*/

#ifndef _PQUEUECS_H
#define _PQUEUECS_H

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>

#include <grass/iostream/mm.h>

/* this is a copy of ijCost */
class  costStructure{
 public: 
  cost_type cost;  //the priority
  dimension_type i,j; 

  /***************************************************/
  costStructure(const cost_type c =0, 
		const dimension_type gi=0, const dimension_type gj=0) {
    cost = c; 
    i = gi; 
    j = gj;
  }
  
/*   costStructure(const costStructure &cs) { */
/*     cost = cs.cost; */
/*     i = cs.i; */
/*     j = cs.j;  */
/*   } */

/*   costStructure(const ijCost &ct) { */
/*     cost = ct.getCost(); */
/*     i = ct.getI(); */
/*     j = ct.getJ(); */
/*   } */

/*   ~costStructure() {} */
  
  static void swap(costStructure *a, costStructure *b) {
	costStructure tmp;

	tmp = *a;
	*a = *b;
	*b = tmp;

/*     cost_type cost = a->getCost(); */
/* 	a->cost = b->cost; */
/* 	b->cost = cost; */

/*     dimension_type i = a->i; */
/* 	a->i = b->i; */
/* 	b->i = i; */

/*     dimension_type j = a->j; */
/* 	a->j = b->j; */
/* 	b->j = j; */
  }


/*   cost_type getCost() const { */
/*     return cost; */
/*   } */

  cost_type getPriority() const {
    return cost;
  }
  
  dimension_type getI() const {
    return i;
  }

  dimension_type getJ() const {
    return j;
  }

  friend ostream& operator<<(ostream& s, const costStructure &cs) {
    return s << "[<prio=" << cs.cost << "> " << cs.i << "," << cs.j <<"]";
  }
  
  friend int operator < (const costStructure &c1, 
			 const costStructure &c2) {
    return (c1.cost < c2.cost);
  }

  friend int operator <= (const costStructure &c1, 
			  const costStructure &c2) {
    return (c1.cost <= c2.cost);
  }
  friend int operator > (const costStructure &c1, 
			 const costStructure &c2) {
    return (c1.cost > c2.cost);
  }
  friend int operator >= (const costStructure &c1,
			  const costStructure &c2) {
    return (c1.cost >= c2.cost);
  }
  friend int operator == (const costStructure &c1, 
			   const costStructure &c2) {
    return (c1.cost == c2.cost);
  }
  friend int operator != (const costStructure &c1, 
			   const costStructure &c2) {
    return (c1.cost != c2.cost);
  }

  static int qscompare(const void *a, const void *b) {
    costStructure* x, *y;
    x = (costStructure*) a;
    y = (costStructure*) b;
    if (*x < *y) return -1;
    if (*x == *y) return 0;
    return 1;
  }
};








/* ************************************************** */
// Helper functions for navigating through a binary heap.
/* for simplicity the heap structure is slightly modified as:
   0
   |
   1
   /\
  2  3
 /\  /\
4 5 6  7

*/

// The children of an element of the heap.
static inline unsigned int heap_lc(unsigned int index) {
  return 2 * index;
}

static inline unsigned int heap_rc(unsigned int index) {
  return 2 * index + 1;
}

// The parent of an element.
static inline unsigned int heap_p(unsigned int index) {
  return index >> 1;
}


// return minimum of two integers
//static unsigned int min(unsigned int a, unsigned int b) {
//  return (a<=b)? a:b;
//}



class pqheap_ijCost {
 public: 
  // A pointer to an array of elements
  costStructure* elements;
  
  // The number of elements currently in the queue.
  unsigned int cur_elts;
  
  // The maximum number the queue can hold.
  unsigned int max_elts;

private:

  /* this function is recursive; replaced by iterative version below */
  void heapifyx(unsigned int root) {
    unsigned int min_index = root;
    unsigned int lc = heap_lc(root);
    unsigned int rc = heap_rc(root);
    
    if ((lc < cur_elts) && 
		((elements[lc].getPriority()) < elements[min_index].getPriority())) {
      min_index = lc;
    }
    if ((rc < cur_elts) && 
		((elements[rc].getPriority()) < elements[min_index].getPriority())) {
      min_index = rc;
    }
    
    if (min_index != root) {	/* need to recurse */
/*       costStructure tmp_q = elements[min_index]; */
/*       elements[min_index] = elements[root]; */
/*       elements[root] = tmp_q; */
	  costStructure::swap(&elements[root], &elements[min_index]);
      heapify(min_index);
    }
  }   

  /* iterative version of heapify, above */
   void heapify(unsigned int root) {
	 unsigned int min_index = root;

	do {
	   root = min_index;

	   unsigned int lc = heap_lc(root);
	   unsigned int rc = heap_rc(root);
	   
	   if ((lc < cur_elts) && 
		   ((elements[lc].getPriority()) < elements[min_index].getPriority())) {
		 min_index = lc;
	   }
	   if ((rc < cur_elts) && 
		   ((elements[rc].getPriority()) < elements[min_index].getPriority())) {
		 min_index = rc;
	   }
	   if (min_index != root) {
		 costStructure::swap(&elements[root], &elements[min_index]);
	   }
	} while (min_index != root);


  }   
  
public:
  /****************************************************/
  pqheap_ijCost(unsigned int size) {
    assert(size>0);
    //elements = new costStructure [size];
    elements = (costStructure *)malloc(sizeof(costStructure) * size);
    MM_manager.register_allocation(sizeof(costStructure) * size);
    assert(elements);
	if(!elements) {
	  fprintf(stderr, "malloc failed\n");
	  exit(1);
	}
    max_elts = size;
    cur_elts = 0;
    // cout << "maxelts=" << max_elts << ", cur_elts=" << cur_elts << endl;
  }

  /****************************************************/
  pqheap_ijCost() {
    cerr << "not implemented;";
    exit(1);
  }

  /****************************************************/
  ~pqheap_ijCost() {
    //delete [] elements;
	free(elements);
    MM_manager.register_deallocation(sizeof(costStructure) * max_elts);
    cur_elts = 0;
    max_elts = 0;
  }
  /****************************************************/

  /* returns success */
  int grow() {
	costStructure *ptr;

	fprintf(stderr, "pqueue: doubling pq from %d elts\n", max_elts);
	MM_manager.register_allocation(sizeof(costStructure) * max_elts);

	ptr = (costStructure *)realloc(elements, sizeof(costStructure) * max_elts * 2);
	if(!ptr) {
	  fprintf(stderr, "Warning: realloc failed");
	  //return 0; 
	  /* 09/13/2005: this was not checked properly, and generated
	     an infinite nb calls to grow() */
	  exit(0);
	} 

	elements = ptr;
	max_elts *= 2;
	return 1;
  }

  /****************************************************/
  void clear() {
    cur_elts = 0;
  }
  
  /****************************************************/
  // Is it full?
  int full(void) {
    return cur_elts == max_elts;
  }
  
  /****************************************************/
  //Is it empty?
  int empty() {
    return cur_elts == 0;
  }
 
  /****************************************************/
  unsigned int size() {
    return cur_elts;
  }
  
  /****************************************************/
  unsigned int maxsize() {
    return max_elts;
  }
  
  /****************************************************/
  // min
  int min(costStructure* elt) {
    if (empty()) return 0;
    *elt = elements[0];
    return 1;
  }
  
  /****************************************************/
  //min
  costStructure min() {
    costStructure elt;
    if(min(&elt)) return elt;
    else {
      assert(0);
      exit(1);
    }
    //should never get here (to avoid warning)
    return elt;
  }

  /****************************************************/
  // Extract min and set elt = min
  int extract_min(costStructure* elt) {
    if (empty()) return 0;
    *elt = elements[0];
    elements[0] = elements[--cur_elts];
    heapify(0);
    return 1;
  }
  
  /****************************************************/
  //delete min; same as extract_min, but ignore the value extracted
  int delete_min() {
    costStructure dummy;
    return extract_min(&dummy);
  }


  /****************************************************/
  // Insert
  int insert(const costStructure elt) {
    //cout << "PQ:insert: cur_elts=" << cur_elts << ",max_elts= "<< max_elts << endl;
    unsigned int ii;
    if (full()) {
	  //return 0;
	  if(!grow()) {
		return 0;
	  }
	}
    for (ii = cur_elts++;
	 ii && (elements[heap_p(ii)].getPriority() > elt.getPriority());
	 ii = heap_p(ii)) {
      elements[ii] = elements[heap_p(ii)];
    }
    elements[ii] = elt;
    return 1;
  }                                    

  /****************************************************/
  //Delete the current minimum and insert the new item x; 
  //the minimum item is lost (i.e. not returned to user); 
  //needed to optimize merge 
  void delete_min_and_insert(const costStructure x) {
    elements[0] = x;
    heapify(0);
  }

  /****************************************************/
  //print the first 10 elements in the pq
  friend ostream& operator<<(ostream& s, const pqheap_ijCost &pq) {
    s << "PQ: "; s.flush();
    for (unsigned int i=0; i< pq.cur_elts; i++) {
      s <<  "[" << pq.elements[i] << "]";
    }
    return s;
  }

};



#endif 
