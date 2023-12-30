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

#include <stdio.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>

#include "double_list.h"

#define SIZE_INCREMENT 10

int double_list_add_item(struct DoubleList *double_list, double item)
{
    int n = double_list->num_items++;

    if (double_list->num_items >= double_list->max_items) {
        double_list->max_items += SIZE_INCREMENT;
        double_list->items =
            G_realloc(double_list->items,
                      (size_t)double_list->max_items * sizeof(double));
    }
    /* n contains the index */
    double_list->items[n] = item;
    return n;
}

void double_list_from_one_item(struct DoubleList *double_list, double item)
{
    double_list->num_items = 0;
    double_list->max_items = 0;
    double_list->items = NULL;
    double_list_add_item(double_list, item);
}

void double_list_init(struct DoubleList *double_list)
{
    double_list->num_items = 0;
    double_list->max_items = 0;
    double_list->items = NULL;
}

void double_list_free(struct DoubleList *double_list)
{
    G_free(double_list->items);
    double_list->num_items = 0;
    double_list->max_items = 0;
    double_list->items = NULL;
}
