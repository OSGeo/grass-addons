/****************************************************************************
 *
 * MODULE:       r.findtheriver
 * AUTHOR(S):    Brian Miles - brian_miles@unc.edu
 *               with hints from: Glynn Clements - glynn gclements.plus.com
 * PURPOSE:      Finds the nearest stream pixel to a coordinate pair using
 *                                  an upstream accumulating area map.
 *
 * SPDX-FileCopyrightText: 2013 the University of North Carolina at Chapel Hill
 * SPDX-FileCopyrightText: Other GRASS authors
 * SPDX-License-Identifier: GPL-2.0-or-later
 *****************************************************************************/

#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include "global.h"

PointList_t *create_list(int col, int row)
{
    PointList_t *head = (PointList_t *)G_malloc(sizeof(PointList_t));

    head->col = col;
    head->row = row;
    head->next = NULL;
    return head;
}

PointList_t *append_point(PointList_t *const head, int col, int row)
{
    PointList_t *tmp = head;

    while (NULL != tmp->next)
        tmp = tmp->next;
    tmp->next = (PointList_t *)G_malloc(sizeof(PointList_t));
    tmp->next->col = col;
    tmp->next->row = row;
    tmp->next->next = NULL;
    return tmp->next;
}

void destroy_list(PointList_t *head)
{
    if (NULL != head) {
        PointList_t *curr = head;
        PointList_t *next = curr->next;

        while (NULL != next) {
            free(curr);
            curr = next;
            next = curr->next;
        }
        G_free(curr);
    }
}

PointList_t *find_nearest_point(PointList_t *const head, int col, int row)
{

    PointList_t *nearest = NULL;
    double tmpDistance, minDistance = HUGE_VAL;
    PointList_t *curr = head;

    while (NULL != curr) {
        tmpDistance = sqrt(pow(col - curr->col, 2) + pow(row - curr->row, 2));
        if (tmpDistance < minDistance) {
            minDistance = tmpDistance;
            nearest = curr;
        }
        curr = curr->next;
    }
    return nearest;
}

void print_list(PointList_t *const head, const char *const sep)
{
    PointList_t *curr = head;

    G_debug(1, "Stream pixels: ");

    while (NULL != curr) {
        G_debug(1, "%d%s%d", curr->col, sep, curr->row);
        curr = curr->next;
    }
}

