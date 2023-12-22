#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int lines_center(struct Map_info *In, struct Map_info *Out, int layer,
                 struct cat_list *cat_list, int n_primitives, int mode)
{
    struct line_pnts *Points, *OPoints;
    struct line_cats *Cats, *ICats;
    double x, y, z;
    int type, cat;
    int i, counter;

    Points = Vect_new_line_struct();
    OPoints = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    ICats = Vect_new_cats_struct();

    /* mid point */
    if (mode & L_MID) {
        double len;

        G_message(_("Calculating mid point coordinates..."));
        counter = 0;

        Vect_rewind(In);
        while ((type = Vect_read_next_line(In, Points, ICats)) > 0) {
            G_percent(counter, n_primitives, 4);
            counter++;

            if (!(type & GV_LINE))
                continue;

            cat = -1;
            Vect_reset_cats(Cats);
            if (layer > 0) {
                if (!Vect_cats_in_constraint(ICats, layer, cat_list))
                    continue;

                for (i = 0; i < ICats->n_cats; i++) {
                    if (ICats->field[i] == layer) {
                        Vect_cat_set(Cats, 1, ICats->cat[i]);
                        cat = ICats->cat[i];
                    }
                }
            }

            Vect_line_prune(Points);

            len = Vect_line_length(Points) / 2.;

            Vect_point_on_line(Points, len, &x, &y, &z, NULL, NULL);

            if (Out) {
                Vect_reset_line(OPoints);
                Vect_append_point(OPoints, x, y, z);
                Vect_cat_set(Cats, 2, 4);
                Vect_write_line(Out, GV_POINT, OPoints, Cats);
            }
            else {
                if (layer > 0)
                    fprintf(stdout, "%.15g|%.15g|%.15g|4|%d\n", x, y, z, cat);
                else
                    fprintf(stdout, "%.15g|%.15g|%.15g|4\n", x, y, z);
            }
        }
        G_percent(1, 1, 1);
    }

    /* center of gravity */
    if (mode & L_MEAN) {
        double len, slen;
        double dx, dy, dz;

        G_message(_("Calculating centers of gravity for lines..."));
        counter = 0;

        Vect_rewind(In);
        while ((type = Vect_read_next_line(In, Points, ICats)) > 0) {
            G_percent(counter, n_primitives, 4);
            counter++;
            if (!(type & GV_LINE))
                continue;

            cat = -1;
            Vect_reset_cats(Cats);
            if (layer > 0) {
                if (!Vect_cats_in_constraint(ICats, layer, cat_list))
                    continue;

                for (i = 0; i < ICats->n_cats; i++) {
                    if (ICats->field[i] == layer) {
                        Vect_cat_set(Cats, 1, ICats->cat[i]);
                        cat = ICats->cat[i];
                    }
                }
            }

            Vect_line_prune(Points);

            len = 0.;

            x = y = z = 0.;

            for (i = 1; i < Points->n_points; i++) {
                dx = Points->x[i - 1] - Points->x[i];
                dy = Points->y[i - 1] - Points->y[i];
                dz = Points->z[i - 1] - Points->z[i];

                slen = sqrt(dx * dx + dy * dy + dz * dz);

                x += (Points->x[i - 1] + Points->x[i]) * slen;
                y += (Points->y[i - 1] + Points->y[i]) * slen;
                z += (Points->z[i - 1] + Points->z[i]) * slen;

                len += slen;
            }

            x /= (len * 2);
            y /= (len * 2);
            z /= (len * 2);

            if (Out) {
                Vect_reset_line(OPoints);
                Vect_append_point(OPoints, x, y, z);
                Vect_cat_set(Cats, 2, 5);
                Vect_write_line(Out, GV_POINT, OPoints, Cats);
            }
            else {
                if (layer > 0)
                    fprintf(stdout, "%.15g|%.15g|%.15g|5|%d\n", x, y, z, cat);
                else
                    fprintf(stdout, "%.15g|%.15g|%.15g|5\n", x, y, z);
            }
        }
        G_percent(1, 1, 1);
    }

