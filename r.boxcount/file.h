#ifndef FILEH
#define FILEH

#include <stdio.h>
#include "record.h"

FILE* Create_file (char*, char*, char*, int);
void Pretty_print (FILE*, tRecord*, int, int, int, float*);
void Functional_print (FILE*, tRecord*, int, float*);
void Print_gnuplot_commands (FILE*, char*, tRecord*, int, int, int, float*);
void Terse_print (FILE*, int, int, float*);

#endif
