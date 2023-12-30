#include "local_proto.h"

int writeDistMatrixAndID(char *name, Coords **frags, int count)
{
    FILE *out_fp;
    int res = 0;
    int out_fd;
    int row, col, i;
    DCELL *result;

    /* allocate memory for result-row */
    result = Rast_allocate_d_buf();

    /* open ASCII-file or use stdout */
    if (!(out_fp = fopen(name, "w"))) {
        fprintf(stderr, "Error creating file <%s>.", name);
        res = 1;
    }
    else {
        /* write distance matrix */
        for (row = 0; row < count; row++) {
            for (col = 0; col < count; col++) {
                fprintf(out_fp, "%f ", distmatrix[row * count + col]);
            }
            fprintf(out_fp, "\n");
        }
        fclose(out_fp);

        /* check if the new file name is correct */
        if (G_legal_filename(name) < 0) {
            G_warning(_("<%s> is an illegal file name"), name);
            res = 1;
        }

        /* open the new cellfile */
        out_fd = Rast_open_new(name, DCELL_TYPE);
        if (out_fd < 0) {
            G_fatal_error(_("can't create new cell file <%s> in mapset %s\n"),
                          name, G_mapset());
            res = 1;
        }
        else {
            /* write data */
            for (row = 0; row < nrows; row++) {
                Rast_set_d_null_value(result, ncols);

                for (i = 0; i < count; i++) {
                    for (actpos = frags[i]; actpos < frags[i + 1]; actpos++) {
                        if (actpos->y == row) {
                            result[actpos->x] = i;
                        }
                    }
                }

                Rast_put_d_row(out_fd, result);
            }
        }
        Rast_close(out_fd);
    }

    /* free memory */
    G_free(result);

    return res;
}

int writeAdjacencyMatrix(char *name, Coords **frags, int count, int *nns,
                         int nn_count)
{
    FILE *out_fp;
    int row, col, i;
    char fullname[GNAME_MAX];
    int res = EXIT_SUCCESS;

    /* open ASCII-file or use stdout */
    for (i = 0; i < nn_count; i++) {
        sprintf(fullname, "%s_%d", name, nns[i]);
        if (!(out_fp = fopen(fullname, "w"))) {
            G_fatal_error("Error creating file <%s>.", name);
            res = EXIT_FAILURE;
        }
        else {
            /* write distance matrix */
            for (row = 0; row < count; row++) {
                for (col = 0; col < count; col++) {
                    if (nearest_indices[row * patch_n + nns[i] - 1] == col) {
                        fprintf(out_fp, "1 ");
                    }
                    else {
                        fprintf(out_fp, "0 ");
                    }
                }
                fprintf(out_fp, "\n");
            }
            fclose(out_fp);
        }
    }

    return res;
}
