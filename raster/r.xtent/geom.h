#ifndef GEOM_H_
#define GEOM_H_

/* distance calculation helpers */
int get_closest_point ( double x, double y, GVT_map_s *map );
double get_distance ( double x, double y, double *costs, GVT_map_s *map );
/* normalization helpers */
double get_max_distance_region ( GVT_map_s *map );
double get_max_size ( double *C, GVT_map_s *map );

#endif /*GEOM_H_*/
