#include "local_proto.h"

void parse_line(DCELL *values, char *buffer, int id_col, int val_col)
{
    int counter = 1;
    char *p = buffer;
    int id;
    DCELL value;

    while (*p != 0) {

        /* if current column is the id column or value column, then read value
         */
        if (counter == id_col) {
            sscanf(p, "%d", &id);
        }
        if (counter == val_col) {
            sscanf(p, "%lf", &value);
        }

        /* skip to next column */
        while (!(*p == 0 || *p == ' ')) {
            p++;
        }

        counter++;

        if (*p != 0) {
            p++;
        }
    }

    values[id] = value;
}

void parse(DCELL *values, char *file_name, int id_col, int val_col,
           int fragcount)
{
    char buffer[GNAME_MAX];
    FILE *fp;

    fp = fopen(file_name, "r");

    /* fill values with NULL */
    Rast_set_d_null_value(values, fragcount);

    if (fp == NULL) {
        G_fatal_error("Couldn't open input file!");
    }

    /* read lines */
    while (fgets(buffer, GNAME_MAX, fp)) {
        parse_line(values, buffer, id_col, val_col);
    }

    fclose(fp);
}
