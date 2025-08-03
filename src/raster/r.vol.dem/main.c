/* r.vol.dem */
/* Purpose: Interpolate a voxel model from a series of DEMs by flood filling the
 * voxel space in between. */

/* TODO:

   BUG: output_ascii_points (): when option -f is given, the v.in.ascii module
   aborts with an error message! strangely, if you copy and paste the line from
   the tmpfile, which is exactly the same syntax, it works! (???)

   - fix warnings and license issues for chull.c (provide complete copy of the
   original sources)

   - tempfiles
   this program leaves lots of them around right now ...

   - cell counts: AVOID counting cells twice for layers that have the same
   label!

   - USER MAN PAGE:

   filling up or down does not make a difference in volume, unless -f option is
   also given! BUT: it makes a difference in the labeling of layers: When
   filling down, the bottom DEM is interpreted as the last boundary of a layer
   and is thus assigned an individual label When fillin up, the top DEM is
   interpreted as the last boundary of a layer and is thus assigned an
   individual label Where this is undesirable, boundaries can be dissolved by
   giving them identical labels using the labels= option!

   Visible differences in Paraview are due to rounding effects in the software.
   Displaying points in NVIZ will show you that both data sets are the same
   [check if this ist true: same number of points in both cases?]

   Vector hulls are currently very rough approximations with lots of
   shortcomings

   Layers are numbered from bottom to top : 0 .. n

   DEMs have to be given from bottom to top as well. Order matters!

   - LICENSE ISSUES with convex hull 3D code !(?): include at least a full
   version of original chull.c and add some comments!
   - also replace warinng messages (e.g. all points colinear) with own versions.

   - make clean and get rid of compiler warnings

   in a first pass, that can also be disabled by the user
   - check for overlaps

   in a second pass, to be optionally enabled by user:
   - create a 0/1 mask file for each DEM to mask
   out interpolation for edges that are not straight

   - fuzzy layer boundaries (!)

   - in mode -f revert interpolation direction once at the end to make sure
   everything gets filled (?)!
   - maybe as a separate option -r if it will be good for anything

   - standard options for voxels (data type ...)

   - automatically adjust 3D region to fit full DEM data (x,y,z)

   - output a map that shows areas with topologic problems. User can overlay all
   DEMs and this map and query for problems. Map will contain highest ID of the
   DEM(s) that caused a problem here. After clearing all problems, user might
   have to generate another map with errors from lower ID DEMs ... [DONE BUT
   UNTESTED]

   - DNULLVALUE needs to be adjustable, also many other vars in globals.h:
   PRECISION, TMPFILE, ...

   - EXPORTS: switch all export functions away from ASCII bridge:
   3D vector hulls output:
   - export 3D vector hulls into one GRASS bin file and create proper attribute
   table
   - 3D vector hulls don't overlap nicely, because the points are in the voxel
   centers. all hull points have to be extruded half a voxel size into normal
   direction!
   - layers with all points on one voxel plane do not get turned into a hull
   currently!
   - RRR:GGG:BBB color option for each layer
   voxel output:
   - add history information
   - a category number for each DEM (3d raster cats?)
   - RRR:GGG:BBB color option for each layer

   - surface smoothing for VTK file output
   smoothing surfaces for VTK-output with top= and bottom= options (r3.out.vtk)
   smoothes all surfaces by degrees!

   - more progress indicators in export functions!  [lots done but test what it
   looks like]

   - implement quite operation: most messages don't respect VERBOSE! [lots done,
   but needs testing]

   - v.in.ascii now takes --o for overwrite. Since when?

 */

#define MAIN

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>

#include <string.h>
#include <math.h>
#include <time.h>

#include <grass/gis.h>
#include <grass/raster3d.h>
#include <grass/glocale.h>

#include "chull.h"

#include "globals.h"

/* ================================================================================

   GLOBAL DECLARATIONS

   ===================================================================================
 */

/* by making this global, all func's will have access to module options and
 * flags */
struct {
    struct Option *maps;   /* raster DEM(s) to work on */
    struct Option *output; /* output rast3d map */
    struct Option *values; /* specify the value that each layer represents */
    struct Option *colors; /* RRR:GGG:BBB triplets for each layer */
    struct Option
        *error; /* raster map to represent topology errors in input DEMs */
    struct Option *algorithm; /* choose interpolation algorithm */
} parm;
struct {
    struct Flag *countcells; /* calculate 3D cell stats for each layer */
    struct Flag
        *fillnull;     /* fill NULL areas in input DEMs from above or below */
    struct Flag *hull; /* export a 3D hull polygon for every layer */
    struct Flag *grasspts; /* produce a GRASS points vector file */
    struct Flag *points;   /* produce VTK point data instead of cells */
    struct Flag *quiet;    /* no status display on screen */
    struct Flag
        *skip; /* start interpolation even if topology errors were detected */
    struct Flag *vtk;     /* generate a VTK file */
    struct Flag *zadjust; /* adjust z range of current region to fit DEM data */
} flag;

/* ================================================================================

   UTILITY FUNCTIONS

   ===================================================================================
 */

/* returns 1 if the integer is a DEM ID, not a MASKED or NULL value or UNSET,
   0 otherwise */
int isValue(int val)
{
    if (val == UNSET) {
        return (0);
    }
    if (val == NULLVALUE) {
        return (0);
    }
    if (val == MASKVALUE) {
        return (0);
    }
    return (1);
}

