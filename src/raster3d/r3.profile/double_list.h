/*
 * Functionality to handle list of doubles
 *
 * Authors:
 *   Vaclav Petras <wenzeslaus gmail com>
 *
 * Copyright 2015-2016 by Vaclav Petras, and the GRASS Development Team
 *
 * This program is free software licensed under the GPL (>=v2).
 * Read the COPYING file that comes with GRASS for details.
 *
 */

#ifndef __DOUBLE_LIST_H__
#define __DOUBLE_LIST_H__

struct DoubleList {
    int num_items;
    int max_items;
    double *items;
};

void double_list_init(struct DoubleList *double_list);
void double_list_from_one_item(struct DoubleList *double_list, double item);
void double_list_free(struct DoubleList *double_list);
int double_list_add_item(struct DoubleList *double_list, double item);

#endif /* __DOUBLE_LIST_H__ */
