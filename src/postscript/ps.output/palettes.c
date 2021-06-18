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

int PS_str_to_color(char *name, PSCOLOR * color)
{
    int i;

    for (i = 0; i < ncolors; i++) {
	if (strcmp(Palette[i].name, name) == 0) {
	    HSV_RGB(&(Palette[i]), color);
	    color->none = 0;
	    return 1;
	}
    }
    color->none = 1;
    return 0;
}

/*
   void PL_set_name(int k, char *name, int i)
   {
   if (Palette[k].h < 0.)    Palette[k].h += 360.;
   if (Palette[k].h >= 360.) Palette[k].h -= 360.;

   sprintf(Palette[k].name, "%s%d", name, i);
   }
 */

/* pure colors: color-wheel */
int pure_color(char *name, int div)
{
    int i, k;
    double step;

    /* alloc memory */
    k = palette_new(div);

    step = 360. / div;

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = (double)i *step;

	Palette[k].s = 1.;
	Palette[k].v = 1.;
	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* gray color: white to black */
int gray(char *name, int div)
{
    int i, k;
    double step;

    /* alloc memory */
    k = palette_new(div);
    step = (div > 1) ? (1. / (double)(div - 1)) : 0.;

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = 0.;
	Palette[k].s = 0.;
	Palette[k].v = (double)i *step;	/* ((double)i * step) ^ (1.5) */

	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* monochrome color: white to color */
int monochrome(char *name, PSCOLOR * rgb, int div)
{
    int i, k;
    double step;
    PALETTE hsv;

    if (rgb->r == rgb->g && rgb->g == rgb->b) {
	gray(name, div);
	return 1;
    }

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);
    step = (div > 1) ? (1. / (double)(div - 1)) : 0.;

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = hsv.h;
	Palette[k].s = (double)i *step;
	Palette[k].v = 1. + (double)i *step * (hsv.v - 1.);	/* if pure v = 1. */

	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* complementary or contrast color */
int complementary(char *name, PSCOLOR * rgb, int div, double sector)
{
    int i, k;
    double step;
    PALETTE hsv;

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);
    step = (div > 1) ? (sector / (double)(div - 1)) : 0.;

    hsv.h += 180.;
    if (div > 1)
	hsv.h -= (sector / 2.);

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = hsv.h + (double)i *step;

	Palette[k].s = hsv.s;
	Palette[k].v = hsv.v;

	if (Palette[k].h < 0.)
	    Palette[k].h += 360.;
	if (Palette[k].h >= 360.)
	    Palette[k].h -= 360.;
	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* analogous or similar color */
int analogous(char *name, PSCOLOR * rgb, int div, double sector)
{
    int i, k;
    double step;
    PALETTE hsv;

    RGB_HSV(rgb, &hsv);

    /* alloc memory */
    k = palette_new(div);
    step = (div > 1) ? (sector / (double)(div - 1)) : 0.;

    if (div > 1)
	hsv.h -= (sector / 2.);

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = hsv.h + (double)i *step;

	Palette[k].s = hsv.s;
	Palette[k].v = hsv.v;

	if (Palette[k].h < 0.)
	    Palette[k].h += 360.;
	if (Palette[k].h >= 360.)
	    Palette[k].h -= 360.;
	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* gradient */
int gradient(char *name, PSCOLOR * A, PSCOLOR * B, int div, int pure)
{
    int i, k;
    double h_step, s_step, v_step;
    PALETTE pal_A, pal_B;

    RGB_HSV(A, &pal_A);
    RGB_HSV(B, &pal_B);

    if (pal_A.h == pal_B.h || div < 2)
	return 0;

    /* alloc memory */
    k = palette_new(div);

    if (pal_A.h < pal_B.h)
	pal_A.h += 360;

    h_step = (pal_B.h - pal_A.h) / (div - 1.);
    s_step = (pal_B.s - pal_A.s) / (div - 1.);
    v_step = (pal_B.v - pal_A.v) / (div - 1.);

    for (i = 0; i < div; i++, k++) {
	Palette[k].h = pal_A.h + (double)i *h_step;
	Palette[k].s = pure ? 1. : pal_A.s + (double)i *s_step;
	Palette[k].v = pure ? 1. : pal_A.v + (double)i *v_step;

	if (Palette[k].h < 0.)
	    Palette[k].h += 360.;
	if (Palette[k].h >= 360.)
	    Palette[k].h -= 360.;
	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}

/* diverging */
int diverging(char *name, PSCOLOR * A, PSCOLOR * B, int div)
{
    int i, k;
    double h_step, v_step, tmp;
    PALETTE pal_A, pal_B;

    RGB_HSV(A, &pal_A);
    RGB_HSV(B, &pal_B);

    if (pal_A.h == pal_B.h || div < 2)
	return 0;

    /* alloc memory */
    k = palette_new(div);

    if (pal_A.h < pal_B.h)
	pal_A.h += 360;

    div -= 1;
    h_step = (pal_B.h - pal_A.h) / div;
    v_step = (pal_B.v - pal_A.v) / div;

    for (i = 0; i < (div + 1); i++, k++) {
	tmp = (2. * i / div - 1.);
	Palette[k].h = pal_A.h + (double)i *h_step;

	Palette[k].s = tmp * tmp;
	Palette[k].v = pal_A.v + (double)i *v_step;

	if (Palette[k].h < 0.)
	    Palette[k].h += 360.;
	if (Palette[k].h >= 360.)
	    Palette[k].h -= 360.;
	sprintf(Palette[k].name, "%s%d", name, i + 1);
    }

    return 1;
}


/*
 * TRANSFORMATIONS BETWEEN COLORSPACES
 */

/* r, g, b values are from 0 to 1
   h = [0,360], s = [0,1], v = [0,1]
 */
void RGB_HSV(PSCOLOR * col, PALETTE * pal)
{
    double min, max, delta;
    int r_max = 1, b_max = 0;

    min = max = col->r;
    if (min > col->g) {
	if (col->b < col->g) {
	    min = col->b;
	}
	else {
	    min = col->g;
	    if (col->b > col->r) {
		max = col->b;
		b_max = 1;
		r_max = 0;
	    }
	}
    }
    else {
	if (col->b > col->g) {
	    max = col->b;
	    b_max = 1;
	    r_max = 0;
	}
	else {
	    max = col->g;
	    r_max = 0;
	    if (col->b < col->r)
		min = col->b;
	}
    }

    pal->v = max;
    if (max == 0 || (delta = max - min) == 0) {
	pal->s = pal->h = 0;
	return;
    }
    pal->s = delta / max;
    if (r_max == 1) {
	pal->h = (col->g - col->b) / delta;
    }
    else if (b_max == 1) {
	pal->h = 4 + (col->r - col->g) / delta;
    }
    else {
	pal->h = 2 + (col->b - col->r) / delta;
    }
    pal->h *= 60.;
    if (pal->h < 0)
	pal->h += 360.;

    return;
}


/* r, g, b values are from 0 to 1
   h = [0,360], s = [0,1], v = [0,1]
 */
void HSV_RGB(PALETTE * pal, PSCOLOR * col)
{
    /* achromatic, gray */
    if (pal->s == 0) {
	col->r = col->g = col->b = pal->v;
	return;
    }

    double f, p, q, t;
    int i;

    //     f = modf(pal->h * 60, &t);
    //     i = ((int) t) % 60;
    i = floor(pal->h / 60.);
    f = pal->h / 60. - (double)i;

    p = pal->v * (1. - pal->s);
    q = pal->v * (1. - pal->s * f);
    t = pal->v * (1. - pal->s * (1. - f));
    switch (i) {
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
    case 5:
	col->r = pal->v;
	col->g = p;
	col->b = q;
	break;
    default:
	col->none = 1;
    }
}
