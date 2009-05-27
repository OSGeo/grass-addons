
#define LEFT    0
#define RIGHT   1
#define LOWER   0
#define UPPER   1
#define CENTER  2

#define NONE   0
#define POINTS 1
#define LINES  2
#define AREAS  3

#define DEF_FONT "Helvetica"

/* cat_val.c */
#ifdef DBMIN_H
int load_catval_array(VECTOR *, const char *, dbCatValArray *);
int get_number(dbCatValArray *, int, double *);
char * get_string(dbCatValArray *, int);
#endif

/* colors.c */
#ifdef _PSCOLOR_H_
int set_color_name(PSCOLOR *, char *);
void set_color_rgb(PSCOLOR *, int, int, int);
void unset_color(PSCOLOR *);
void set_ps_color(PSCOLOR *);
int set_ps_grey(PSCOLOR *);
void set_ps_rgb(int, int, int);
#endif

/* eps.c */
int eps_bbox(char *, double *, double *, double *, double *);
int eps_trans(double, double, double, double, double, double,
              double, double, double *, double *);
#ifdef _STDIO_H
int eps_save(FILE *, char *, char *);
int eps_draw_saved(FILE *, char *, double, double, double, double);
int eps_draw(FILE *, char *, double, double, double, double);
int pat_save(FILE *, char *, char *);
#endif

/* fonts.c */
#ifdef _PSFONT_H_
double set_ps_font(PSFONT *);
double set_ps_font_nocolor(PSFONT *);
#endif

/* frames.c */
#ifdef _PSFRAME_H_
void set_box_orig(PSFRAME *);
void set_box_size(PSFRAME *, double, double);
void set_box_draw(PSFRAME *);
void set_box_auto(PSFRAME *, PSFONT *, double);
void set_box_readjust_title(PSFRAME *, const char *);
void set_box_readjust(PSFRAME *, double, double, double, double);
#endif

/* input.c */
int input(int, char *);
int key_data(char *, char **, char **);
int error(char *, char *, char *);

/* legends.c */
#ifdef _LEGENG_H_
void set_legend_adjust(LEGEND *, double);
#endif

/* lines.c */
#ifdef _PSLINE_H_
int set_ps_linewidth(double);
int set_ps_line(PSLINE *);
int set_ps_line_no_color(PSLINE *);
#endif

/* load_raster.c */
int load_group(char *);
int load_cell(int, char *);
int load_rgb(char *, char *, char *);

/* paper.c */
int set_paper(char *);

/* ps3_map.c */
int PS3_map(void);

/* proj_geo.c */
#ifdef _GPROJECTS_H
void init_proj(struct pj_info *, struct pj_info *);
int find_limits(double *, double *, double *, double *, struct pj_info *, struct pj_info *);
#endif

/* r_draw.c */
int read_draw(char *);

/* r_font.c */
int get_font(char *);
#ifdef _PSFONT_H_
int default_font(PSFONT *);
int read_font(char *, PSFONT *);
#endif

/* r_frame.c */
#ifdef _PSFRAME_H_
int default_frame(PSFRAME *, int, int);
int read_frame(PSFRAME *);
#endif

/* r_grid.c */
#ifdef _GRID_H_
int read_grid(GRID *, int);
#endif

/* r_line.c */
#ifdef _PSLINE_H_
int default_psline(PSLINE *);
int read_psline(char *, PSLINE *);
#endif

/* r_maparea.c */
int read_maparea(void);

/* r_note.c */
int read_note(char *);

/* r_paper.c */
int read_paper(char *);

/* r_raster.c */
int read_raster(char *);

/* r_rlegend.c */
int read_rlegend(char *);

/* r_vareas.c */
int r_vareas(char *);

/* r_vlegend.c */
int read_vlegend(char *);

/* r_vlines.c */
int r_vlines(char *);

/* r_vpoints.c */
int r_vpoints(char *);

/* raster.c */
int raster_close(void);

/* scanners.c */
int scan_easting(char *, double *);
int scan_northing(char *, double *);
int scan_resolution(char *, double *);
int scan_percent(char *, double *, double, double);
int scan_ref(char *, int *, int *);
int scan_yesno(char *, char *);
#ifdef _PSCOLOR_H_
int scan_color(char *, PSCOLOR *);
#endif
int scan_dimen(char *, double *);
int scan_second(char *, double *);

/* set_draw.c */
int set_draw(char *, char*);

/* set_geogrid.c */
int set_lines_geogrid(void);
int set_numbers_geogrid(void);
#ifdef _PSLINE_H_
int set_geogrid_lines(PSLINE *, int);
#endif
int set_geogrid_inner_numbers(void);
int set_geogrid_outer_numbers(void);

/* set_grid.c */
int set_lines_grid(void);
int set_numbers_grid(void);
#ifdef _PSLINE_H_
int set_grid_lines(char, PSLINE *, int);
#endif
int set_grid_inner_numbers(void);
int set_grid_outer_numbers(void);
int set_grid_iho_numbers(void);
int set_grid_fine_border(double, double);
int set_grid_minor_border(double, double, double);
int set_grid_major_border(double, double);
int set_grid_corners(double, double);

/* set_mask.c */
int set_mask(void);

/* set_note.c */
int note_int_file(char *);
int set_note(int);

/* set_ps.c */
void set_ps_rect(double, double, double, double);
int set_ps_where(char, double, double);
int set_xy_where(char *, double, double, char*);
#ifdef _VECTOR_H_
int set_ps_pattern(int, char *, VAREAS *);
int set_ps_symbol_eps(int, VPOINTS *, char *);
#endif

/* set_raster.c */
int set_raster(void);
int set_raster_cell(void);
int set_raster_rgb(void);
int set_raster_maskcell(void);
int set_raster_maskcolor(void);

/* set_rlegend.c */
int set_rlegend_cats(void);
int set_rlegend_gradient(void);
static double nice_step(double, int, int*);

/* set_scalebar.c */
char *strnumber(double);
int set_scalebar(void);

/* set_vector.c */
int set_vector(int, int);
#ifdef GRASS_VECT_H
int set_vareas(VECTOR, VAREAS *);
int set_vpoints(VECTOR, VPOINTS *);
int set_vlines(VECTOR, VLINES *, int);
int vector_line(struct line_pnts *);
#endif

/* start_map.c */
int start_map(void);

/* symbol.c */
#if defined GRASS_SYMB_H
int draw_chain(SYMBCHAIN *, double);
int symbol_save(int, VPOINTS *, SYMBOL *);
#endif

/* val_list.c */
#ifdef GRASS_GIS_H
int parse_val_list(char *, DCELL **);
int sort_list(char *, int, CELL **);
#endif

/* vector.c */
int vector_new(void);
int where_moveto(double, double);
int where_lineto(double, double);
