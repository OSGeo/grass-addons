/* File: palette.c
 *
 *  AUTHOR:    E. Jorge Tizado, Spain 2009
 *
 *  COPYRIGHT: (c) 2009 E. Jorge Tizado
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with GRASS
 *             for details.
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include "colors.h"
#include "palettes.h"

void RGB_HSV(PSCOLOR *, PALETTE *);
void HSV_RGB(PALETTE *, PSCOLOR *);


int palette_new(int n)
{
    int i = ncolors;

    ncolors += n;
    Palette = (PALETTE *) G_realloc(Palette, ncolors * sizeof(PALETTE));

    return i;
}

int PS_str_to_color(char *name, PSCOLOR *color)
{
    int i;

    for (i = 0; i < ncolors; i++)
    {
        if (strcmp(Palette[i].name, name) == 0)
        {
            HSV_RGB(&(Palette[i]), color);
            color->none = 0;
            return 1;
        }
    }
    color->none = 1;
    return 0;
}

/* pure colors: color-wheel */
int pure_color(char *name, int div)
{
    int i, k;
    double step;

    /* alloc memory */
    k = palette_new(div);

    step = 360./div;

    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = (double)i * step;
        Palette[k].s = 1.;
        Palette[k].v = 1.;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}

/* monochrome color: white to color */
int monochrome(char *name, PSCOLOR *rgb, int div)
{
    int i, k;
    double step;
    PALETTE hsv;

    if (rgb->r == rgb->g && rgb->g == rgb->b)
    {
        gray(name, div);
        return 1;
    }

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);

    if (div > 1) {
        step = 1./(double)(div-1);
    }
    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = hsv.h;
        Palette[k].s = (double)i * step;
        Palette[k].v = 1.;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}

/* gradient */
int gradient(char *name, PSCOLOR *A, PSCOLOR *B, int div, int pure)
{
    int i, k;
    double hstep, sstep, vstep;
    PALETTE pal_A, pal_B;

    RGB_HSV(A, &pal_A);
    RGB_HSV(B, &pal_B);

    if (pal_A.h == pal_B.h)
        return 0;

    if (pal_B.h < pal_A.h) {
        i = pal_A.h;
        pal_A.h = pal_B.h;
        pal_B.h = i;
    }

    /* alloc memory */
    k = palette_new(div);

    hstep = (pal_B.h - pal_A.h)/(div-1.);
    sstep = (pal_B.s - pal_A.s)/(div-1.);
    vstep = (pal_B.v - pal_A.v)/(div-1.);

    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = pal_A.h + (double)i * hstep;
        Palette[k].s = pure ? 1. : pal_A.s + (double)i * sstep;
        Palette[k].v = pure ? 1. : pal_A.v + (double)i * vstep;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}

/* analogous or similar color */
int analogous(char *name, PSCOLOR *rgb, int div)
{
    int i, k;
    double h, step;
    PALETTE hsv;

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);

    if (div > 1) {
        hsv.h -= 40.;
        step = 80./(double)(div-1);
    }

    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = hsv.h + (double)i * step;
        if (Palette[k].h < 0.)    Palette[k].h += 360.;
        if (Palette[k].h >= 360.) Palette[k].h -= 360.;
        Palette[k].s = hsv.s;
        Palette[k].v = hsv.v;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}

/* complementary or contrast color */
int complementary(char *name, PSCOLOR *rgb, int div)
{
    int i, k;
    double step;
    PALETTE hsv;

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);

    if (div > 1) {
        hsv.h += 140.;
        step = 80./(double)(div-1);
    }
    else {
        hsv.h += 180.;
    }
    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = hsv.h + (double)i * step;
        if (Palette[k].h < 0.)
            Palette[k].h += 360.;
        if (Palette[k].h >= 360.)
            Palette[k].h -= 360.;
        Palette[k].s = hsv.s;
        Palette[k].v = hsv.v;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}


/* gray color */
int gray(char *name, int div)
{
    int i, k;
    double step;

    /* alloc memory */
    k = palette_new(div);

    if (div > 1) {
        step = 1./(double)(div-1);
    }
    for (i = 0; i < div; i++, k++)
    {
        Palette[k].h = 0.;
        Palette[k].s = 0.;
        Palette[k].v = (double)i * step;
        sprintf(Palette[k].name, "%s%d", name, i);
    }

    return 1;
}


/*
 * TRANSFORMATIONS BETWEEN COLORSPACES
 */

/* r, g, b values are from 0 to 1
 * h = [0,360], s = [0,1], v = [0,1]
 */
void RGB_HSV(PSCOLOR *col, PALETTE *pal)
{
    double min, max;

    if (col->r == col->g && col->g == col->b)
    {
        pal->h = pal->s = 0.;   /* achromatic, gray */
        pal->v = col->b;
        return;
    }
    else if (col->r > col->g && col->r > col->b)
    {
        max = col->r;
        min = (col->g < col->b) ? col->g : col->b;
        pal->h = (col->g - col->b)/(max - min);
    }
    else if (col->g > col->b && col->g > col->r)
    {
        max = col->g;
        min = (col->r < col->b) ? col->r : col->b;
        pal->h = 2. + (col->b - col->r)/(max - min);
    }
    else
    {
        max = col->b;
        min = (col->g < col->r) ? col->g : col->r;
        pal->h = 4. + (col->r - col->g)/(max - min);
    }

    /* hue */
    pal->h *= 60.;
    if (pal->h < 0.) pal->h += 360.;
    /* saturation */
    pal->s = (max - min) / max;
    /* value */
    pal->v = max;

    return;
}

/* r, g, b values are from 0 to 1
 * h = [0,360], s = [0,1], v = [0,1]
 */
void HSV_RGB(PALETTE *pal, PSCOLOR *col)
{
    /* achromatic, gray */
    if (pal->s == 0) {
        col->r = col->g = col->b = pal->v;
        return;
    }

    int i;
    double f, p, q, t;
    i = floor(pal->h/60.);
    f = pal->h/60. - (double)i;
    p = pal->v * ( 1. - pal->s );
    q = pal->v * ( 1. - pal->s * f );
    t = pal->v * ( 1. - pal->s * ( 1. - f ) );
    switch (i)
    {
        case 0:
            col->r = pal->v;
            col->g = t;
            col->b = p;
            break;
        case 1:
            col->r = q;
            col->g = pal->v;
            col->b = p;
            break;
        case 2:
            col->r = p;
            col->g = pal->v;
            col->b = t;
            break;
        case 3:
            col->r = p;
            col->g = q;
            col->b = pal->v;
            break;
        case 4:
            col->r = t;
            col->g = p;
            col->b = pal->v;
            break;
        default: /* 5 */
            col->r = pal->v;
            col->g = p;
            col->b = q;
            break;
    }
}

