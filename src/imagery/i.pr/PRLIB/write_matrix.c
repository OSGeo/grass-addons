#include <grass/gis.h>
#include <stdio.h>

void write_matrix(char *outfile, double **matrix, int r, int c)
{
    FILE *fp;
    int i, j;
    char tempbuf[500];

    fp = fopen(outfile, "w");
    if (fp == NULL) {
        sprintf(tempbuf, "write_matrix-> Can't open file <%s> for writing",
                outfile);
        G_fatal_error(tempbuf);
    }

    for (i = 0; i < r; i++) {
        fprintf(fp, "%e", matrix[i][0]);
        for (j = 1; j < c; j++)
            fprintf(fp, "\t%e", matrix[i][j]);
        fprintf(fp, "\n");
    }
    fclose(fp);
}
