/***********************************************************************/
/*
   azimuth.c

   Revised by Mark Lake, 30/10/2020, for r.bearing.distance in GRASS 7.x
   Revised by Mark Lake, 10/08/20017, for r.azimuth.distance in GRASS 7.x
   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 17/08/2000, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"

#define AZ_PI     3.14159265
#define AZ_RAD90  1.57079633
#define AZ_RAD180 3.14159265
#define AZ_RAD270 4.71238898
#define AZ_RAD360 6.28318531

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

double calc_azimuth(int row, int col, int reverse)
{
    double azimuth, alpha;
    double row_diff, col_diff, x, y;
    int row_dir, col_dir;
    int quad, axis;

    /* Dummy values so we know whether various azimuths have been calculated */

    axis = 0;
    quad = 0;
    azimuth = 999.0;

    /* Get the two sides of the triangle */

    col_diff = (double)(col - point_col);
    row_diff = (double)(row - point_row);

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

    col_dir = 0; /* cell same longitude as point */
    row_dir = 0; /* cell same latitude as point */
    if (col_diff < 0.0)
        col_dir = -1; /* cell to west of point */
    else if (col_diff > 0.0)
        col_dir = 1; /* cell to east of point */
    if (row_diff < 0.0)
        row_dir = -1; /* cell to north of point */
    else if (row_diff > 0.0)
        row_dir = 1; /* cell to south of point */

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

    /* Calculate azimuths for cells which fall on axes */

    if (axis) {
        if (reverse) {
            /* Calculate bearing from cell towards point */
            switch (axis) {
            case (1):
                azimuth = 180.0;
                break;
            case (2):
                azimuth = 270.0;
                break;
            case (3):
                azimuth = 0.0;
                break;
            case (4):
                azimuth = 90.0;
                break;
            case (5):
                azimuth = IS_POINT;
                break;
            };
        }
        else {
            /* Calculate bearing from point towards cell */
            switch (axis) {
            case (1):
                azimuth = 0.0;
                break;
            case (2):
                azimuth = 90.0;
                break;
            case (3):
                azimuth = 180.0;
                break;
            case (4):
                azimuth = 270.0;
                break;
            case (5):
                azimuth = IS_POINT;
                break;
            };
        }
    }
    else {
        /* Calculate azimuths for cells which do not fall on axes as */

        x = (fabs(col_diff) * window.ew_res);
        y = (fabs(row_diff) * window.ns_res);

        /* Now calculate alpha */

        alpha = atan(x / y);

        /* Convert alpha in radians to azimuth in degrees */

        if (reverse) {
            /* Calculate bearing from cell towards point */
            switch (quad) {
            case (1):
                azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
                break;
            case (2):
                azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
                /* Shouldn't produce 360, since that should only occur for cell
                 * on axis) */
                break;
            case (3):
                azimuth = alpha * 180.0 / AZ_PI;
                break;
            case (4):
                azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
                break;
            }
        }
        else {
            /* Calculate bearing from point towards cell */
            switch (quad) {
            case (1):
                azimuth = alpha * 180.0 / AZ_PI;
                break;
            case (2):
                azimuth = (AZ_RAD180 - alpha) * 180.0 / AZ_PI;
                break;
            case (3):
                azimuth = (AZ_RAD180 + alpha) * 180.0 / AZ_PI;
                break;
            case (4):
                azimuth = (AZ_RAD360 - alpha) * 180.0 / AZ_PI;
                break;
            }
        }
    }

    return azimuth;
}

/***********************************************************************/
/*
   This variant computes the axial difference such that if the bearing
   is aligned with the reference bearing then the result is zero. If the
   the bearing is orthogonal to the reference bearing then the result is
   +90. Intermediate differences fall between 0 and +90.
 */

double calc_azimuth_axial_diff(double reference_bearing, double bearing)
{
    double diff;

    diff = fabs(reference_bearing - bearing);
    if (diff > 270.0)
        diff = fabs(360 - diff);
    else {
        if (diff > 90.0)
            diff = fabs(180.0 - diff);
    }
    return (diff);
}

/***********************************************************************/
/*
   This variant computes the axial difference such that if the bearing
   is aligned with the reference bearing then the result is zero. If the
   the bearing is orthogonal to the reference bearing then the result is
   +/-90. Intermediate differences fall between 0 and +/-90. The difference is
   positive if the bearing is between 0 and 180 degree clockwise of the
   reference bearing. The difference is negative if the bearing is
   between 0 and 180 degrees anticlockwise of the reference bearing.
 */

