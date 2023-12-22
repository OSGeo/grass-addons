#include "local_proto.h"

int f_area(DCELL *vals, Coords **frags, int count)
{
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        vals[i] = (DCELL)(frags[i + 1] - frags[i]);
    }

    return 0;
}

int f_perim(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int border = 0;

        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            border += 4 - p->neighbors;
        }
        vals[i] = (DCELL)border;
    }

    return 0;
}

int f_shapeindex(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int border = 0;
        int area = (DCELL)(frags[i + 1] - frags[i]);

        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            border += 4 - p->neighbors;
        }
        vals[i] = (DCELL)border / (4 * sqrt((DCELL)area));
    }

    return 0;
}

int f_borderindex(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int border = 0;
        int maxx, maxy, minx, miny;
        int l = 0;
        int w = 0;

        maxx = minx = frags[i]->x;
        maxy = miny = frags[i]->y;
        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            border += 4 - p->neighbors;
            maxx = p->x > maxx ? p->x : maxx;
            minx = p->x < minx ? p->x : minx;
            maxy = p->y > maxy ? p->y : maxy;
            miny = p->y < miny ? p->y : miny;
        }
        l = maxx - minx + 1;
        w = maxy - miny + 1;
        vals[i] = (DCELL)border / (2 * ((DCELL)l + (DCELL)w));
    }

    return 0;
}

int f_compactness(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int area = 0;
        int maxx, maxy, minx, miny;
        int l = 0;
        int w = 0;

        maxx = minx = frags[i]->x;
        maxy = miny = frags[i]->y;
        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            area++;
            maxx = p->x > maxx ? p->x : maxx;
            minx = p->x < minx ? p->x : minx;
            maxy = p->y > maxy ? p->y : maxy;
            miny = p->y < miny ? p->y : miny;
        }
        l = maxx - minx + 1;
        w = maxy - miny + 1;
        vals[i] = (DCELL)l * (DCELL)w / (DCELL)area;
    }

    return 0;
}

int f_asymmetry(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        /* compute variance for x,y and xy in the patch */
        /* formula: a(x) = sum(x_i), b(x) = sum(x_i²), var(x) = (b(x) - a(x)² /
         * n) / n */
        /* covar(x*y) = (a(x * y) - a(x) * a(y) / n) /n */
        int ax, ay, axy;
        int bx, by;
        DCELL vx, vy, vxy, vsum, invn;
        int n = 0;

        ax = ay = axy = 0;
        bx = by = 0;
        /* for all cells in a patch */
        /*              fprintf(stderr, "\npatch %d: ", i); */
        for (p = frags[i]; p < frags[i + 1]; p++, n++) {
            int x = p->x;
            int y = p->y;
            int xy = p->x * p->y;

            ax += x;
            ay += y;
            axy += xy;
            bx += x * x;
            by += y * y;
            /*                      fprintf(stderr, "x_%d = %d, y_%d = %d; ", n,
             * x, n, y); */
        }
        invn = 1.0 / (DCELL)n;
        vx = ((DCELL)bx - (DCELL)ax * (DCELL)ax * invn) * invn;
        vy = ((DCELL)by - (DCELL)ay * (DCELL)ay * invn) * invn;
        vxy = ((DCELL)axy - (DCELL)ax * (DCELL)ay * invn) * invn;
        /*              fprintf(stderr, " axy = %d, ax = %d, ay = %d, n = %d",
         * axy, ax, ay, n); */
        vsum = vx + vy;
        vals[i] = 2 * sqrt(0.25 * vsum * vsum + vxy * vxy - vx * vy) / vsum;
    }
    return 1;
}

int f_area_perim_ratio(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int border = 0;
        int area = (DCELL)(frags[i + 1] - frags[i]);

        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            border += 4 - p->neighbors;
        }
        vals[i] = (DCELL)area / (DCELL)border;
    }

    return 0;
}

int f_frac_dim(DCELL *vals, Coords **frags, int count)
{
    Coords *p;
    int i;

    /* for all patches */
    for (i = 0; i < count; i++) {
        int border = 0;
        int area = (DCELL)(frags[i + 1] - frags[i]);

        /* for all cells in a patch */
        for (p = frags[i]; p < frags[i + 1]; p++) {
            border += 4 - p->neighbors;
        }
        vals[i] = 2 * log(0.25 * (DCELL)border) / log((DCELL)area);
    }

    return 0;
}

DCELL dist(Coords *p1, Coords *p2)
{
    int x1 = p1->x;
    int y1 = p1->y;
    int x2 = p2->x;
    int y2 = p2->y;
    int dx = x2 - x1;
    int dy = y2 - y1;

    return sqrt(dx * dx + dy * dy);
}

DCELL min_dist(Coords **frags, int n1, int n2)
{
    Coords *p1, *p2;
    DCELL min = 1000000.0;

    /* for all cells in the first patch */
    for (p1 = frags[n1]; p1 < frags[n1 + 1]; p1++) {
        /* if cell at the border */
        if (p1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = frags[n2]; p2 < frags[n2 + 1]; p2++) {
                /* if cell at the border */
                if (p2->neighbors < 4) {
                    DCELL d = dist(p1, p2);

                    if (d < min) {
                        min = d;
                    }
                }
            }
        }
    }

    return min;
}

int f_nearest_dist(DCELL *vals, Coords **frags, int count)
{
    int i, j;

    /* for all patches */
    for (i = 0; i < count; i++) {
        DCELL min = 1000000.0;

        for (j = 0; j < count; j++) {
            if (i != j) {
                DCELL d = min_dist(frags, i, j);

                if (d < min) {
                    min = d;
                }
            }
        }
        vals[i] = min;
    }

    return 0;
}
