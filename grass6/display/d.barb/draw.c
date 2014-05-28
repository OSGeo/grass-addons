#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/display.h>
#include <grass/symbol.h>
#include <grass/glocale.h>
#include "local_proto.h"


/* draw a single barb at the given map coordinates */
void draw_barb(double easting, double northing, double velocity,
	       double compass_deg, int color, double scale, int style)
{
    double radius;
    G_debug(3, "in draw_barb()");

    //dbg:    unknown_(594578,4920392);

    D_raster_use_color(color);

    R_move_abs((int)(D_u_to_d_col(easting) + 0.5),
	       (int)(D_u_to_d_row(northing) + 0.5));

    if (style == TYPE_ARROW || style == TYPE_STRAW) {
	if (velocity == velocity)	/* ie not NaN */
	    arrow_mag(easting, northing, compass_deg, velocity, style);
	else
	    arrow_360(easting, northing, compass_deg, TYPE_GRASS, scale,
		      style);
    }
    else {
	/* calc barb parameters */
	//dbg: compass_deg=0;
	/* draw barb bits */
	if (style == TYPE_SMLBARB)
	    radius = 5.0;
	else
	    radius = 10.0;

	draw_circle(easting, northing, radius, FALSE);
	draw_feather(easting, northing, radius, velocity,
		     compass_deg);

	//dbg:      int i;
	//      for (i=0; i < 360; i+=20)
	//          draw_feather(easting, northing, 20.0 /*radius*/, velocity, i);
    }

    return;
}

/* draw an arrow, with only direction */
void arrow_360(double easting, double northing, double theta, int aspect_type,
	       double scale, int style)
{
    arrow_mag(easting, northing,
	      aspect_type == TYPE_GRASS ? theta : 90 - theta, scale, style);
    return;
}


/* draw an arrow, with magnitude and direction */
/* angle is measured in degrees counter-clockwise from east */
void arrow_mag(double easting, double northing, double theta, double length,
	       int style)
{
    double x, y, dx, dy, tail_x, tail_y;
    double theta_offset;

    G_debug(4, "in arrow_mag()");

    /* convert to compass dir ?! */
    theta = 90 - theta;
    if (theta < 0)
	theta += 360;

    /* display coords use inverse y */
    theta *= -1;

    tail_x = D_u_to_d_col(easting);
    tail_y = D_u_to_d_row(northing);

    /* tail */
    R_move_abs((int)(tail_x + 0.5), (int)(tail_y + 0.5));

    /* head */
    x = tail_x + (length * cos(D2R(theta)));
    y = tail_y + (length * sin(D2R(theta)));
    R_cont_abs((int)(x + 0.5), (int)(y + 0.5));


    if (style == TYPE_ARROW) {
	theta_offset = theta + 20;
	if (theta_offset > 360)
	    theta_offset -= 360;

	/* fin 1 */
	dx = tail_x + (0.6 * length * cos(D2R(theta_offset)));
	dy = tail_y + (0.6 * length * sin(D2R(theta_offset)));
	R_cont_abs((int)(dx + 0.5), (int)(dy + 0.5));

	/* fin 2 */
	R_move_abs((int)(x + 0.5), (int)(y + 0.5));
	theta_offset = theta - 20;
	dx = tail_x + (0.6 * length * cos(D2R(theta_offset)));
	dy = tail_y + (0.6 * length * sin(D2R(theta_offset)));
	R_cont_abs((int)(dx + 0.5), (int)(dy + 0.5));
    }
}


/* draw a grey '?' if data is non-sensical */
void unknown_(double easting, double northing)
{
    double x, y;

    x = D_u_to_d_col(easting);
    y = D_u_to_d_row(northing);

    R_standard_color(D_translate_color("grey"));

    R_move_abs((int)(x + 0.5), (int)(y + 0.5));
    R_text_size(8, 8);
    R_text("?");
}

/* put a "+" at the percentage of the display frame */
void mark_the_spot(double perc_x, double perc_y)
{
    SYMBOL *Symb;
    RGBA_Color *line_color, *fill_color;
    int R, G, B;
    int Xpx, Ypx;
    int t, b, l, r;
    int color;

    line_color = G_malloc(sizeof(RGBA_Color));
    fill_color = G_malloc(sizeof(RGBA_Color));
    Symb = S_read("basic/cross1");

    G_str_to_color("black", &R, &G, &B);
    line_color->r = (unsigned char)R;
    line_color->g = (unsigned char)G;
    line_color->b = (unsigned char)B;
    line_color->a = RGBA_COLOR_OPAQUE;
    //?
    //    R_RGB_color(R, G, B);

    color = G_str_to_color("yellow", &R, &G, &B);
    fill_color->r = (unsigned char)R;
    fill_color->g = (unsigned char)G;
    fill_color->b = (unsigned char)B;
    fill_color->a = RGBA_COLOR_OPAQUE;

    S_stroke(Symb, 6, 0, 0);

    D_get_screen_window(&t, &b, &l, &r);
    Xpx = (int)((perc_x * (r - l) / 100.) + 0.5);
    Ypx = (int)(((100. - perc_y) * (b - t) / 100.) + 0.5);

    D_symbol(Symb, Xpx, Ypx, line_color, fill_color);

    return;
}