int isUnset(int val)
{
    if (val == UNSET) {
        return (1);
    }
    return (0);
}

int isMask(int val)
{
    if (val == MASKVALUE) {
        return (1);
    }
    return (0);
}

int isNull(int val)
{
    if (val == NULLVALUE) {
        return (1);
    }
    return (0);
}

/* returns 1 if the string contains a valid RRR:GGG:BBB color triplet,
   0 otherwise

   IF the string is valid, the R, G and B levels (0-255) will be
   stored at the int pointers (NULL otherwise)
 */

int isRGB(char *triplet, unsigned short int *R, unsigned short int *G,
          unsigned short int *B)
{
    R = NULL;
    G = NULL;
    B = NULL;
    return (0);
}

/* ================================================================================

   Z-RANGE AND TOPOLOGY CHECKING

   ===================================================================================
 */

/* checks if a DEM value intersects a voxel at a given depth */
/* depth goes from 0 (bottom voxel) to slices-1 (top voxel) */
/* returns 1 if DEM intersects, 0 if not */

/* if a DEM intersects the top surface of a voxel, that counts as */
/* a cut, the bottom does not. */
int cut(DCELL val, int depth, struct Cell_head window)
{
    if (DEBUG > 2) {
        fprintf(stdout, "CUT: %.3f at depth %i", (double)val, depth);
    }
    if ((val > (window.bottom + depth * window.tb_res)) &&
        (val < (window.bottom + (depth + 1) * window.tb_res))) {
        if (DEBUG > 2) {
            fprintf(stdout, " = YES\n");
        }
        return (1);
    }
    if (val == window.bottom + (depth + 1) * window.tb_res) {
        if (DEBUG > 1) {
            fprintf(stdout, " = YES\n");
        }
        return (1);
    }
    if (DEBUG > 2) {
        fprintf(stdout, " = NO\n");
    }
    return (0);
}

/* Adjust the ACTIVE region's Z range so that it will be big enough for the
   highest and lowest point in the input DEMs.
   This setting will stay in effect even after r.vol.dem exits!
 */
void adjust_zrange(void)
{
    fprintf(stderr, "DEBUG: Adjustment of Z range not implemented yet.\n");
    return;
}

/* check if DEMs are within z-range of current 3d region */
void check_zrange(int *fd, DCELL **dcell, int nfiles)
{

    struct Cell_head window;

    int i;
    int row, col, nrows, ncols;

    double top, bottom;
    int topDEM, bottomDEM;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    G_get_window(&window);

    if (flag.zadjust->answer) {
        adjust_zrange();
        fprintf(stderr, "DEBUG: Insert a return() statement here.\n");
    }

    if (VERBOSE)
        fprintf(stdout, " Z-range checking, pass 1: \n");

    /* get maximum and minimum elevation from all DEMs */
    row = 0;
    Rast_get_d_row(fd[0], dcell[0], row);
    top = dcell[0][0];
    topDEM = 0;
    for (i = 0; i < nfiles; i++) {
        for (row = 0; row < nrows; row++) {
            Rast_get_d_row(fd[i], dcell[i], row);
            for (col = 0; col < ncols; col++) {
                if (dcell[i][col] > top) {
                    top = dcell[i][col];
                    topDEM = i;
                }
            }
        }

        G_percent(i, (nfiles - 1), 1);
    }
    fflush(stdout);
    if (DEBUG)
        fprintf(stdout, "TOP = %.2f in %s\n", top, parm.maps->answers[topDEM]);

    if (VERBOSE)
        fprintf(stdout, " z-range-checking, pass 2: \n");

    row = 0;
    Rast_get_d_row(fd[0], dcell[0], row);
    bottom = dcell[0][0];
    bottomDEM = 0;
    for (i = 0; i < nfiles; i++) {
        for (row = 0; row < nrows; row++) {
            Rast_get_d_row(fd[i], dcell[i], row);
            for (col = 0; col < ncols; col++) {
                if (dcell[i][col] < bottom) {
                    bottom = dcell[i][col];
                    bottomDEM = i;
                }
            }
        }
        G_percent(i, (nfiles - 1), 1);
    }
    fflush(stdout);
    if (DEBUG)
        fprintf(stdout, "BOTTOM = %.2f in %s\n", bottom,
                parm.maps->answers[bottomDEM]);

    if (top > window.top) {
        G_fatal_error(_("Highest DEM value (%.3f in %s) outside extent of "
                        "current 3d region (top=%.3f) "),
                      top, parm.maps->answers[topDEM], window.top);
    }

    if (bottom < window.bottom) {
        G_fatal_error(_("Lowest DEM value (%.3f in %s) outside extent of "
                        "current 3d region (bottom=%.3f) "),
                      bottom, parm.maps->answers[bottomDEM], window.bottom);
    }

    return;
}

