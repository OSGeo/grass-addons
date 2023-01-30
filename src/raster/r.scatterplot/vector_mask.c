/*
 * v.in.lidar vector mask
 *
 * Copyright 2016 by Vaclav Petras, and The GRASS Development Team
 *
 * This program is free software licensed under the GPL (>=v2).
 * Read the COPYING file that comes with GRASS for details.
 *
 */

#include <grass/vector.h>
#include <grass/glocale.h>

#include "vector_mask.h"

void VectorMask_init(struct VectorMask *vector_mask, const char *name,
                     const char *layer, char *cats, char *where,
                     int invert_mask)
{
    vector_mask->map_info = G_malloc(sizeof(struct Map_info));
    if (Vect_open_old2(vector_mask->map_info, name, "", layer) < 2)
        G_fatal_error(_("Failed to open vector <%s>"), name);
    vector_mask->cats = NULL;
    vector_mask->layer = Vect_get_field_number(vector_mask->map_info, layer);
    if (vector_mask->layer > 0 && (cats || where))
        vector_mask->cats = Vect_cats_set_constraint(
            vector_mask->map_info, vector_mask->layer, where, cats);
    vector_mask->map_bbox = G_malloc(sizeof(struct bound_box));
    Vect_get_map_box(vector_mask->map_info, vector_mask->map_bbox);
    vector_mask->nareas = Vect_get_num_areas(vector_mask->map_info);
    vector_mask->area_bboxes =
        G_malloc(vector_mask->nareas * sizeof(struct bound_box));
    vector_mask->area_cats =
        G_malloc(vector_mask->nareas * sizeof(struct line_cats *));
    int i;
    struct line_cats *area_cats;
    for (i = 1; i <= vector_mask->nareas; i++) {
        Vect_get_area_box(vector_mask->map_info, i,
                          &vector_mask->area_bboxes[i - 1]);
        if (vector_mask->cats) {
            /* it would be nice to allocate whole list at once
             * with a library function */
            area_cats = Vect_new_cats_struct();
            /* getting the cats ahead of time cuts the time to less
             * than half for maps with many areas */
            Vect_get_area_cats(vector_mask->map_info, i, area_cats);
            vector_mask->area_cats[i - 1] = area_cats;
        }
    }
    G_debug(3, "VectorMask_init(): loaded %d areas", vector_mask->nareas);
    if (invert_mask)
        vector_mask->inverted = 1;
    else
        vector_mask->inverted = 0;
}

void VectorMask_destroy(struct VectorMask *vector_mask)
{
    if (vector_mask->cats) {
        int i;
        for (i = 1; i <= vector_mask->nareas; i++) {
            Vect_destroy_cats_struct(vector_mask->area_cats[i - 1]);
        }
    }
    G_free(vector_mask->area_cats);
    G_free(vector_mask->map_bbox);
    G_free(vector_mask->area_bboxes);
    Vect_close(vector_mask->map_info);
    G_free(vector_mask->map_info);
}

int VectorMask_point_in(struct VectorMask *vector_mask, double x, double y)
{
    /* inv in res
     *   F  T continue
     *   F  F return F
     *   T  T continue
     *   T  F return T
     */
    // if (!Vect_point_in_box_2d(x, y, vector_mask->map_bbox))
    //     return vector_mask->inverted;
    int is_out = TRUE;
    int i;
    for (i = 1; i <= vector_mask->nareas; i++) {
        if (vector_mask->cats) {
            /* the same as if the area would not exist */
            if (!Vect_cats_in_constraint(vector_mask->area_cats[i - 1],
                                         vector_mask->layer, vector_mask->cats))
                continue;
        }
        if (Vect_point_in_area(x, y, vector_mask->map_info, i,
                               &vector_mask->area_bboxes[i - 1])) {
            is_out = FALSE;
            break;
        }
    }
    /* inv out res
     *  F   T   F
     *  F   F   T
     *  T   T   T
     *  T   F   F
     */
    if (vector_mask->inverted ^ is_out)
        return FALSE;
    return TRUE;
}
