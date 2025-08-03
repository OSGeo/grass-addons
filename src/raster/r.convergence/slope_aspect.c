#include "local_proto.h"

int get_distance(int once, int row)
{

    double north, south, east, west, middle;
    double zfactor = 1;

    if (once) {

        north = Rast_row_to_northing(0.5, &window);
        middle = Rast_row_to_northing(1.5, &window);
        south = Rast_row_to_northing(2.5, &window);
        east = Rast_col_to_easting(2.5, &window);
        west = Rast_col_to_easting(0.5, &window);
    }
    else {

        north = Rast_row_to_northing(row + 0.5, &window);
        middle = Rast_row_to_northing(row + 1.5, &window);
        south = Rast_row_to_northing(row + 2.5, &window);
        east = Rast_col_to_easting(2.5, &window);
        west = Rast_col_to_easting(0.5, &window);
    }

    V = G_distance(east, north, east, south) / zfactor;
    H = G_distance(east, middle, west, middle) / zfactor;
    return 0;
}

int create_distance_aspect_matrix(int row)
{

    int i;
    int mx, x, my, y;
    int dx, dy;
    float distance;
    int set_to_zero = 0;
    float cur_northing, cur_easting, target_northing, target_easting;
    float ns_dist, ew_dist;
    float min_cell_size;

    aspect_matrix = G_calloc(window_size * window_size, sizeof(float));
    distance_matrix = G_calloc(window_size * window_size, sizeof(float));

    cur_northing = Rast_row_to_northing(row + 0.5, &window);
    cur_easting = Rast_col_to_easting(0.5, &window);
    target_northing = Rast_row_to_northing(row + 1.5, &window);
    target_easting = Rast_col_to_easting(1.5, &window);

    ns_dist =
        G_distance(cur_easting, cur_northing, cur_easting, target_northing);
    ew_dist =
        G_distance(cur_easting, cur_northing, target_easting, cur_northing);

    min_cell_size = MIN(ns_dist, ew_dist);

    for (my = 0, y = -radius; my < window_size; ++my, ++y)
        for (mx = 0, x = radius; mx < window_size; ++mx, --x) {

            cur_northing = Rast_row_to_northing(row + 0.5, &window);
            cur_easting = Rast_col_to_easting(0.5, &window);
            target_northing = Rast_row_to_northing(row + y + 0.5, &window);
            target_easting = Rast_col_to_easting(x + 0.5, &window);

            distance = G_distance(cur_easting, cur_northing, target_easting,
                                  target_northing);
            distance /= min_cell_size;

            set_to_zero = 0;
            if (distance < 1)
                set_to_zero = 1;
            if (f_circular && distance > radius)
                set_to_zero = 1;

            if (set_to_zero) {
                distance_matrix[my * window_size + mx] = 0;
                aspect_matrix[my * window_size + mx] = -1;
            }
            else {
                distance_matrix[my * window_size + mx] = distance;
                ns_dist = G_distance(cur_easting, cur_northing, cur_easting,
                                     target_northing);
                ns_dist = (cur_northing > target_northing) ? ns_dist : -ns_dist;
                ew_dist = G_distance(cur_easting, cur_northing, target_easting,
                                     cur_northing);
                ew_dist = (cur_easting > target_easting) ? -ew_dist : ew_dist;

                aspect_matrix[my * window_size + mx] =
                    (y != 0.) ? PI + atan2(ew_dist, ns_dist)
                              : (x > 0. ? PI2 + PI : PI2);
            }
        }

    return 0;
}