/* draws a circle at the map coords given by e,n.
   radius is in display pixels, fill is boolean */

/*** change fill to int=0-8 for cloud cover? ***/
void draw_circle(double easting, double northing, double radius, int fill)
{
    int i, n;
    double angle, step = 5.0;
    int *xi, *yi;

    G_debug(4, "draw_circle()");

    n = (int)(360 / step) + 1;	/* number of vertices */

    xi = G_calloc(n + 1, sizeof(int));
    yi = G_calloc(n + 1, sizeof(int));

    /* for loop moving around the circle */
    for (i = 0; i <= n; i++) {
	angle = D2R(step * i);
	xi[i] = (int)floor(0.5 + D_u_to_d_col(easting) + radius * cos(angle));
	yi[i] =
	    (int)floor(0.5 + D_u_to_d_row(northing) + radius * sin(angle));
	G_debug(5, "angle=%.2f   xi[%d]=%d  yi[%d]=%d", step * i, i, xi[i], i,
		yi[i]);
    }

    /* close it */
    xi[n] = xi[0];
    yi[n] = yi[0];

    if (fill)
	R_polygon_abs(xi, yi, n);
    else
	R_polyline_abs(xi, yi, n);

    G_free(xi);
    G_free(yi);

    return;
}


/* draws the stem and tail of a wind barb centred at e,n.
   radius is scaling in display pixels, velocity is assumed as knots,
   angle is Cartesian convention CCW from positive x-axis */
