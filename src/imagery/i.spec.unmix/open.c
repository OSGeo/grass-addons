/* Spextral unmixing */
/* (c) 15. Jan. 1999 Markus Neteler, Hannover */

/* Cited references are from
   Steward, D.E, Leyk, Z. 1994: Meschach: Matrix computations in C.
   Proceedings of the centre for Mathematics and its Applicaions.
   The Australian National University. Vol. 32.
   ISBN 0 7315 1900 0
 */

#include <stdio.h>
#include <math.h>
#include <grass/imagery.h>
#include <grass/gmath.h>
#include <grass/glocale.h>
#include "global.h"

int G_matrix_read2(
    FILE *fp, mat_struct *out); /* Modified version of G_matrix_read(..). */

mat_struct *open_files(char *matrixfile, char *img_grp, char *result_prefix,
                       char *iter_name, char *error_name)
{
    char result_name[80];

    FILE *fp;
    int i, matrixsize;
    mat_struct A_input, *A;

    /* Read in matrix file with spectral library.
     * Input matrix must contain spectra row-wise (for user's convenience)!
     * Transposed here to col-wise orientation (for modules/mathematical
     * convenience).
     */

    if ((fp = fopen(matrixfile, "r")) == NULL)
        G_fatal_error(_("Matrix file %s not found."), matrixfile);

    /* Read data and close file */
    if ((G_matrix_read2(fp, &A_input) < 0))
        G_fatal_error(_("Unable to read matrix file %s."), matrixfile);
    fclose(fp);

#if 0
    G_message(_("Your spectral matrix = %d"), m_output(A_input));
#endif

    /* transpose input matrix from row orientation to col orientation.
     * Don't mix rows and cols in the source code and the modules
     * messages output!
     */

    A = G_matrix_init(A_input.rows, A_input.cols, A_input.rows);
    if (A == NULL)
        G_fatal_error(_("Unable to allocate memory for matrix"));

    A = G_matrix_transpose(&A_input);

    if ((A->rows) < (A->cols))
        G_fatal_error(
            _("Need number of cols >= rows to perform least squares fitting."));

    /* number of rows must be equivalent to no. of bands */
    matrixsize = A->rows;

    /* open input files from group */
    if (!I_find_group(img_grp))
        G_fatal_error(_("Unable to find imagery group %s."), img_grp);

    I_get_group_ref(img_grp, &Ref);
    if (Ref.nfiles <= 1) {
        if (Ref.nfiles <= 0)
            G_fatal_error(_("Group %s does not have any rasters. "
                            "The group must have at least 2 rasters."),
                          img_grp);
        else
            G_fatal_error(_("Group %s only has 1 raster. "
                            "The group must have at least 2 rasters."),
                          img_grp);
    }

    /* Error check: input file number must be equal to matrix size */
    if (Ref.nfiles != matrixsize)
        G_fatal_error(_("Number of input files (%i) in group <%s> "
                        "does not match number of spectra in matrix. "
                        "(contains %i cols)."),
                      Ref.nfiles, img_grp, A->rows);

    /* get memory for input files */
    cell = (CELL **)G_malloc(Ref.nfiles * sizeof(CELL *));
    cellfd = (int *)G_malloc(Ref.nfiles * sizeof(int));
    for (i = 0; i < Ref.nfiles; i++) {
        cell[i] = Rast_allocate_c_buf();

        G_message(_("Opening input file no. %i [%s]"), (i + 1),
                  Ref.file[i].name);

        if ((cellfd[i] = Rast_open_old(Ref.file[i].name, Ref.file[i].mapset)) <
            0)
            G_fatal_error(_("Unable to open <%s>"), Ref.file[i].name);
    }

    /* open files for results */
    result_cell = (CELL **)G_malloc(A->cols * sizeof(CELL *));
    resultfd = (int *)G_malloc(A->cols * sizeof(int));

    for (i = 0; i < A->cols; i++) { /* no. of spectra */
        sprintf(result_name, "%s.%d", result_prefix, (i + 1));
        G_message(_("Opening output file [%s]"), result_name);

        result_cell[i] = Rast_allocate_c_buf();
        if ((resultfd[i] = Rast_open_c_new(result_name)) < 0)
            G_fatal_error(_("GRASS-DB internal error: Unable to proceed."));
    }
    /* open file containing SMA error */
    error_cell = NULL;
    error_fd = -1;
    if (error_name) {
        G_message(_("Opening error file [%s]"), error_name);

        if ((error_fd = Rast_open_c_new(error_name)) < 0)
            G_fatal_error(_("Unable to create error layer [%s]"), error_name);
        else
            error_cell = Rast_allocate_c_buf();
    }

    /* open file containing number of iterations */
    iter_cell = NULL;
    iter_fd = -1;
    if (iter_name) {
        G_message(_("Opening iteration file [%s]"), iter_name);

        if ((iter_fd = Rast_open_c_new(iter_name)) < 0)
            G_fatal_error(_("Unable to create iterations layer [%s]"),
                          iter_name);
        else
            iter_cell = Rast_allocate_c_buf();
    }

    /* give back number of output files (= Ref.nfiles) */
    return A;
}

int G_matrix_read2(FILE *fp, mat_struct *out)
{
    char buff[4096];
    int rows, cols;
    int i, j, row;
    double val;

    /* skip comments */
    for (;;) {
        if (!G_getl2(buff, sizeof(buff), fp))
            return -1;
        if (buff[0] != '#')
            break;
    }

    if (sscanf(buff, "Matrix: %d by %d", &rows, &cols) != 2) {
        G_warning(_("Input Matrix format error: %s"), buff);
        return -1;
    }

    G_matrix_set(out, rows, cols, rows);

    for (i = 0; i < rows; i++) {
        if (fscanf(fp, "row%d:", &row) != 1) {
            G_warning(_("Input row format error: %d"), row);
            return -1;
        }

        for (j = 0; j < cols; j++) {
            if (fscanf(fp, "%lf:", &val) != 1) {
                G_warning(_("Input column format error: %f"), val);
                return -1;
            }

            fgetc(fp);
            G_matrix_set_element(out, i, j, val);
        }
    }

    return 0;
}
