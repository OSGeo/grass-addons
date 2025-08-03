/***********************************************************************/
/*
   file.c

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#include <stdlib.h>
#include <string.h>
#include "file.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

FILE *Create_file(char *name, char *suffix, char *message, int overwrite)
{
    FILE *stream;
    int exists = 0;

    strcat(name, suffix);
    stream = fopen(name, "r");
    if (stream != NULL)
        exists = 1;

    if ((exists) && (!overwrite)) {
        sprintf(message, _("File <%s> exits "), name);
        fclose(stream);
        return NULL;
    }
    else {
        stream = fopen(name, "w");

        if (stream == NULL) {
            sprintf(message, _("Can't create file <%s> "), name);
            return NULL;
        }
    }

    if (exists && overwrite)
        G_message(_("Overwriting output file <%s> \n"), name);
    else
        G_message(_("Writing output file <%s> \n"), name);

    return (stream);
}
