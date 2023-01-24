/***********************************************************************/
/*
   azimuth.c

   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"

#define AZ_PI     3.14159265358979323846
#define AZ_RAD180 3.14159265358979323846
#define AZ_RAD360 6.2831853071798

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void calc_azimuth(int row, int col, int *ax, int *qd, double *smallest_azimuth,
                  double *centre_azimuth, double *largest_azimuth,
                  double *distance)
{
    double alpha;
    double row_diff, col_diff, x, y;
    double x_adjust = 0.0, y_adjust = 0.0;
    int row_dir, col_dir;
    int quad, axis;

    /* Dummy values so we know whether various azimuths have been calculated */

    axis = 0;
    quad = 0;
    *smallest_azimuth = 999.0;
    *centre_azimuth = 999.0;
    *largest_azimuth = 999.0;

    /* Get the two sides of the triangle */

    col_diff = (double)(col - viewpt_col);
    row_diff = (double)(row - viewpt_row);

    /* Work out which quadrant the cell falls in

       ---------
       | 4 | 1 |
       ---------
       | 3 | 2 |
       ---------

       or which axis is falls on

       1
       ---------
       |   |   |
       4 ----5---- 2
       |   |   |
       ---------
       3
     */

    col_dir = 0; /* cell same longitude as viewpt */
    row_dir = 0; /* cell same latitude as viewpt */
    if (col_diff < 0.0)
        col_dir = -1; /* cell to west of viewpt */
    else if (col_diff > 0.0)
        col_dir = 1; /* cell to east of viewpt */
    if (row_diff < 0.0)
        row_dir = -1; /* cell to north of viewpt */
    else if (row_diff > 0.0)
        row_dir = 1; /* cell to south of viewpt */

    switch (col_dir) {
    case (-1):
        switch (row_dir) {
        case (-1):
            quad = 4;
            break;
        case (0):
            axis = 4;
            break;
        case (1):
            quad = 3;
            break;
        };
        break;
    case (0):
        switch (row_dir) {
        case (-1):
            axis = 1;
            break;
        case (0):
            axis = 5;
            break;
        case (1):
            axis = 3;
            break;
        };
        break;
    case (1):
        switch (row_dir) {
        case (-1):
            quad = 1;
            break;
        case (0):
            axis = 2;
            break;
        case (1):
            quad = 2;
            break;
        };
        break;
    };

    *ax = axis;
    *qd = quad;

    /* Calculate centre azimuths and centre-to-centre distances
       for cells which fall on axes */

    if (axis) {
        switch (axis) {
        case (1):
            *centre_azimuth = 0.0;
            *distance = fabs(row_diff) * window.ns_res;
            break;
        case (2):
            *centre_azimuth = 90.0;
            *distance = fabs(col_diff) * window.ew_res;
            break;
        case (3):
            *centre_azimuth = 180.0;
            *distance = fabs(row_diff) * window.ns_res;
            break;
        case (4):
            *centre_azimuth = 270.0;
            *distance = fabs(col_diff) * window.ew_res;
            break;
        case (5):
            *centre_azimuth = 0.0;
            *distance = 0.0;
            break;
        };
    }
    else
    /* Calculate centre azimuths for cells which do not fall on axes */
    {
        /* Calc orthogonal distances from centre to centre  */

        x = (fabs(col_diff) * window.ew_res);
        y = (fabs(row_diff) * window.ns_res);
        *distance = sqrt((x * x) + (y * y));

        /* Now calculate alpha */

        alpha = atan(x / y);

        /* Convert alpha in radians to centre_azimuth in degrees */

        switch (quad) {
        case (1):
            *centre_azimuth = alpha * 180.0 / AZ_PI;
            break;
        case (2):
            *centre_azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
            break;
        case (3):
            *centre_azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
            break;
        case (4):
            *centre_azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
            break;
        }
    }

    /* Calculate smallest azimuths for cells which fall on axes */

    if (axis) {
        switch (axis) {
        case (1):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (2):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        case (3):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (4):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        };

        /* If cell is not viewpoint */

        if (axis != 5) {
            x = (fabs(col_diff) * window.ew_res) + x_adjust;
            y = (fabs(row_diff) * window.ns_res) + y_adjust;

            /* Now calculate alpha */

            alpha = atan(x / y);

            /* Convert alpha in radians to smallest_azimuth in degrees
               Recall here that corner with smallest azimuth will be
               in quadrant preceeding axis in which cell's centre lies */

            switch (axis) {
            case (1):
                *smallest_azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
                break;
            case (2):
                *smallest_azimuth = alpha * 180.0 / AZ_PI;
                break;
            case (3):
                *smallest_azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
                break;
            case (4):
                *smallest_azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
                break;
            };
        }
        else
        /* Cell is viewpoint, so we will set smallest and largest
           to 0.0 and 360.0 respectively */
        {
            *smallest_azimuth = 0.0;
        }
    }
    else
    /* Calculate smallest azimuths for cells which do not fall on axes */
    {
        /* Calc orthogonal distances (viewpt centre to cell corner).
           Adjustments must be made according to which corner will have
           minimum azimuth */

        switch (quad) {
        case (1):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        case (2):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (3):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        case (4):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        };

        x = (fabs(col_diff) * window.ew_res) + x_adjust;
        y = (fabs(row_diff) * window.ns_res) + y_adjust;

        /* Now calculate alpha */

        alpha = atan(x / y);

        /* Convert alpha in radians to smallest_azimuth in degrees */

        switch (quad) {
        case (1):
            *smallest_azimuth = alpha * 180.0 / AZ_PI;
            break;
        case (2):
            *smallest_azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
            break;
        case (3):
            *smallest_azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
            break;
        case (4):
            *smallest_azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
            break;
        }
    }

    /* Calculate largest azimuths for cells which fall on axes */

    if (axis) {
        switch (axis) {
        case (1):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (2):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        case (3):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (4):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        };

        /* If cell is not viewpoint */

        if (axis != 5) {
            x = (fabs(col_diff) * window.ew_res) + x_adjust;
            y = (fabs(row_diff) * window.ns_res) + y_adjust;

            /* Now calculate alpha */

            alpha = atan(x / y);

            /* Convert alpha in radians to smallest_azimuth in degrees
               Recall here that corner with largest azimuth will be
               in quadrant following axis on which cell's centre lies */

            switch (axis) {
            case (1):
                *largest_azimuth = alpha * 180.0 / AZ_PI;
                break;
            case (2):
                *largest_azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
                break;
            case (3):
                *largest_azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
                break;
            case (4):
                *largest_azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
                break;
            };
        }
        else
        /* Cell is viewpoint, so we will set smallest and largest
           to 0.0 and 360.0 respectively */
        {
            *largest_azimuth = 360.0;
        }
    }
    else
    /* Calculate largest azimuths for cells which do not fall on axes */
    {
        /* Calc orthogonal distances (viewpt centre to cell corner).
           Adjustments must be made according to which corner will have
           maximum azimuth */

        switch (quad) {
        case (1):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (2):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        case (3):
            x_adjust = 0.5 * window.ew_res;
            y_adjust = 0.0 - 0.5 * window.ns_res;
            break;
        case (4):
            x_adjust = 0.0 - 0.5 * window.ew_res;
            y_adjust = 0.5 * window.ns_res;
            break;
        };

        x = (fabs(col_diff) * window.ew_res) + x_adjust;
        y = (fabs(row_diff) * window.ns_res) + y_adjust;

        /* Now calculate alpha */

        alpha = atan(x / y);

        /* Convert alpha in radians to largest_azimuth in degrees */

        switch (quad) {
        case (1):
            *largest_azimuth = alpha * 180.0 / AZ_PI;
            break;
        case (2):
            *largest_azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
            break;
        case (3):
            *largest_azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
            break;
        case (4):
            *largest_azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
            break;
        }
    }
}
