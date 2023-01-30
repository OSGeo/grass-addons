#include "file.h"

/**************************************************************************/

FILE *Create_file(char *name, char *suffix, char *message, int overwrite)
{
    FILE *stream;

    strcat(name, suffix);
    stream = fopen(name, "r");
    if ((stream != NULL) && (!overwrite)) {
        /* message passed to G_message or G_warning in main.c) */
        sprintf(message, _("File <%s> exits "), name);
        fclose(stream);
        return NULL;
    }
    else {
        stream = fopen(name, "w");
        /* message passed to G_message or G_warning in main.c) */
        if (stream == NULL)
            sprintf(message, _("Can't create file <%s> "), name);
    }

    return (stream);
}

/**************************************************************************/

/* void Functional_print (FILE *stream, tRecord *record, */
/*                     int k, float *coef) */
/* { */
/*   int m; */

/*   fprintf (stream, "\n  1/Box_size     Occupied    Log_1/Box_Size
 * Log_Occupied       D"); */
/*   for (m = 0; m <= k; m ++) */
/*     { */
/*       if (record [m].size != 0) */
/*      { */
/*        fprintf (stream, "\n%12lu ", (unsigned long int) (pow (2, k - m))); */
/*        fprintf (stream, "%12lu ", record [m].occupied); */
/*        fprintf (stream, "           %6.3f ", record [m].log_reciprocal_size);
 */
/*        fprintf (stream, "       %6.3f", record [m].log_occupied); */

/*        /\* Fractal dimension only calculated for pairs */
/*           of points... *\/ */

/*        if (m < k) */
/*          fprintf (stream, "  %6.3f", record [m].d); */
/*        else */

/*          /\* ...so skip the last one and print a dummy value *\/ */

/*          fprintf (stream, "  %6.3f", 99.999); */
/*      } */
/*     } */
/*   fflush (stream); */
/* } */

/**************************************************************************/
