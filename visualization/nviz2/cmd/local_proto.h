#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <grass/nviz.h>

/* module flags and parameters */
struct GParams { 
  struct Option *elev, *color_map, *color_const, /* raster */
    *vector, /* vector */
    *exag, *bgcolor, /* misc */
    *pos, *height, *persp, *twist, /* viewpoint */
    *output, *format, *size; /* output */
};

/* args.c */
void parse_command(int, char**, struct GParams *);
int color_from_cmd(const char *);

/* write_img.c */
int write_img(const char *, int);

#endif /* __LOCAL_PROTO_H__ */
