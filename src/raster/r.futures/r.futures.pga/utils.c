/*!
   \file utils.c

   \brief Helper functions

   (C) 2016-2019 by Anna Petrasova, Vaclav Petras and the GRASS Development Team

   This program is free software under the GNU General Public License
   (>=v2).  Read the file COPYING that comes with GRASS for details.

   \author Anna Petrasova
   \author Vaclav Petras
 */
#include <stdlib.h>
#include <math.h>

/*!
 * \brief Computes euclidean distance in cells (not meters)
 * \param[in] row1 row1
 * \param[in] col1 col1
 * \param[in] row2 row2
 * \param[in] col2 col2
 * \return distance
 */
double get_distance(int row1, int col1, int row2, int col2)
{
    return sqrt((row1 - row2) * (row1 - row2) + (col1 - col2) * (col1 - col2));
}
/*!
 * \brief Get index (id) from x, y coordinate
 * \param[in] row
 * \param[in] col
 * \param[in] cols number of columns
 * \return index
 */
size_t get_idx_from_xy(int row, int col, int cols)
{
    return cols * row + col;
}

/*!
 * \brief Get x, y coordinates from index
 * \param[in] idx index (id)
 * \param[in] cols number of columns
 * \param[out] row
 * \param[out] col
 */
void get_xy_from_idx(size_t idx, int cols, int *row, int *col)
{
    *col = idx % cols;
    *row = (idx - *col) / cols;
}