void check_topologies(int *fd, DCELL **dcell, int nfiles)
{

    int i, j;
    struct Cell_head window;
    int row, col, nrows, ncols;
    int nerrors;

    CELL **c_error = NULL;
    int f_error = 0;

    if (VERBOSE)
        fprintf(stdout, " Checking DEM topologies: \n");

    nerrors = 0;

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* does the user want a topology error map? */
    /* if so, we need to alloc mem and create a new CELL map */
    if (parm.error->answer != NULL) {

        /* KILL ME */
        fprintf(stderr,
                "DEBUG: Topology error mapping is an untested feature.\n");
        /* KILL ME */

        c_error = (CELL **)G_malloc(nrows * sizeof(CELL *));
        for (row = 0; row < nrows; row++) {
            c_error[row] = Rast_allocate_c_buf();
        }
        f_error = Rast_open_new(parm.error->answer, CELL_TYPE);
        if (f_error < 0) {
            G_fatal_error("Could not create new CELL raster map for mapping "
                          "topology errors.");
        }
        /* initialise error map */
        for (row = 0; row < nrows; row++) {
            Rast_set_c_null_value(&c_error[row][0], ncols);
        }
    }

    for (row = 0; row < nrows; row++) {
        for (i = 0; i < nfiles; i++) {
            Rast_get_d_row(fd[i], dcell[i], row);
        }
        for (col = 0; col < ncols; col++) {
            for (i = 0; i < nfiles; i++) {
                /* check for undershoots from DEMs above */
                for (j = i + 1; j < nfiles; j++) {
                    if (dcell[j][col] <= dcell[i][col]) {
                        /* UNDERSHOOT */

                        G_warning(
                            _("Z value in %s undershoots Z value in %s at "
                              "cells %i,%i, \ncoordinates: E=%f, N=%f.\n"),
                            parm.maps->answers[j], parm.maps->answers[i], col,
                            row, Rast_col_to_easting((double)col, &window),
                            Rast_row_to_northing((double)row, &window));
                        nerrors++;
                        if (parm.error->answer != NULL) {
                            c_error[row][col] = j;
                        }
                    }
                }
                /* check for overshoots from DEMs below */
                for (j = i - 1; j >= 0; j--) {
                    if (dcell[j][col] >= dcell[i][col]) {
                        /* OVERSHOOT! */
                        G_warning(
                            _("Z value in %s overshoots Z value in %s at cells "
                              "%i,%i, \ncoordinates: E=%f, N=%f.\n"),
                            parm.maps->answers[j], parm.maps->answers[i], col,
                            row, Rast_col_to_easting((double)col, &window),
                            Rast_row_to_northing((double)row, &window));

                        nerrors++;
                        if (parm.error->answer != NULL) {
                            c_error[row][col] = j;
                        }
                    }
                }
            }
        }

        if (VERBOSE)
            G_percent(row, (nrows - 1), 2);
    }
    fflush(stdout);
    if (parm.error->answer != NULL) {
        for (row = 0; row < nrows; row++) {
            Rast_put_c_row(f_error, c_error[row]);
        }
        Rast_close(f_error);
    }
    if (nerrors > 0) {
        G_fatal_error(_("Found %i errors in DEM topology! Aborting."), nerrors);
    }

    return;
}

/* ================================================================================

   CORE INTERPOLATION ROUTINES

   ===================================================================================
 */

void interpolate_up(int *flist, DCELL **dcell, int col, int nfiles)
{

    struct Cell_head window;
    int fillval;
    double level;
    double stopat;
    int i, j, k;
    int DEMAbove;
    int highestDEMValue;

    Rast_get_window(&window);

    /* DEMs must be provided in this order: bottom,...,top ... */
    for (i = 0; i < NSLICES; i++) {
        /* ... the interpolated column, however, has its lowest value */
        /* at the bottom (last element of array), so that order needs to be
         * switched! */
        flist[(NSLICES - 1) - i] =
            NULLVALUE; /* NULLVALUE = no DEM cuts at this point */
        for (j = 0; j < nfiles; j++) {
            if (!Rast_is_d_null_value(
                    &dcell[j][col])) { /* SKIP NULL VALUED CELLS */
                if (cut(dcell[j][col], i, window)) {
                    flist[(NSLICES - 1) - i] = j;
                }
            }
        }
    }

    /* interpolate one column by 'flood filling' DEM values up from the bottom
     */
    fillval = flist[0];

    /* first we need to know where to stop the interpolation ! */

    /* find the highest DEM that has a data value at this point! */
    highestDEMValue = -1;
    i = (nfiles - 1);
    while ((i >= 0) && (highestDEMValue == -1)) {
        if (!Rast_is_d_null_value(&dcell[i][col])) {
            highestDEMValue = i;
        }
        i--;
    }
    i++;

    if (highestDEMValue == -1) {
        /* there is no DEM with any data at this point ! */
        stopat =
            window.bottom -
            1; /* this will prevent any interpolation from happening here ! */
    }
    else {
        /* we found a DEM with a value ... */
        if (highestDEMValue == (nfiles - 1)) {
            /* ... and it is the top one, so we just set this as interpolation
             * stop */
            stopat = dcell[(nfiles - 1)][col];
        }
        else {
            /* ... but it is not the top one, so we need to decide what to do */
            if (flag.fillnull->answer) {
                /* this flag forces us to keep filling (all the way up to the
                 * top of the current 3D region) */
                stopat = window.top;
            }
            else {
                /* we will only fill up to the highest DEM with a value */
                /* but we make sure to fill up at least one slice ! */
                stopat = dcell[highestDEMValue][col] +
                         (window.tb_res + (window.tb_res * 0.5));
            }
        }
    }

    if (DEBUG > 1) {
        fprintf(stderr, "  STOPAT = %.2f\n", stopat);
    }

    for (i = (NSLICES - 1); i >= 0; i--) {
        if (isValue(flist[i])) {
            /* check, if there is another DEM cutting point above this slice */
            /* if not, only keep filling, if flag -f has been set ! */
            if (flag.fillnull->answer) {
                fillval = flist[i];
            }
            else {
                DEMAbove = 0;
                for (k = i; k >= 0; k--) {
                    if (isValue(flist[k])) {
                        DEMAbove = 1;
                    }
                }
                if (DEMAbove) {
                    fillval = flist[i];
                }
            }
        }
        else {
            /* check if we are still below top level */
            level = window.bottom + (((NSLICES - 1) - i) * window.tb_res);
            if (level < stopat) {
                flist[i] = fillval;
            }
            else {
                flist[i] = NULLVALUE;
            }
        }
    }

    return;
}

