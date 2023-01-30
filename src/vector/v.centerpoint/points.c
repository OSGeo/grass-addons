#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

double d_ulp(double d)
{
    int exp;

    if (d == 0)
        return GRASS_EPSILON;

    d = frexp(d, &exp);
    exp -= 51;
    d = ldexp(d, exp);

    return d;
}

int points_center(struct Map_info *In, struct Map_info *Out, int layer,
                  struct cat_list *cat_list, int n_primitives, int mode)
{
    struct line_pnts *Points, *OPoints;
    struct line_cats *Cats, *OCats;
    double xsum, xmean, ysum, ymean, zsum, zmean;
    double x, y, z;
    double medx, medy, medz;
    int type, counter, n;
    int iter, maxiter = 100;

    Points = Vect_new_line_struct();
    OPoints = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    OCats = Vect_new_cats_struct();

    Vect_rewind(In);

    /* coordinates' mean */
    counter = n = 0;
    xsum = ysum = zsum = 0.;
    G_message(_("Calculating center of gravity..."));
    while ((type = Vect_read_next_line(In, Points, Cats)) > 0) {
        G_percent(counter, n_primitives, 4);
        counter++;
        if (!(type & GV_POINT))
            continue;

        if (layer > 0 && !Vect_cats_in_constraint(Cats, layer, cat_list))
            continue;

        xsum += Points->x[0];
        ysum += Points->y[0];
        zsum += Points->z[0];
        n++;
    }
    G_percent(1, 1, 1);

    xmean = xsum / n;
    ymean = ysum / n;
    zmean = zsum / n;

    if (mode & P_MEAN) {
        x = xmean;
        y = ymean;
        z = zmean;

        if (Out) {
            Vect_reset_line(OPoints);
            Vect_append_point(OPoints, x, y, z);
            Vect_reset_cats(OCats);
            Vect_cat_set(OCats, 2, 1);
            Vect_write_line(Out, GV_POINT, OPoints, Cats);
        }
        else
            fprintf(stdout, "%.15g|%.15g|%.15g|1\n", x, y, z);
    }

    medx = xmean;
    medy = ymean;
    medz = zmean;

    /* approximate geometric median with Weiszfeld's algorithm:
     * iterative least squares reduction */
    if ((mode & P_MEDIAN) || (mode & P_MEDIAN_P)) {
        double dist, distsum, dist2all, lastdist2all;
        double dx, dy, dz;

        medx = xmean;
        medy = ymean;
        medz = zmean;
        lastdist2all = -1;

        G_message(_("Approximating geometric median..."));

        for (iter = 0; iter < maxiter; iter++) {

            G_percent(iter, maxiter, 4);

            distsum = dist2all = 0.;
            x = y = z = 0.;

            Vect_rewind(In);
            while ((type = Vect_read_next_line(In, Points, Cats)) > 0) {
                if (!(type & GV_POINT))
                    continue;
                if (layer > 0 &&
                    !Vect_cats_in_constraint(Cats, layer, cat_list))
                    continue;

                dx = Points->x[0] - medx;
                dy = Points->y[0] - medy;
                dz = Points->z[0] - medz;
                dist = sqrt(dx * dx + dy * dy + dz * dz);

                if (dist) {
                    x += Points->x[0] / dist;
                    y += Points->y[0] / dist;
                    z += Points->z[0] / dist;

                    distsum += 1 / dist;
                    dist2all += dist;
                }
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
        G_percent(1, 1, 1);
        G_message(_("Iteration converged after %d passes, dist = %.15g"), iter,
                  lastdist2all);

        if (mode & P_MEDIAN) {
            x = medx;
            y = medy;
            z = medz;

            if (Out) {
                Vect_reset_line(OPoints);
                Vect_append_point(OPoints, x, y, z);
                Vect_reset_cats(OCats);
                Vect_cat_set(OCats, 2, 2);
                Vect_write_line(Out, GV_POINT, OPoints, Cats);
            }
            else
                fprintf(stdout, "%.15g|%.15g|%.15g|2\n", x, y, z);
        }
    }

    /* find point closest to approximated median */
    if (mode & P_MEDIAN_P) {
        double dx, dy, dz;
        double dist, mindist;
        double xmin, ymin, zmin;

        counter = 0;

        xmin = medx;
        ymin = medy;
        zmin = medz;

        mindist = -1;

        G_message(_("Searching point closest to approximated median..."));

        Vect_rewind(In);
        while ((type = Vect_read_next_line(In, Points, Cats)) > 0) {
            G_percent(counter, n_primitives, 4);
            counter++;
            if (!(type & GV_POINT))
                continue;
            if (layer > 0 && !Vect_cats_in_constraint(Cats, layer, cat_list))
                continue;

            dx = Points->x[0] - medx;
            dy = Points->y[0] - medy;
            dz = Points->z[0] - medz;
            dist = sqrt(dx * dx + dy * dy + dz * dz);

            if (dist < mindist || mindist < 0) {
                xmin = Points->x[0];
                ymin = Points->y[0];
                zmin = Points->z[0];
                mindist = dist;
            }
        }
        G_percent(1, 1, 1);

        x = xmin;
        y = ymin;
        z = zmin;
        if (Out) {
            Vect_reset_line(OPoints);
            Vect_append_point(OPoints, x, y, z);
            Vect_reset_cats(OCats);
            Vect_cat_set(OCats, 2, 3);
            Vect_write_line(Out, GV_POINT, OPoints, Cats);
        }
        else
            fprintf(stdout, "%.15g|%.15g|%.15g|3\n", x, y, z);
    }

    return 1;
}
