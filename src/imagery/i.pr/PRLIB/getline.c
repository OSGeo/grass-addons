/*
   The following routine is written and tested by Stefano Merler

   for

   getting a line from a buffered stream
 */

#include <string.h>
#include <stdio.h>
#include "global.h"

char *GetLine(fp)
/*
   get a line from a buffered stream (pointed from fp)
 */
FILE *fp;
{
    char line[BUFFSIZE], *p = NULL;

    strcpy(line, "");

    while (strlen(line) == 0 && !feof(fp)) {
        p = fgets(line, BUFFSIZE, fp);
        if (*line == '#' || strlen(line) == 1)
            strcpy(line, "");
    }

    if (p) {
        line[strlen(line) - 1] = '\0';
        return (char *)strdup(line);
    }
    else
        return NULL;
}