void interpolate_down(int *flist, DCELL **dcell, int col, int nfiles)
{

    struct Cell_head window;
    int fillval;
    double level;
    double stopat = 0.0;
    int i, j, k;
    int DEMBelow;
    int lowestDEMValue;

    Rast_get_window(&window);

    /* DEMs must be provided in this order: bottom,...,top ... */
    for (i = 0; i < NSLICES; i++) {
        /* ... the interpolated column, however, has its lowest value */
        /* at the bottom, so that order needs to be switched! */
        flist[(NSLICES - 1) - i] =
            NULLVALUE; /* NULLVALUE = no DEM cuts at this point */
        for (j = 0; j < nfiles; j++) {
            if (!Rast_is_d_null_value(
                    &dcell[j][col])) { /* SKIP NULL VALUED CELLS */
                if (cut(dcell[j][col], i, window)) {
                    flist[(NSLICES - 1) - i] = j;
                }
            }
        }
    }

    /* interpolate one column by 'flood filling' DEM values down from the top */
    fillval = flist[0];

    /* first we need to know where to stop the interpolation ! */

    /* find the lowest DEM that has a data value at this point! */
    lowestDEMValue = -1;
    i = 0;
    while ((i < nfiles) && (lowestDEMValue == -1)) {
        if (!Rast_is_d_null_value(&dcell[i][col])) {
            lowestDEMValue = i;
        }
        i++;
    }
    i--;

    if (lowestDEMValue == -1) {
        /* there is no DEM with any data at this point ! */
        stopat =
            window.top +
            1; /* this will prevent any interpolation from happening here ! */
    }
    else {
        /* we found a DEM with a value ... */
        if (lowestDEMValue == 0) {
            /* ... and it is the bottom one, so we just set this as
             * interpolation stop */
            stopat = dcell[0][col];
        }
        else {
            /* ... but it is not the bottom one, so we need to decide what to do
             */
            if (flag.fillnull->answer) {
                /* this flag forces us to keep filling (all the way down to the
                 * bottom of the current 3D region) */
                stopat = window.bottom;
            }
            else {
                /* we will only fill down to the lowest DEM with a value */
                /* but we make sure to fill down at least one slice ! */
                stopat = dcell[lowestDEMValue][col] -
                         (window.tb_res + (window.tb_res * 0.5));
            }
        }
    }

    if (DEBUG > 1) {
        fprintf(stderr, "  STOPAT = %.2f\n", stopat);
    }

    for (i = 1; i < NSLICES; i++) {
        if (isValue(flist[i])) {
            /* check, if there is another DEM cutting point below this slice */
            /* if not, only keep filling, if flag -f has been set ! */
            if (flag.fillnull->answer) {
                fillval = flist[i];
            }
            else {
                DEMBelow = 0;
                for (k = i; k <= NSLICES; k++) {
                    if (isValue(flist[k])) {
                        DEMBelow = 1;
                    }
                }
                if (DEMBelow) {
                    fillval = flist[i];
                }
            }
        }
        else {
            /* check if we are still above bottom level */
            level = window.bottom + (((NSLICES - 1) - i) * window.tb_res);
            if (level >= stopat) {
                flist[i] = fillval;
            }
            else {
                flist[i] = NULLVALUE;
            }
        }
    }

    return;
}

void interpolate(int *fd, DCELL **dcell, int nfiles, int nvalues,
                 double ***ascii)
{

    struct Cell_head window;

    int *flist;

    int i;
    int row, col, nrows, ncols;

    Rast_get_window(&window);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    flist = G_malloc(sizeof(int) * NSLICES);

    if (VERBOSE)
        fprintf(stdout, "\nInterpolating: \n");

    for (row = 0; row < nrows; row++) {
        /* read one row from all layers */
        for (i = 0; i < nfiles; i++) {
            Rast_get_d_row(fd[i], dcell[i], row);
        }
        for (col = 0; col < ncols; col++) {

            if (!strcmp(parm.algorithm->answer, "up")) {
                interpolate_up(flist, dcell, col, nfiles);
            }
            if (!strcmp(parm.algorithm->answer, "down")) {
                interpolate_down(flist, dcell, col, nfiles);
            }

            for (i = 1; i < NSLICES; i++) {
                if (isValue(flist[i])) {
                    if (nvalues == 0) {
                        /* either enumerate layers from 0 .. n */
                        ascii[i][row][col] = (double)(flist[i]);
                    }
                    else {
                        /* OR write user-provided values for layers? */
                        ascii[i][row][col] =
                            atof(parm.values->answers[flist[i]]);
                    }
                }
                else {
                    /* write a NULL valued voxel */
                    ascii[i][row][col] = DNULLVALUE;
                }
            }
            if (DEBUG > 1) {
                fprintf(stdout, "col %i (", col);
                for (i = 0; i < NSLICES; i++) {
                    if (isValue(flist[i])) {
                        fprintf(stdout, "%i ", flist[i]);
                    }
                    if (isNull(flist[i])) {
                        fprintf(stdout, "N ");
                    }
                    if (isMask(flist[i])) {
                        fprintf(stdout, "M ");
                    }
                }
                fprintf(stdout, ")\n");
            }
        }

        if (VERBOSE) {
            G_percent(row, nrows - 1, 2);
        }
        if (DEBUG > 1)
            fprintf(stdout, "row=%i\n", row);
    }
    fprintf(stdout, "\n");
    fflush(stdout);
}