void draw_feather(double easting, double northing, double radius,
		  double velocity, double compass_deg)
{
    double x, y, dx, dy, angle, rot_angle, flag_angle1, flag_angle2;
    double stem_length = 5.;	/* length of tail */
    double xd[4], yd[4];
    int i, xi[4], yi[4];

    G_debug(4, "draw_feather()");

    angle = compass_deg - 90;
    if (angle < 0)
	angle += 360;
    else if (angle > 360)
	angle -= 360;

    /* barb points to FROM direction */
    angle += 180;
    if (angle > 360)
	angle -= 360;

    rot_angle = angle + 60;
    if (rot_angle > 360)
	rot_angle -= 360;

    flag_angle1 = rot_angle + 30;
    if (flag_angle1 > 360)
	flag_angle1 -= 360;
    /* for equilateral flag ~150 is good, try 45,195 */
    flag_angle2 = flag_angle1 + 150;
    if (flag_angle2 > 360)
	flag_angle2 -= 360;


    G_debug(5, "  compass_deg=%.2f   angle=%.2f   rot_angle=%.2f",
	    compass_deg, angle, rot_angle);

    /* D_line_width(2); */

    if (velocity < 5) {
	/*dot:  draw_circle(easting, northing, 2.0, TRUE); */
	draw_circle(easting, northing, 3 * radius / 4, FALSE);
	return;
    }

    //R_RGB_color(255, 0, 0);
    /* move to head */
    x = D_u_to_d_col(easting) + radius * cos(D2R(angle));
    y = D_u_to_d_row(northing) + radius * sin(D2R(angle));
    R_move_abs((int)floor(x + 0.5), (int)floor(y + 0.5));

    /* draw to tail */
    dx = D_u_to_d_col(easting) + stem_length * radius * cos(D2R(angle));
    dy = D_u_to_d_row(northing) + stem_length * radius * sin(D2R(angle));
    R_cont_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));

    /* TODO: simplify following into loops */
    if (velocity < 50) {
	//R_RGB_color(0, 255, 0);
	if (velocity >= 10) {
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 5) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  0.5) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   0.5) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	//R_RGB_color(0, 0, 255);
	if (velocity >= 20) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  0.5) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   0.5) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 15) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  0.5) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   0.5) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	//R_RGB_color(0, 255, 255);
	if (velocity >= 30) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 25) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	//R_RGB_color(255, 255, 0);
	if (velocity >= 40) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1.5) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1.5) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 35) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1.5) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1.5) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 45) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;
    }


    //R_RGB_color(255, 0, 255);
    /* beyond 50 kts gets a filled triangle (flag) at the end */
    if (velocity >= 50) {
	/* inner angle is same as barb lines, outer angle is perpendicular to the barb */
	xd[0] =
	    D_u_to_d_col(easting) + stem_length * radius * cos(D2R(angle));
	yd[0] =
	    D_u_to_d_row(northing) + stem_length * radius * sin(D2R(angle));
	xd[1] = xd[0] + radius * 2 * cos(D2R(flag_angle1));
	yd[1] = yd[0] + radius * 2 * sin(D2R(flag_angle1));
	xd[2] = xd[1] + radius * 2 * (2 / sqrt(3)) * cos(D2R(flag_angle2));	/* cos(30)=sqrt(3)/2 */
	yd[2] = yd[1] + radius * 2 * (2 / sqrt(3)) * sin(D2R(flag_angle2));
	xd[3] = xd[0];
	yd[3] = yd[0];

	for (i = 0; i < 4; i++) {
	    xi[i] = (int)floor(xd[i] + 0.5);
	    yi[i] = (int)floor(yd[i] + 0.5);
	}
	R_polygon_abs(xi, yi, 4);
    }

    if (velocity < 100) {

	if (velocity >= 60) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1.6) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1.6) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 55) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  1.6) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   1.6) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 70) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 65) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 80) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.6) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.6) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 75) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.6) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.6) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 90) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 85) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.1) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.1) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 95) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.6) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.6) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;
    }

    /* beyond 100 kts gets two 50kt flags at the end */
    if (velocity >= 100) {
	/* inner angle is same as barb lines, outer angle is perpendicular to the barb */
	xd[0] = xd[2];
	yd[0] = yd[2];
	xd[1] = xd[0] + radius * 2 * cos(D2R(flag_angle1));
	yd[1] = yd[0] + radius * 2 * sin(D2R(flag_angle1));
	xd[2] = xd[1] + radius * 2 * (2 / sqrt(3)) * cos(D2R(flag_angle2));	/* cos(30)=sqrt(3)/2 */
	yd[2] = yd[1] + radius * 2 * (2 / sqrt(3)) * sin(D2R(flag_angle2));
	xd[3] = xd[0];
	yd[3] = yd[0];

	for (i = 0; i < 4; i++) {
	    xi[i] = (int)floor(xd[i] + 0.5);
	    yi[i] = (int)floor(yd[i] + 0.5);
	}
	R_polygon_abs(xi, yi, 4);
    }


    if (velocity < 150) {

	if (velocity >= 110) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.8) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.8) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 105) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  2.8) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   2.8) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 120) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.2) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.2) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 115) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.2) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.2) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 130) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.7) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.7) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 125) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  3.7) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   3.7) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 140) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  4.2) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   4.2) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * 2 * cos(D2R(rot_angle));
	    y = dy + radius * 2 * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else if (velocity >= 135) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  4.2) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   4.2) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;

	if (velocity >= 145) {
	    dx = D_u_to_d_col(easting) + (stem_length -
					  4.7) * radius * cos(D2R(angle));
	    dy = D_u_to_d_row(northing) + (stem_length -
					   4.7) * radius * sin(D2R(angle));
	    R_move_abs((int)floor(dx + 0.5), (int)floor(dy + 0.5));
	    x = dx + radius * cos(D2R(rot_angle));
	    y = dy + radius * sin(D2R(rot_angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));

	    R_move_abs((int)(D_u_to_d_col(easting) + 0.5),
		       (int)(D_u_to_d_row(northing) + 0.5));
	    x = D_u_to_d_col(easting) + radius * cos(D2R(angle));
	    y = D_u_to_d_row(northing) + radius * sin(D2R(angle));
	    R_cont_abs((int)floor(x + 0.5), (int)floor(y + 0.5));
	}
	else
	    return;
    }


    /* beyond 150 kts gets three 50kt flags at the end */
    if (velocity >= 150) {
	/* inner angle is same as barb lines, outer angle is perpendicular to the barb */
	xd[0] = xd[2];
	yd[0] = yd[2];
	xd[1] = xd[0] + radius * 2 * cos(D2R(flag_angle1));
	yd[1] = yd[0] + radius * 2 * sin(D2R(flag_angle1));
	xd[2] = xd[1] + radius * 2 * (2 / sqrt(3)) * cos(D2R(flag_angle2));	/* cos(30)=sqrt(3)/2 */
	yd[2] = yd[1] + radius * 2 * (2 / sqrt(3)) * sin(D2R(flag_angle2));
	xd[3] = xd[0];
	yd[3] = yd[0];

	for (i = 0; i < 4; i++) {
	    xi[i] = (int)floor(xd[i] + 0.5);
	    yi[i] = (int)floor(yd[i] + 0.5);
	}
	R_polygon_abs(xi, yi, 4);
    }

    /* barb rendering currently saturates at 150 kts */

    return;
}