    /* approximate geometric median with Weiszfeld's algorithm:
     * iterative least squares reduction */
    if (mode & L_MEDIAN) {
        struct line_pnts *SPoints;
        double *len;
        double dx, dy, dz;
        double xmean, ymean, zmean;
        double medx, medy, medz;
        double dist, distsum, dist2all, lastdist2all;
        int j, iter, maxiter = 100;

        SPoints = Vect_new_line_struct();

        G_message(_("Approximating geometric medians..."));
        counter = 0;

        Vect_rewind(In);
        while ((type = Vect_read_next_line(In, Points, ICats)) > 0) {
            G_percent(counter, n_primitives, 4);
            counter++;
            if (!(type & GV_LINE))
                continue;

            cat = -1;
            Vect_reset_cats(Cats);
            if (layer > 0) {
                if (!Vect_cats_in_constraint(ICats, layer, cat_list))
                    continue;

                for (i = 0; i < ICats->n_cats; i++) {
                    if (ICats->field[i] == layer) {
                        Vect_cat_set(Cats, 1, ICats->cat[i]);
                        cat = ICats->cat[i];
                    }
                }
            }

            Vect_line_prune(Points);

            len = G_malloc((Points->n_points - 1) * sizeof(double));
            Vect_reset_line(SPoints);

            xmean = ymean = zmean = 0.;

            for (i = 0; i < Points->n_points - 1; i++) {
                dx = Points->x[i + 1] - Points->x[i];
                dy = Points->y[i + 1] - Points->y[i];
                dz = Points->z[i + 1] - Points->z[i];

                len[i] = sqrt(dx * dx + dy * dy + dz * dz);

                x = (Points->x[i + 1] + Points->x[i]) / 2.;
                y = (Points->y[i + 1] + Points->y[i]) / 2.;
                z = (Points->z[i + 1] + Points->z[i]) / 2.;

                Vect_append_point(SPoints, x, y, z);

                xmean += Points->x[i];
                ymean += Points->y[i];
                zmean += Points->z[i];
            }

            i = Points->n_points - 1;
            xmean += Points->x[i];
            ymean += Points->y[i];
            zmean += Points->z[i];

            xmean /= Points->n_points;
            ymean /= Points->n_points;
            zmean /= Points->n_points;

            medx = xmean;
            medy = ymean;
            medz = zmean;

            lastdist2all = -1;

            G_debug(3, "Approximating geometric median...");

            for (iter = 0; iter < maxiter; iter++) {

                distsum = dist2all = 0.;
                x = y = z = 0.;

                for (j = 0; j < SPoints->n_points; j++) {

                    dx = SPoints->x[j] - medx;
                    dy = SPoints->y[j] - medy;
                    dz = SPoints->z[j] - medz;
                    dist = sqrt(dx * dx + dy * dy + dz * dz);

                    if (dist) {
                        x += SPoints->x[j] * len[j] / dist;
                        y += SPoints->y[j] * len[j] / dist;
                        z += SPoints->z[j] * len[j] / dist;

                        distsum += len[j] / dist;
                        dist2all += dist;
                    }
                    if (len[j])
                        dist2all += dist / len[j];
                }

                if (distsum) {
                    x /= distsum;
                    y /= distsum;
                    z /= distsum;
                }

                G_debug(3, "dist2all: %.15g", dist2all);
                G_debug(3, "lastdist2all: %.15g", lastdist2all);
                if (lastdist2all > 0) {
                    double d = d_ulp(lastdist2all);

                    if (lastdist2all - dist2all < d)
                        break;
                }
                if (dist2all == 0.)
                    break;

                lastdist2all = dist2all;

                medx = x;
                medy = y;
                medz = z;
            }
            G_debug(3, "Iteration converged after %d passes, dist = %.15g",
                    iter, lastdist2all);

            G_free(len);

            x = medx;
            y = medy;
            z = medz;

            if (Out) {
                Vect_reset_line(OPoints);
                Vect_append_point(OPoints, x, y, z);
                Vect_cat_set(Cats, 2, 6);
                Vect_write_line(Out, GV_POINT, OPoints, Cats);
            }
            else {
                if (layer > 0)
                    fprintf(stdout, "%.15g|%.15g|%.15g|6|%d\n", x, y, z, cat);
                else
                    fprintf(stdout, "%.15g|%.15g|%.15g|6\n", x, y, z);
            }
        }
        G_percent(1, 1, 1);
    }

    return 1;
}