/* ================================================================================

   DATA OUTPUT AND EXPORT

   ===================================================================================
 */

void count_3d_cells(double ***ascii, int nfiles, int nvalues)
{
    struct Cell_head window;
    int a, i, j, k;
    unsigned long int sum;
    int nrows, ncols;

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    fprintf(stdout, "\nCell counts: \n");

    for (a = 0; a < nfiles; a++) {
        sum = 0;
        for (i = 0; i < NSLICES; i++) {
            for (j = 0; j < nrows; j++) {
                for (k = 0; k < ncols; k++) {
                    if (nvalues == 0) {
                        if (a == (int)ascii[i][j][k]) {
                            sum++;
                        }
                    }
                    else {
                        if (atof(parm.values->answers[a]) == ascii[i][j][k]) {
                            sum++;
                        }
                    }
                }
            }
        }
        if (nvalues == 0) {
            fprintf(stdout, "  Layer %i has %li 3D cells\n", a, sum);
        }
        else {
            fprintf(stdout, "  Layer %i (label=%f) has %li 3D cells\n", a,
                    atof(parm.values->answers[a]), sum);
        }
    }
}

void output_ascii(double ***ascii)
{

    struct Cell_head window;
    int i, j, k;
    int nrows, ncols;
    FILE *tmpfile;

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* open a tmp file for writing ascii output data */
    tmpfile = fopen(TMPFILE, "w+");
    if (tmpfile == NULL) {
        G_fatal_error(
            _("Could not create temporary file for writing ASCII output (%s)"),
            TMPFILE);
    }
    /* write output to ASCII file */
    fprintf(tmpfile, "north: %f\n", window.north);
    fprintf(tmpfile, "south: %f\n", window.south);
    fprintf(tmpfile, "east: %f\n", window.east);
    fprintf(tmpfile, "west: %f\n", window.west);
    fprintf(tmpfile, "top: %f\n", window.top);
    fprintf(tmpfile, "bottom: %f\n", window.bottom);
    fprintf(tmpfile, "rows: %i\n", nrows);
    fprintf(tmpfile, "cols: %i\n", ncols);
    fprintf(tmpfile, "levels:%i\n", NSLICES);
    for (i = 0; i < NSLICES; i++) {
        for (j = 0; j < nrows; j++) {
            for (k = 0; k < ncols; k++) {
                /* below is the correct data order for Paraview and GRASS rast3d
                 * ASCII files ! */
                fprintf(tmpfile, "%f ",
                        ascii[(NSLICES - 1) - i][(nrows - 1) - j][k]);
            }
            fprintf(tmpfile, "\n");
        }
    }
    fclose(tmpfile);
}

void output_ascii_points(double ***ascii)
{

    struct Cell_head window;
    int i, j, k;
    int nrows, ncols;
    FILE *tmpfile;
    char tmp[2048];
    double x, y, z, w;
    int error;

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* open a tmp file for writing ascii output data */
    sprintf(tmp, "%s.points.txt", parm.output->answer);
    tmpfile = fopen(tmp, "w+");
    if (tmpfile == NULL) {
        G_fatal_error(
            _("Could not create temporary file for writing ASCII output (%s)"),
            tmp);
    }

    fprintf(tmpfile, "# Simple 3D vector points file.\n");
    fprintf(tmpfile, "# This file was created by %s version %.2f \n", PROGNAME,
            PROGVERSION);
    fprintf(tmpfile, "# Tab delimited point data: x, y, z, value. \n");
    fprintf(tmpfile, "# Import into GRASS GIS using this command:\n");
    fprintf(tmpfile,
            "#   v.in.ascii in=%s.points.txt out=%s -z x=1 y=2 z=3 cat=0 "
            "columns='x double, y double, z double, w double' fs=tab\n",
            parm.output->answer, parm.output->answer);

    /* write output to ASCII file */
    for (i = 0; i < NSLICES; i++) {
        for (j = 0; j < nrows; j++) {
            for (k = 0; k < ncols; k++) {
                /* coordinates for points will be centers of 3D raster cells !
                 */
                /* only produce points at non-NULL locations ! */
                w = ascii[i][(nrows - 1) - j][k];
                if (w != DNULLVALUE) {
                    x = window.west + (window.ew_res * k) +
                        (window.ew_res * 0.5);
                    y = window.south + (window.ns_res * j) +
                        (window.ns_res * 0.5);
                    z = window.top - (window.tb_res * i) -
                        (window.tb_res * 0.5);
                    fprintf(tmpfile, "%.6f\t%.6f\t%.6f\t%.6f\n", x, y, z, w);
                }
            }
        }
    }

    if (VERBOSE) {
        fprintf(stdout, "\nRunning v.in.ascii to create 3D points map: \n");
    }

    /* TODO: KILL THIS AND REPLACE WITH NEAT --o OPTION CHECK */
    /* remove output map, if exists */
    sprintf(tmp, "g.remove -f type=vect name=%s", parm.output->answer);
    error = system(tmp);
    if (error != EXIT_SUCCESS) {
        G_fatal_error("Error running command: %s", tmp);
    }

    /* call v.in.ascii to make GRASS native vector map */
    sprintf(tmp,
            "v.in.ascii in=%s.points.txt out=%s -z x=1 y=2 z=3 cat=0 "
            "columns='x double, y double, z double, w double' fs=tab\n",
            parm.output->answer, parm.output->answer);

    error = system(tmp);
    if (error != EXIT_SUCCESS) {
        G_fatal_error("Error running command: %s", tmp);
    }

    if (VERBOSE)
        fprintf(stdout, " DONE \n");

    fclose(tmpfile);
}

