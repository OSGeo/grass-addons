#ifndef __LOCAL_PROTO_H__
#define __LOCAL_PROTO_H__

#include <stdio.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include "globals.h"

/* header.c */
int read_ply_header(struct ply_file *ply);

/* body */
int get_element_data(struct ply_file *ply, struct prop_data *data);
int get_element_list(struct ply_file *ply);
int append_vertex(struct Map_info *Map, struct line_pnts *Points, int cat);

#endif /* __LOCAL_PROTO_H__ */
