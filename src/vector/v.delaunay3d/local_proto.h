#ifndef __LOCAL_PROTO_H__

#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Triangulation_3.h>
#include <CGAL/Delaunay_triangulation_3.h>

typedef CGAL::Exact_predicates_inexact_constructions_kernel K;

typedef CGAL::Triangulation_3<K> Triangulation;
typedef CGAL::Delaunay_triangulation_3<K> DelaunayTriangulation;
typedef Triangulation::Point Point;

/* read.cpp */
int read_points(struct Map_info *, int, std::vector<Point> &);

/* write.cpp */
void write_lines(struct Map_info *, int, const Triangulation *);
#endif