void output_ascii_hulls(double ***ascii, int nvalues, int nfiles)
{

    struct Cell_head window;
    int i, j, k, l;
    double label;
    int num_points;
    int nrows, ncols;
    FILE *tmpfile;
    char tmp[2048];
    double w;
    long int *px;
    long int *py;
    long int *pz;
    int curPoint;

    int error;

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* MAIN LOOP START */
    /* do this vor every layer, i.e. all 3D cells with the same label */
    for (l = 0; l < nfiles; l++) {

        /* open tmp file for writing ascii output data */
        sprintf(tmp, "%s.hull.%i.txt", parm.output->answer, l);
        tmpfile = fopen(tmp, "w+");
        if (tmpfile == NULL) {
            G_fatal_error(_("Could not create temporary file for writing ASCII "
                            "output (%s)"),
                          tmp);
        }

        if (nvalues == 0) {
            /* either enumerate layers from 0 .. (nfiles-1) */
            label = (double)l;
        }
        else {
            /* OR use user-provided values for layers? */
            label = atof(parm.values->answers[l]);
        }

        num_points = 0;
        /* create arrays large enough to store all points of the current layer
         */
        for (i = 0; i < NSLICES; i++) {
            for (j = 0; j < nrows; j++) {
                for (k = 0; k < ncols; k++) {
                    w = ascii[i][j][k];
                    if (w == label) {
                        num_points++;
                    }
                }
            }
        }

        if (DEBUG) {
            fprintf(stderr, "EXPORT HULLS: %i points with label %.6f\n",
                    num_points, label);
        }

        px = (long int *)malloc(num_points * sizeof(long int));
        py = (long int *)malloc(num_points * sizeof(long int));
        pz = (long int *)malloc(num_points * sizeof(long int));

        /* pick points with current label from ASCII array */

        curPoint = 0;
        for (i = 0; i < NSLICES; i++) {
            for (j = 0; j < nrows; j++) {
                for (k = 0; k < ncols; k++) {
                    /* coordinates for points will be centers of 3D raster cells
                     * ! */
                    /* only produce points at non-NULL locations ! */
                    /* we have to store them as int values for performance
                     * reasons, so we will multiply by PRECISION */
                    /* PRECISION = 1000 = 10^3 = 3 decimal places precision! */
                    w = ascii[i][(nrows - 1) - j][k];
                    if (w == label) {
                        px[curPoint] =
                            ((long int)window.west + (window.ew_res * k) +
                             (window.ew_res * 0.5)) *
                            (PRECISION);
                        py[curPoint] =
                            ((long int)window.south + (window.ns_res * j) +
                             (window.ns_res * 0.5)) *
                            (PRECISION);
                        pz[curPoint] =
                            ((long int)window.top - (window.tb_res * i) -
                             (window.tb_res * 0.5)) *
                            (PRECISION);
                        curPoint++;
                    }
                }
            }
        }

        if (VERBOSE) {
            fprintf(stdout, "\nExporting 3D convex hull for layer %i: \n", l);
        }
        /* make 3D hull */
        error = make3DHull(px, py, pz, num_points, tmpfile);

        if (error < 0) {

            fprintf(stdout,
                    "DEBUG: Simple planar hulls not implemented yet.\n");
            fprintf(stdout, "DEBUG: This layer will not be exported.\n");

            /* all points in the same voxel plane. Let's output a very simple
             * hull with 8 vertices */

            /* ONCE THIS IS IMPLEMENTED: call v.in.ascii for these hulls, too!
             */

            if (l == 0) {
                /* this is the bottom DEM: we will extend it half a slice
                 * (tbres) down */
                fprintf(tmpfile,
                        "DEBUG: Simple planar hulls not implemented yet.\n");
                fprintf(tmpfile, "DEBUG: This layer was not exported.\n");
            }
            else {
                if (l == (nfiles - 1)) {
                    /* this is the top DEM: we will extend it half a slice
                     * (tbres) up */
                    fprintf(
                        tmpfile,
                        "DEBUG: Simple planar hulls not implemented yet.\n");
                    fprintf(stdout, "DEBUG: This layer was not exported.\n");
                }
                else {
                    /* this DEM is somewhare in between, its vector
                     * representation will be planar! */
                    fprintf(
                        tmpfile,
                        "DEBUG: Simple planar hulls not implemented yet.\n");
                    fprintf(stdout, "DEBUG: This layer was not exported.\n");
                }
            }
        }

        /* free memory for points */
        free(px);
        free(py);
        free(pz);

        fclose(tmpfile);

        /* call v.in.ascii to create a native GRASS vector map */
        /* DEBUG: remove once planar hulls are implemented */
        if (error > -1) {
            if (VERBOSE) {
                fprintf(stdout,
                        "\nRunning v.in.ascii to create 3D points map: \n");
            }
            sprintf(
                tmp,
                "v.in.ascii -z in=%s.hull.%i.txt out=%s_hull_%i form=standard",
                parm.output->answer, l, parm.output->answer, l);

            error = system(tmp);
            if (error != EXIT_SUCCESS) {
                G_fatal_error("Error running command: %s", tmp);
            }

            if (VERBOSE)
                fprintf(stdout, " DONE \n");
        }
    }
    /* MAIN LOOP END */
}

