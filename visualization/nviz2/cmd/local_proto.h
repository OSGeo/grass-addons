#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include "render.h"
#include "nviz.h"

/* module flags and parameters */
struct GParams { 
  struct Option *elev, /* data */
    *pos, *height, *persp, *twist; /* viewpoint */
};

/* args.c */
void parse_command(int, char**, struct GParams *);

/* cplanes_obj.c */
int cplane_new(nv_data *, int);
int cplane_off(nv_data *, int);
int cplane_draw(nv_data *, int, int);

/* change_view.c */
int update_ranges(nv_data *);
int viewpoint_set_position(nv_data *,
			   float, float);
int viewpoint_set_height(nv_data *,
			 float);
int viewpoint_set_persp(nv_data *, int);
int viewpoint_set_twist(nv_data *, int);
void resize_window(int, int);

/* draw.c */
int draw_all_surf(nv_data *);
int draw_all(nv_data *);
int draw_quick(nv_data *);

/* map_obj.c */
int new_map_obj(int, const char *,
		nv_data *);
int set_attr(int, int, int, int, const char *,
	     nv_data *);
void set_att_default();

/* nviz.c */
void nv_data_init(nv_data *);

/* lights.c */
int light_set_position(nv_data *, int,
		       float, float, float, float);
int light_set_bright(nv_data *, int, float);
int light_set_color(nv_data *, int,
		    float, float, float);
int light_set_ambient(nv_data *, int,
		      float, float, float);
int light_init(nv_data *, int);
int light_new(nv_data *);

/* render.c */
void render_window_init(render_window *);
int render_window_create(render_window *, int, int);
int render_window_destroy(render_window *);
int render_window_make_current(const render_window *);
void swap_gl();

/* write_img.c */
int write_ppm(const char *);

#endif /* __LOCAL_PROTO_H__ */