double calc_azimuth_axial_diff_signed(double reference_bearing, double bearing)
{
    double diff;
    double relative_bearing;

    /* First convert the bearing relative to the reference bearing */

    if (bearing < reference_bearing)
        relative_bearing = (360 - reference_bearing) + bearing;
    else
        relative_bearing = bearing - reference_bearing;

    /* Now compute the difference */

    if (relative_bearing <= 90)
        diff = relative_bearing;
    else {
        if (relative_bearing > 90 && relative_bearing <= 180)
            diff = 90 - (relative_bearing - 90);
        else {
            if (relative_bearing > 180 && relative_bearing <= 270)
                diff = 180 - relative_bearing;
            else
                diff = (relative_bearing - 270) - 90;
        }
    }

    return (diff);
}

/***********************************************************************/

double calc_azimuth_clockwise_diff(double reference_bearing, double bearing)
{
    double diff;

    if (reference_bearing > bearing)
        diff = 360.0 - (reference_bearing - bearing);
    else
        diff = bearing - reference_bearing;

    return (diff);
}

/***********************************************************************/

int calc_segment(double diff)
{
    if (do_eight_segments) {
        if (diff >= 0 && diff < 45)
            return 1;
        if (diff >= 45 && diff < 90)
            return 2;
        if (diff >= 90 && diff < 135)
            return 3;
        if (diff >= 135 && diff < 180)
            return 4;
        if (diff >= 180 && diff < 225)
            return 5;
        if (diff >= 225 && diff < 270)
            return 6;
        if (diff >= 270 && diff < 315)
            return 7;
        if (diff >= 315 && diff < 360)
            return 8;
    }
    else {
        if (do_square_segments) {
            if (diff >= 0 && diff < 90)
                return 1;
            if (diff >= 90 && diff < 180)
                return 2;
            if (diff >= 180 && diff < 270)
                return 3;
            if (diff >= 270 && diff < 360)
                return 4;
        }
        else {
            if (diff >= 315 || diff < 45)
                return 1;
            if (diff >= 45 && diff < 135)
                return 2;
            if (diff >= 135 && diff < 225)
                return 3;
            if (diff >= 225 && diff < 315)
                return 4;
        }
    }
    /* Should not get here */
    return 0;
}

/***********************************************************************/

/***********************************************************************/

double calc_distance(int row, int col)
{
    double distance = 0.0;
    double row_diff, col_diff;
    double ew_diff, ns_diff;
    int row_dir, col_dir;
    int axis;

    /* Dummy values so we know whether various azimuths have been calculated */

    axis = 0;

    /* Get the two sides of the triangle */

    col_diff = (double)(col - point_col);
    row_diff = (double)(row - point_row);

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

    col_dir = 0; /* cell same longitude as point */
    row_dir = 0; /* cell same latitude as point */
    if (col_diff < 0.0)
        col_dir = -1; /* cell to west of point */
    else if (col_diff > 0.0)
        col_dir = 1; /* cell to east of point */
    if (row_diff < 0.0)
        row_dir = -1; /* cell to north of point */
    else if (row_diff > 0.0)
        row_dir = 1; /* cell to south of point */

    switch (col_dir) {
    case (-1):
        switch (row_dir) {
        case (0):
            axis = 4;
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
        case (0):
            axis = 2;
            break;
        };
        break;
    };

    /* Calculate centre-to-centre distances for cells which fall on
       axes */

    point_col = (int)Rast_easting_to_col(east, &window);
    point_row = (int)Rast_northing_to_row(north, &window);

    ew_diff = fabs(east - Rast_col_to_easting(col, &window));
    ns_diff = fabs(north - Rast_row_to_northing(row, &window));

    if (axis) {
        switch (axis) {
        case (1):
            distance = ns_diff;
            break;
        case (2):
            distance = ew_diff;
            break;
        case (3):
            distance = ns_diff;
            break;
        case (4):
            distance = ew_diff;
            break;
        case (5):
            distance = 0.0;
            break;
        };
    }
    else {
        /* Calculate distance for cells which do not fall on axes */
        /* Calc orthogonal distances from centre to centre  */

        distance = sqrt((ew_diff * ew_diff) + (ns_diff * ns_diff));
    }

    return distance;
}
