/*
   The following routines are written and tested by Stefano Merler

   for

   Blob and BlobSites structure management
 */

#include <stdio.h>
#include <math.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include "global.h"

static void add_points_to_blob();
static int in_blob();

void extract_sites_from_blob(Blob *blobs, int npoints, int nblobs,
                             struct Cell_head *cellhd, BlobSites *sites,
                             double **matrix)

/*extract geographical coordinates of the blob centers
   and store results in a BlobSites structure, containing the minimum
   value of the blob too (computation based on matrix) */
{
    int index, j, intindex;
    double barix, bariy;

    index = 0;
    for (j = 0; j < nblobs; j++) {
        if (index < npoints) {
            barix = .0;
            bariy = .0;
            intindex = 0;
            sites[j].max = sites[j].min =
                matrix[blobs[index].row][blobs[index].col];
            while (blobs[index].number == j) {
                if (matrix[blobs[index].row][blobs[index].col] > sites[j].max)
                    sites[j].max = matrix[blobs[index].row][blobs[index].col];
                if (matrix[blobs[index].row][blobs[index].col] < sites[j].min)
                    sites[j].min = matrix[blobs[index].row][blobs[index].col];
                barix +=
                    Rast_col_to_easting((double)blobs[index].col + .5, cellhd);
                bariy +=
                    Rast_row_to_northing((double)blobs[index].row + .5, cellhd);
                index += 1;
                intindex += 1;
            }
            sites[j].east = barix / intindex;
            sites[j].north = bariy / intindex;
            sites[j].n = intindex;
        }
    }
}

static int in_blob(int row, int col, Blob *blobs, int npoints)
{

    while (npoints > 0) {
        if (blobs[npoints - 1].row == row)
            if (blobs[npoints - 1].col == col)
                return TRUE;
        npoints -= 1;
    }
    return FALSE;
}

void find_blob(double **matrix, int r, int c, Blob **blobs, int *npoints,
               int *nblobs, double tm, double tM)

/*find blobs within a matrix and add to structure blob. A blob is
   a set of contiguous cells of a matrix, all of them with value <=
   tM and >= tm.  npoints is just a counter of cells belonging to the blob.
   nblobs is the total number of blobs. */
{
    int i, j;

    for (i = 0; i < r; i++) {
        for (j = 0; j < c; j++) {
            if ((matrix[i][j] <= tM) && (matrix[i][j] >= tm)) {
                if (!in_blob(i, j, *blobs, *npoints)) {
                    if (*npoints == 0)
                        *blobs = (Blob *)G_calloc(*npoints + 1, sizeof(Blob));
                    else
                        *blobs = (Blob *)G_realloc(*blobs, (*npoints + 1) *
                                                               sizeof(Blob));
                    (*blobs)[*npoints].row = i;
                    (*blobs)[*npoints].col = j;
                    (*blobs)[*npoints].number = *nblobs;
                    (*npoints) += 1;
                    add_points_to_blob(&blobs, npoints, *nblobs, matrix, r, c,
                                       i, j, tm, tM);
                    (*nblobs) += 1;
                }
            }
        }
    }
}

static void add_points_to_blob(Blob ***blobs, int *npoints, int nblobs,
                               double **matrix, int r, int c, int i, int j,
                               double tm, double tM)
{
    int s;
    int points_in_blob;
    int *row, *col;

    points_in_blob = 0;
    row = (int *)G_calloc(points_in_blob + 1, sizeof(int));
    col = (int *)G_calloc(points_in_blob + 1, sizeof(int));

    row[points_in_blob] = i;
    col[points_in_blob] = j;

    for (s = 0; s <= points_in_blob; s++) {
        if (row[s] > 0 && row[s] < r && col[s] > 0 && col[s] < c) {
            if ((matrix[row[s] - 1][col[s] - 1] <= tM) &&
                (matrix[row[s] - 1][col[s] - 1] >= tm)) {
                if (!in_blob(row[s] - 1, col[s] - 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] - 1;
                    (**blobs)[*npoints].col = col[s] - 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] - 1;
                    col[points_in_blob] = col[s] - 1;
                }
            }
            if ((matrix[row[s] - 1][col[s]] <= tM) &&
                (matrix[row[s] - 1][col[s]] >= tm)) {
                if (!in_blob(row[s] - 1, col[s], **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] - 1;
                    (**blobs)[*npoints].col = col[s];
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] - 1;
                    col[points_in_blob] = col[s];
                }
            }
            if ((matrix[row[s] - 1][col[s] + 1] <= tM) &&
                (matrix[row[s] - 1][col[s] + 1] >= tm)) {
                if (!in_blob(row[s] - 1, col[s] + 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] - 1;
                    (**blobs)[*npoints].col = col[s] + 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] - 1;
                    col[points_in_blob] = col[s] + 1;
                }
            }
            if ((matrix[row[s]][col[s] - 1] <= tM) &&
                (matrix[row[s]][col[s] - 1] >= tm)) {
                if (!in_blob(row[s], col[s] - 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s];
                    (**blobs)[*npoints].col = col[s] - 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s];
                    col[points_in_blob] = col[s] - 1;
                }
            }
            if ((matrix[row[s]][col[s] + 1] <= tM) &&
                (matrix[row[s]][col[s] + 1] >= tm)) {
                if (!in_blob(row[s], col[s] + 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s];
                    (**blobs)[*npoints].col = col[s] + 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s];
                    col[points_in_blob] = col[s] + 1;
                }
            }
            if ((matrix[row[s] + 1][col[s] - 1] <= tM) &&
                (matrix[row[s] + 1][col[s] - 1] >= tm)) {
                if (!in_blob(row[s] + 1, col[s] - 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] + 1;
                    (**blobs)[*npoints].col = col[s] - 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] + 1;
                    col[points_in_blob] = col[s] - 1;
                }
            }
            if ((matrix[row[s] + 1][col[s]] <= tM) &&
                (matrix[row[s] + 1][col[s]] >= tm)) {
                if (!in_blob(row[s] + 1, col[s], **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] + 1;
                    (**blobs)[*npoints].col = col[s];
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] + 1;
                    col[points_in_blob] = col[s];
                }
            }
            if ((matrix[row[s] + 1][col[s] + 1] <= tM) &&
                (matrix[row[s] + 1][col[s] + 1] >= tm)) {
                if (!in_blob(row[s] + 1, col[s] + 1, **blobs, *npoints)) {
                    **blobs = (Blob *)G_realloc(**blobs,
                                                (*npoints + 1) * sizeof(Blob));
                    (**blobs)[*npoints].row = row[s] + 1;
                    (**blobs)[*npoints].col = col[s] + 1;
                    (**blobs)[*npoints].number = nblobs;
                    *npoints += 1;
                    points_in_blob += 1;
                    row = (int *)G_realloc(row,
                                           (points_in_blob + 1) * sizeof(int));
                    col = (int *)G_realloc(col,
                                           (points_in_blob + 1) * sizeof(int));
                    row[points_in_blob] = row[s] + 1;
                    col[points_in_blob] = col[s] + 1;
                }
            }
        }
    }
}
