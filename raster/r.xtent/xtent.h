#ifndef XTENT_H_
#define XTENT_H_

int get_center_xtent_original ( double x, double y, double *C, double a, double k, double *costs, double *reach, int *ruler, GVT_map_s *map );
int get_center_xtent_second ( double x, double y, double *C, double a, double k, double *diff, double *costs, int *ruler, GVT_map_s *map );

#endif /*XTENT_H_*/
