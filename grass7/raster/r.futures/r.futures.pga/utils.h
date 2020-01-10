#ifndef FUTURES_UTILS_H
#define FUTURES_UTILS_H

#include <stdlib.h>

double get_distance(int row1, int col1, int row2, int col2);
size_t get_idx_from_xy(int row, int col, int cols);
void get_xy_from_idx(size_t idx, int cols, int *row, int *col);
#endif // FUTURES_UTILS_H
