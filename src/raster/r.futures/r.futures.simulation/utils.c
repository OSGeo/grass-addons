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

/*!
 * \brief Internal function for percentile computation.
 * Taken from r.univar.
 * \param array to sort
 * \param n array size
 * \param k
 */
static void downheap_float(float *array, size_t n, size_t k)
{
    size_t j;
    float v;

    v = array[k];
    while (k <= n / 2) {
        j = k + k;
        if (j < n && array[j] < array[j + 1])
            j++;
        if (v >= array[j])
            break;
        array[k] = array[j];
        k = j;
    }
    array[k] = v;
}

/*!
 * \brief Internal function for percentile computation.
 * Taken from r.univar.
 * \param array
 * \param n
 */
static void heapsort_float(float *array, size_t n)
{
    ssize_t k;
    float t;

    --n;
    for (k = n / 2; k >= 0; k--)
        downheap_float(array, n, k);

    while (n > 0) {
        t = array[0];
        array[0] = array[n];
        array[n] = t;
        downheap_float(array, --n, 0);
    }
}
/*!
 * \brief Get percentile p of array of size n
 * \param array array to be sorted
 * \param n size of array
 * \param p percentile (0-100)
 * \return
 */
float get_percentile(float *array, size_t n, int p)
{
    int perc;
    perc = (int)(n * 1e-2 * p - 0.5);
    heapsort_float(array, n);
    return array[perc];
}

/*!
 * \brief float comparison for qsort
 */
int float_cmp(const void *a, const void *b)
{
    float fa = *(const float *)a;
    float fb = *(const float *)b;
    return (fa > fb) - (fa < fb);
}
/*!
 * \brief int comparison for qsort
 */
int int_cmp(const void *a, const void *b)
{
    int fa = *(const int *)a;
    int fb = *(const int *)b;
    return (fa > fb) - (fa < fb);
}
