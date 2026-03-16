#pragma once

#include <grass/gis.h>

#include "global.h"

void Mouse_pointer(int *, int *, int *);
void display_one_point(View *, double, double);
int point_in_view(View *, double, double);
void rectangle(int, int, int, int);
void point(int, int);
int read_points_from_file(Training *, char *);
void display_title(View *);
void Configure_view(View *, char *, char *, double, double);
int In_view(View *, int, int);
void Erase_view(View *);
double magnification(View *view);
void write_map(struct Cell_head *, char *, const char *, char *);
void compute_temp_region2(struct Cell_head *, struct Cell_head *, double,
                          double, int, int);
void compute_temp_region(struct Cell_head *, struct Cell_head *, double, double,
                         double, double);
void Outline_box(int, int, int, int);
void Init_graphics2(void);
void Init_graphics(void);

int Text_width(char *);
void Text(char *, int, int, int, int, int);
void Uparrow(int, int, int, int);
void Downarrow(int, int, int, int);
void display_map(struct Cell_head *, View *, char *, char *);
void drawcell(View *);
void exit_button(void);
void info_button(void);

void row_to_northing(struct Cell_head *, int, double, double *);
void col_to_easting(struct Cell_head *, int, double, double *);
void northing_to_row(struct Cell_head *, double, int *);
void easting_to_col(struct Cell_head *, double, int *);
void from_screen_to_geo(View *, int, int, double *, double *);
int view_to_col(View *, int);
int view_to_row(View *, int);
int col_to_view(View *, int);
int row_to_view(View *, int);
void dot(int, int);
