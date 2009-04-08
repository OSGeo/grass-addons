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


#ifndef _PQ_H
#define _PQ_H

#include "types.h"

class costStructureOld;
class costPriorityOld;
class costValueOld;


class costPriorityOld {
 public:
  cost_type dist;

 public:
  costPriorityOld(cost_type a=0):
    dist(a) {}

  costPriorityOld(const costPriorityOld &c):
    dist(c.dist) {}

  ~costPriorityOld() {}

  cost_type getDist() {
    return dist;
  };

  void set (cost_type g_c, dimension_type g_i, dimension_type g_j) {
    dist = g_c;
  };

  friend ostream& operator<<(ostream& s, const costPriorityOld &pri) {
    return s << pri.dist;
  };

  
  friend istream& operator>>(istream& s, costPriorityOld &pri) {
    return s >> pri.dist;
  };

  friend int operator < (const costPriorityOld &p1, 
			 const costPriorityOld &p2) {
    return p1.dist < p2.dist;
  };

  friend int operator <= (const costPriorityOld &p1, 
			  const costPriorityOld &p2) {
    return p1.dist <= p2.dist;
  };
  
  friend int operator > (const costPriorityOld &p1, 
			 const costPriorityOld &p2) {
    return p1.dist > p2.dist;
  };

   friend int operator >= (const costPriorityOld &p1, 
			  const costPriorityOld &p2) {
     return p1.dist >= p2.dist;
   };

   friend bool operator==(const costPriorityOld &p1, 
			 const costPriorityOld &p2) {
     return p1.dist == p2.dist;
   };

   friend bool operator!=(const costPriorityOld &p1, 
			  const costPriorityOld &p2) {
     return p1.dist != p2.dist;
   };

};


class costValueOld {
 public:
  dimension_type i,j;

 public:
  costValueOld(dimension_type a=0, dimension_type b=0):
    i(a), j(b) {}

  ~costValueOld() {}

  dimension_type getI() const {
    return i;
  }

  dimension_type getJ() const {
    return j;
  }

  int isNull() {
    //return (i == NODATA && j == NODATA);
    return (i == dim_undef && j == dim_undef); // shouldnt this be OR?
  }

  friend ostream& operator<<(ostream& s, const costValueOld &cst) {
    return s << "(" << cst.i << "," << cst.j << ")";
  }

  /*
  friend istream& operator>>(istream& s, costValueOld &cst) {
    return s >> "(" >> cst.i >> "," >> cst.j >> ")";
  }
  */
  

  /*
  friend costValueOld operator +(const costValueOld &cst1, 
			      const costValueOld &cst2) {
    costValueOld cst(cst1.value + cst2.value);
    return cst;
  }
  */
/*   costValueOld operator =(const costValueOld &cst) { */
/*     i = cst.getI(); */
/*     j = cst.getJ(); */
/*     return *this; */
/*   }  */

  costValueOld operator != (const costValueOld &cst) {
    return ((i != cst.getI()) || (j != cst.getJ()));
   
  }
  costValueOld operator == (const costValueOld &cst) {
    return ((i == cst.getI()) && (j == cst.getJ()));
  }
  
  friend int operator > (const costValueOld &p1, const costValueOld &p2) {
    if (p1.i > p2.i) return 1;
    if ((p1.i == p2.i) && (p1.j > p2.j)) return 1;
    return 0;
  }
  friend int operator >= (const costValueOld &p1, 
			  const costValueOld &p2) {
    return ((p1>p2) || ((p1.i == p2.i) && (p1.j == p2.j)));
  }
  friend int operator < (const costValueOld &p1, 
			 const costValueOld &p2) {
    if (p1.i < p2.i) return 1;
    if ((p1.i == p2.i) && (p1.j < p2.j)) return 1;
    return 0;
  }
    friend int operator <= (const costValueOld &p1, 
			  const costValueOld &p2) {
    return ((p1 < p2) || ((p1.i == p2.i) && (p1.j == p2.j)));
  }

};

class costStructureOld {
 private:
  costPriorityOld prio;
  costValueOld val;

 public: 
  
  costStructureOld(const costPriorityOld &p = 0, const costValueOld &e = 0):
    prio(p), val(e) {}

/*   costStructureOld(const costStructureOld &cs) { */
/*     prio = cs.prio; */
/*     val = cs.val; */
/*   } */

  costStructureOld(const ijCost &ct) {
    prio = ct.getCost();
    dimension_type i = ct.getI();
    dimension_type j = ct.getJ();
    val = costValueOld(i,j);
  }

  costStructureOld(dimension_type i, dimension_type j, cost_type p) {
    prio = p;
    val = costValueOld(i,j);
  }

/*   ~costStructureOld() {} */
  
  costPriorityOld getPriority() const {
    return prio;
  }
  
  costValueOld  getValue() const {
    return val;
  }

  dimension_type getI() {
    return val.getI();
  }

  dimension_type getJ() {
    return val.getJ();
  }

  friend ostream& operator<<(ostream& s, const costStructureOld &cs) {
    return s << "[<prio=" << cs.prio << "> " << cs.val <<"]";
  }
  
  friend int operator < (const costStructureOld &c1, 
			 const costStructureOld &c2) {
    return (c1.prio < c2.prio);
  }

  friend int operator <= (const costStructureOld &c1, 
			  const costStructureOld &c2) {
    return (c1.prio <= c2.prio);
  }
  friend int operator > (const costStructureOld &c1, 
			 const costStructureOld &c2) {
    return (c1.prio > c2.prio);
  }
  friend int operator >= (const costStructureOld &c1,
			  const costStructureOld &c2) {
    return (c1.prio >= c2.prio);
  }
  friend bool operator == (const costStructureOld &c1, 
			   const costStructureOld &c2) {
    return (c1.prio == c2.prio);
  }
  friend bool operator != (const costStructureOld &c1, 
			   const costStructureOld &c2) {
    return (c1.prio != c2.prio);
  }

  static int qscompare(const void *a, const void *b) {
    costStructureOld* x, *y;
    x = (costStructureOld*) a;
    y = (costStructureOld*) b;
    if (*x < *y) return -1;
    if (*x == *y) return 0;
    return 1;
  }

};

#endif
