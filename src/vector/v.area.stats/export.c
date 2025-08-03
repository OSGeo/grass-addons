#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "global.h"

char *join(const char *sep, char **string_list, int llen, char *buf)
{
    int i;

    strcpy(buf, string_list[0]);
    strcat(buf, sep);
    for (i = 1; i < llen; i++) {
        strcat(buf, string_list[i]);
        if (i < llen - 1)
            strcat(buf, sep);
    }
    strcat(buf, "\n");
    /* G_debug(4, "buf: %s", buf); */

    return buf;
}

int get_str_length(char **string_list, int llen, int seplen)
{
    int i;
    int slen = llen * seplen + 1;

    G_debug(3, "Compute the length of the final string");
    for (i = 0; i < llen; i++) {
        slen += strlen(string_list[i]);
    }
    return slen;
}

int get_vals(char **str_vals, struct value val)
{
    G_debug(3,
            "Copy the values from the struct"
            " for area <%d> to a list of strings.",
            val.area_id);
    sprintf(str_vals[AREA_ID], "%d", val.area_id);
    sprintf(str_vals[CAT], "%d", val.cat);
    sprintf(str_vals[NISLES], "%d", val.nisles);
    sprintf(str_vals[X_EXTENT], "%f", val.x_extent);
    sprintf(str_vals[Y_EXTENT], "%f", val.y_extent);
    sprintf(str_vals[IPERIMETER], "%f", val.iperimeter);
    sprintf(str_vals[IAREA], "%f", val.iarea);
    sprintf(str_vals[ICOMPACT], "%f", val.icompact);
    sprintf(str_vals[IFD], "%f", val.ifd);
    sprintf(str_vals[PERIMETER], "%f", val.perimeter);
    sprintf(str_vals[AREA], "%f", val.area);
    sprintf(str_vals[BOUNDAREA], "%f", val.boundarea);
    sprintf(str_vals[ARATIO], "%f", val.aratio);
    sprintf(str_vals[COMPACT], "%f", val.compact);
    sprintf(str_vals[FD], "%f", val.fd);
    return 0;
}

int export2csv(int length)
{
    int i, idx, buflen;
    int len = LENVALS + 1;
    FILE *fp;

    G_debug(2, "Allocate memory to copy and write the results");
    char **str_vals = (char **)calloc(len, sizeof(char *));

    for (i = 0; i <= len; i++) {
        str_vals[i] = (char *)G_calloc(STRLEN, sizeof(char));
    }

    G_debug(2, "Allocate memory for row buffer");
    get_vals(str_vals, Values[0]);
    buflen = get_str_length(str_vals, LENVALS, strlen(options.separator));
    buflen += 128; /* for safety reasons */
    char *buf = (char *)G_calloc(buflen, sizeof(char));

    G_debug(2, "Open the file to write the results.");
    if (options.out != NULL && strcmp(options.out, "-") != 0) {
        fp = fopen(options.out, "w");
        if (fp == NULL) {
            G_fatal_error(_("Unable to open file <%s> for writing"),
                          options.out);
        }
    }
    else
        fp = stdout;

    G_debug(2, "Start copying the results.");
    for (idx = 1; idx <= length; idx++) {
        if (Values[idx].area_id) {
            get_vals(str_vals, Values[idx]);
            buf = join(options.separator, str_vals, LENVALS, buf);
            G_debug(3, "buf:%s", buf);
            fprintf(fp, buf);
        }
    }

    if (fp != stdout)
        fclose(fp);

    /* free string list */
    G_free((void *)str_vals);
    G_free((void *)buf);

    return 0;
}
