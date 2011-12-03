#ifndef TOOLS_H_
#define TOOLS_H_

void run_cmd ( char *cmd );

void r_mapcalc ( char *outmap, char *cmd );

void quicksort ( double *array, int n );

char *mktmpmap ( char* prefix );

int map_exists ( char *map );

int test_map ( char *map, ... );
int test_map_f ( char *map, ... );

#endif /*TOOLS_H_*/