void output_vtk()
{

    char sys[2048];
    int error;

    if (flag.vtk->answer) {

        /* write a VTK file for visualisation in paraview etc. */
        if (VERBOSE)
            fprintf(stdout, "\nCreating VTK file (%s.vtk): \n",
                    parm.output->answer);

        if (flag.points->answer) {
            sprintf(sys, "r3.out.vtk -p in=%s out=%s.vtk null=%f dp=3",
                    parm.output->answer, parm.output->answer, DNULLVALUE);
        }
        else {
            sprintf(sys, "r3.out.vtk in=%s out=%s.vtk null=%f dp=3",
                    parm.output->answer, parm.output->answer, DNULLVALUE);
        }
        if (DEBUG > 0) {
            fprintf(stdout, "%s\n", sys);
        }
        error = system(sys);
        if (error != 0) {
            G_fatal_error("Error running command: %s", sys);
        }
    }
}

/* ================================================================================

   MAIN

   ===================================================================================
 */

int main(int argc, char *argv[])
{
    struct GModule *module;

    struct Cell_head window;

    int i, j, k;
    int nrows, ncols;

    int *fd;
    int nfiles, nvalues, ncolors;
    double dslices;
    char *name, *mapset;
    DCELL **dcell;

    double ***ascii; /* 3D array that holds values to print into ASCII file */

    unsigned short int *R;
    unsigned short int *G;
    unsigned short int *B;

    char sys[2048];

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("volume"));
    G_add_keyword(_("conversion"));
    module->description =
        "Creates a 3D raster model (voxels) from a series of raster DEMs";

    /* DEFINE OPTIONS AND FLAGS */
    /* input raster map */
    parm.maps = G_define_standard_option(G_OPT_R_MAPS);
    parm.maps->key = "input";
    parm.maps->description =
        "Input DEMs (at least 2) in raster format. Bottom DEM first";
    parm.maps->multiple = YES;

    /* Output map name */
    parm.output = G_define_standard_option(G_OPT_R3_OUTPUT);

    /* optional: specify a value for each layer */
    parm.values = G_define_option();
    parm.values->key = "labels";
    parm.values->type = TYPE_DOUBLE;
    parm.values->required = NO;
    parm.values->description = "List of label values, one for each 3D layer";

    /* optional: specify an RRR:GGG:BBB color triplet for each layer */
    parm.colors = G_define_option();
    parm.colors->key = "colors";
    parm.colors->type = TYPE_STRING;
    parm.colors->required = NO;
    parm.colors->description =
        "List of RRR:GGG:BBB color triplets, one for each layer";

    /* optional: Raster map to represent topology errors in input DEMs */
    parm.error = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.error->key = "errormap";
    parm.error->required = NO;
    parm.error->description =
        "Raster map to represent topology errors in input DEMs";

    /* algorithm to use for flood filling */
    parm.algorithm = G_define_option();
    parm.algorithm->key = "algorithm";
    parm.algorithm->type = TYPE_STRING;
    parm.algorithm->required = NO;
    parm.algorithm->options = "up,down";
    parm.algorithm->answer = "up";
    parm.algorithm->description = "3D flood fill algorithm to use";

    /* 3D cell stats? */
    flag.countcells = G_define_flag();
    flag.countcells->key = 'c';
    flag.countcells->description = "Calculate 3D cell counts for each layer.";

    /* VTK point data output ? */
    flag.fillnull = G_define_flag();
    flag.fillnull->key = 'f';
    flag.fillnull->description = "Fill through NULL value areas in DEMs";

    /* export a 3D hull polygon for every layer ? */

    /** Suffers from severe memory leak! MN 4/2012
        flag.hull = G_define_flag();
        flag.hull->key = 'h';
        flag.hull->description = "Export convex hull polygons for layers";
    **/

    /* GRASS ASCII vector point data output ? */
    flag.grasspts = G_define_flag();
    flag.grasspts->key = 'g';
    flag.grasspts->description = "Export voxel model as vector points";

    /* VTK point data output ? */
    flag.points = G_define_flag();
    flag.points->key = 'p';
    flag.points->description = "Export VTK point data instead of cell data";

    /* quiet operation? */
    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = "Disable on-screen progress display";

    /* skip DEM topology checks? */
    flag.skip = G_define_flag();
    flag.skip->key = 's';
    flag.skip->description = "Skip topology error checking";

    /* generate a VTK file? */
    flag.vtk = G_define_flag();
    flag.vtk->key = 'v';
    flag.vtk->description =
        "Generate a .vtk file for visualisation with e.g. paraview";

    /* adjust Z-region settings to fit DEM values? */
    flag.zadjust = G_define_flag();
    flag.zadjust->key = 'z';
    flag.zadjust->description = "Fit active region's Z range to input DEMs";

    int error;

    /* INIT GLOBAL VARIABLES */
    VERBOSE = 1;
    NSLICES = 0;
    PRECISION = 1000;

    /* setup some basic GIS stuff */
    G_gisinit(argv[0]);
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (flag.quiet->answer) {
        VERBOSE = 0;
    }

    Rast_get_window(&window);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /*                                                      */
    /*      STEP 1: VALIDATE input data and topology        */
    /*                                                      */

    fprintf(stdout, "Validating data: \n");

    /* check if input DEMs are available */
    /* allocate all necessary handles */
    for (nfiles = 0; parm.maps->answers[nfiles]; nfiles++)
        ;

    if (DEBUG)
        fprintf(stdout, "nfiles = %i\n", nfiles);

    fd = (int *)G_malloc(nfiles * sizeof(int));
    dcell = (DCELL **)G_malloc(nfiles * sizeof(DCELL *));

    if (nfiles < 2) {
        G_fatal_error("Need at least two raster maps!");
    }

    for (i = 0; i < nfiles; i++) {
        dcell[i] = Rast_allocate_d_buf();
        name = parm.maps->answers[i];
        mapset = G_find_raster2(name, "");
        if (!mapset)
            G_fatal_error(_("%s - raster map not found"), name);
        fd[i] = Rast_open_old(name, mapset);
        if (fd[i] < 0)
            G_fatal_error(_("%s - can't open raster map"), name);
    }

    nvalues = 0;
    ncolors = 0;
    /* if values and/or colors have been specified for the model: check these
     * parameters */
    if (parm.values->answers != NULL)
        for (nvalues = 0; parm.values->answers[nvalues]; nvalues++)
            ;
    if (nvalues > 0) {
        if (nvalues != nfiles) {
            G_fatal_error(
                _("Number of values (%i) does not match number of DEMs (%i)!"),
                nvalues, nfiles);
        }
    }
    if (parm.colors->answers != NULL) {
        for (ncolors = 0; parm.colors->answers[ncolors]; ncolors++)
            ;
        /* KILL ME */
        fprintf(stdout, "DEBUG: custom RGB colouring not implemented yet.\n");
        /* KILL ME */
    }
    if (ncolors > 0) {
        R = G_malloc(ncolors * sizeof(unsigned short int));
        G = G_malloc(ncolors * sizeof(unsigned short int));
        B = G_malloc(ncolors * sizeof(unsigned short int));
        if (ncolors != nfiles) {
            G_fatal_error(_("Number of RGB triplets (%i) does not match number "
                            "of DEMs (%i)!"),
                          ncolors, nfiles);
        }
        for (i = 0; i < ncolors; i++) {
            if (!isRGB(parm.colors->answers[i], &R[i], &G[i], &B[i])) {
                G_fatal_error(_("%s is not a valid RRR:GGG:BBB code!"),
                              parm.colors->answers[i]);
            }
        }
    }

    check_zrange(fd, dcell, nfiles);

    if (!flag.skip->answer) {
        check_topologies(fd, dcell, nfiles);
    }

    /* let's see how many slices we will make */
    dslices = ((window.top - window.bottom) / window.tb_res);
    NSLICES = (int)rint(dslices);
    if (NSLICES < 1) {
        G_fatal_error("This would produce < 1 slice. Adjust active 3d region "
                      "resolution.");
    }
    if (DEBUG) {
        fprintf(stdout, "%i DEMS, NSLICES = %i (%f)\n", nfiles, NSLICES,
                dslices);
        fflush(stdout);
    }

    /*                                                      */
    /*      STEP 2: INTERPOLATE volume from DEMs            */
    /*                                                      */

    /* allocate array for storing voxel data and initialise it with DNULLVALUE
     */
    ascii = (double ***)G_malloc(NSLICES * sizeof(double **));
    for (i = 0; i < NSLICES; i++) {
        ascii[i] = (double **)G_malloc(nrows * sizeof(double *));
        for (j = 0; j < nrows; j++) {
            ascii[i][j] = G_malloc(ncols * sizeof(double));
            for (k = 0; k < ncols; k++) {
                ascii[i][j][k] = DNULLVALUE;
            }
        }
    }
    interpolate(fd, dcell, nfiles, nvalues, ascii);

    /*                                                      */
    /*      STEP 3: OUTPUT volume data                      */
    /*                                                      */

    /* TEMP SECTION */
    /* this will only stay in here temporarily until this
       program will be able to write voxel maps directly !!! */
    output_ascii(ascii);
    /* now call r3.in.ascii to write a voxel model for us */

    if (VERBOSE)
        fprintf(stdout, "Running r3.in.ascii to create voxel model: \n");

    sprintf(sys, "r3.in.ascii in=%s out=%s nv=%f", TMPFILE, parm.output->answer,
            DNULLVALUE);
    if (DEBUG > 0) {
        fprintf(stdout, "%s\n", sys);
    }
    error = system(sys);
    if (error != EXIT_SUCCESS) {
        G_fatal_error("Error running command: %s", sys);
    }
    if (VERBOSE)
        fprintf(stdout, " DONE \n");

    /* END (TEMP SECTION) */

    /* VTK output */
    if (flag.vtk->answer) {
        output_vtk();
    }

    /* ASCII vector points output */
    if (flag.grasspts->answer) {
        output_ascii_points(ascii);
    }

    /* ASCII convex hulls ouput */
    if (flag.hull->answer) {
        output_ascii_hulls(ascii, nvalues, nfiles);
    }

    /* show cell count stats? */
    if (flag.countcells->answer) {
        count_3d_cells(ascii, nfiles, nvalues);
    }

    fprintf(stdout, "\nJOB DONE.\n");
    fflush(stdout);

    return (EXIT_SUCCESS);
}
