#include <grass/vector.h>

#include "proto.h"

void load_points(struct Map_info *In, struct line_pnts *Points,
                 struct line_cats *Cats)
{
    /* variables */
    struct line_pnts *OPoints;
    int type, i, cat;

    /* create and initializes structs where to store points, categories */
    OPoints = Vect_new_line_struct();

    Vect_reset_cats(Cats);

    /* load points */
    while ((type = Vect_read_next_line(In, OPoints, Cats)) > 0) {
        if (type == GV_LINE || type == GV_POINT || type == GV_CENTROID) {
            if (Vect_cat_get(Cats, 1, &cat) == 0) {
                Vect_cat_set(Cats, 1, i);
                i++;
            }
        }

        Vect_append_points(Points, OPoints, GV_FORWARD);
        Vect_reset_line(OPoints);
    }

    Vect_destroy_line_struct(OPoints);

    /* close map */
    Vect_close(In);
}