int get_slope_aspect(int row)
{

    int col, i;
    FCELL c[10];
    FCELL dx, dy;
    FCELL *uprow, *thisrow, *downrow;
    int d_row[] = {-1, -1, -1, 0, 0, 0, 1, 1, 1};
    int d_col[] = {-1, 0, 1, -1, 0, 1, -1, 0, 1};

    if (row < 1 || row > nrows - 2) {
        Rast_set_f_null_value(slope[row], ncols);
        Rast_set_f_null_value(aspect[row], ncols);
        return 1;
    }

    Rast_set_f_null_value(&slope[row][0], 1);
    Rast_set_f_null_value(&aspect[row][0], 1);
    Rast_set_f_null_value(&slope[row][ncols - 1], 1);
    Rast_set_f_null_value(&aspect[row][ncols - 1], 1);

    uprow = elevation.elev[row - 1];
    thisrow = elevation.elev[row];
    downrow = elevation.elev[row + 1];

    for (col = 1; col < ncols - 1; ++col) {

        for (i = 0; i < 9; ++i)
            if (Rast_is_f_null_value(
                    &elevation.elev[row + d_row[i]][col + d_col[i]])) {
                Rast_set_f_null_value(&slope[row][col], 1);
                Rast_set_f_null_value(&aspect[row][col], 1);
                continue;
            }

        dx = ((elevation.elev[row - 1][col - 1] +
               2 * elevation.elev[row][col - 1] +
               elevation.elev[row + 1][col - 1]) -
              (elevation.elev[row - 1][col + 1] +
               2 * elevation.elev[row][col + 1] +
               elevation.elev[row + 1][col + 1])) /
             (H * 4);

        dy = ((elevation.elev[row + 1][col - 1] +
               2 * elevation.elev[row + 1][col] +
               elevation.elev[row + 1][col + 1]) -
              (elevation.elev[row - 1][col - 1] +
               2 * elevation.elev[row - 1][col] +
               elevation.elev[row - 1][col + 1])) /
             (V * 4);

        slope[row][col] = atan(sqrt(dx * dx + dy * dy));
        if (dy == 0.)
            aspect[row][col] = dx < 0 ? PI + PI2 : PI2;
        else
            aspect[row][col] =
                atan2(dx, dy) < 0 ? atan2(dx, dy) + M2PI : atan2(dx, dy);
    }
    return 0;
}

float calculate_convergence(int row, int cur_row, int col)
{
    int i, j, k = 0;
    float i_distance;
    float conv, sum = 0, div = 0;
    float x;
    float cur_slope;
    float slope_modifier;
    float distance_modifier;
    float cur_northing, cur_easting, target_northing, target_easting,
        cur_distance;

    if (f_slope) {
        cur_northing = Rast_row_to_northing(row + 0.5, &window);
        cur_easting = Rast_col_to_easting(col + 0.5, &window);
    }

    for (i = -radius; i < radius + 1; ++i)
        for (j = -radius; j < radius + 1; ++j, ++k) {

            if (cur_row + i < 0 || cur_row + i > window_size - 1 ||
                col + j < 1 || col + j > ncols - 2)
                continue;
            x = distance_matrix[k];

            if (x < 1)
                continue;

            if (f_slope) {
                target_northing = Rast_row_to_northing(row + i + 0.5, &window);
                target_easting = Rast_col_to_easting(col + j + 0.5, &window);

                cur_distance = G_distance(cur_easting, cur_northing,
                                          target_easting, target_northing);
                cur_slope = (atan((elevation.elev[cur_row + i][col + j] -
                                   elevation.elev[cur_row][col]) /
                                  cur_distance));
                slope_modifier = sin(slope[cur_row][col]) * sin(cur_slope) +
                                 cos(slope[cur_row][col]) * cos(cur_slope);
            }

            conv = aspect[cur_row + i][col + j] - aspect_matrix[k];

            if (f_slope)
                conv = acos(slope_modifier * cos(conv));

            if (conv < -PI)
                conv += M2PI;
            else if (conv > PI)
                conv -= M2PI;

            switch (f_method) {
            case 0:
                distance_modifier = 1;
                break;
            case 1: /* inverse */
                distance_modifier = x;
                break;
            case 2: /* power */
                distance_modifier = x * x;
                break;
            case 3: /* square */
                distance_modifier = sqrt(x);
                break;
            case 4: /* gentle */
                distance_modifier = 1 + ((1 - x) * (1 + x));
                break;
            default:
                G_fatal_error(_("Decay: wrong option"));
            }

            sum += fabs(conv) * (1 / distance_modifier);
            div += 1 / distance_modifier;

        } /* end for i, j */

    sum /= div;
    sum -= PI2;
    return sum;
}
