/* **************************************************************
 * 
 *  MODULE:       v.in.redwg
 *  
 *  AUTHOR(S):    Rodrigo Rodrigues da Silva
 *                based on original code by Radim Blazek
 *                
 *  PURPOSE:      Import of DWG files (using free software lib)
 *                
 *  COPYRIGHT:    (C) 2001, 2010 by the GRASS Development Team
 * 
 *                This program is free software under the 
 *                GNU General Public License (>=v2). 
 *                Read the file COPYING that comes with GRASS
 *                for details.
 * 
 * **************************************************************/

/*
 * Unsupported entities must be added in write_entity()
 *
 * TODO: 3rd dimension is not functional for CIRCLE and ARC
 *       -> required updated of transformation in INSERT
 *          (how to do that??)
 */

#define AD_PROTOTYPES
#define AD_VM_PC

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <fcntl.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/dbmi.h>
#include <grass/vector.h>
#include <dwg.h>
#include "global.h"

#define exampleprintf printf
#define LOCPI M_PI

char buf[1000];
char buf2[1000];

void getEntTypeName(Dwg_Object *obj, char *name)
{
    switch (obj->type)
    {
    case DWG_TYPE_LINE:
	strcpy(name, "LINE");
	break;
    case DWG_TYPE_POINT:
	strcpy(name, "POINT");
	break;
    case DWG_TYPE_CIRCLE:
	strcpy(name, "CIRCLE");
	break;
    case DWG_TYPE_SHAPE:
	strcpy(name, "SHAPE");
	break;
    case DWG_TYPE_ELLIPSE:
	strcpy(name, "ELLIPSE");
	break;
    case DWG_TYPE_SPLINE:
	strcpy(name, "SPLINE");
	break;
    case DWG_TYPE_TEXT:
	strcpy(name, "TEXT");
	break;
    case DWG_TYPE_ARC:
	strcpy(name, "ARC");
	break;
    case DWG_TYPE_TRACE:
	strcpy(name, "TRACE");
	break;
    case DWG_TYPE_SOLID:
	strcpy(name, "SOLID");
	break;
    case DWG_TYPE_BLOCK:
	strcpy(name, "BLOCK");
	break;
    case DWG_TYPE_ENDBLK:
	strcpy(name, "ENDBLK");
	break;
    case DWG_TYPE_INSERT:
	strcpy(name, "INSERT");
	break;
    case DWG_TYPE_ATTDEF:
	strcpy(name, "ATTDEF");
	break;
    case DWG_TYPE_ATTRIB:
	strcpy(name, "ATTRIB");
	break;
    case DWG_TYPE_SEQEND:
	strcpy(name, "SEQEND");
	break;
    case DWG_TYPE_POLYLINE_2D:
    case DWG_TYPE_POLYLINE_3D:
	strcpy(name, "POLYLINE");
	break;
    case  DWG_TYPE_VERTEX_2D:
    case  DWG_TYPE_VERTEX_3D:
    case  DWG_TYPE_VERTEX_MESH:
    case  DWG_TYPE_VERTEX_PFACE:
    case  DWG_TYPE_VERTEX_PFACE_FACE:
	strcpy(name, "VERTEX");
	break;
	/*
    case AD_ENT_LINE3D:
	strcpy(name, "3DLINE");
	break;
    case AD_ENT_FACE3D:
	strcpy(name, "3DFACE");
	break;
	*/

    case  DWG_TYPE_DIMENSION_ORDINATE:
    case  DWG_TYPE_DIMENSION_LINEAR:
    case  DWG_TYPE_DIMENSION_ALIGNED:
    case  DWG_TYPE_DIMENSION_ANG3PT:
    case  DWG_TYPE_DIMENSION_ANG2LN:
    case  DWG_TYPE_DIMENSION_RADIUS:
    case  DWG_TYPE_DIMENSION_DIAMETER:
	strcpy(name, "DIMENSION");
	break;
    case DWG_TYPE_VIEWPORT:
	strcpy(name, "VIEWPORT");
	break;
    case DWG_TYPE__3DSOLID:
	strcpy(name, "SOLID3D");
	break;
    case DWG_TYPE_RAY:
	strcpy(name, "RAY");
	break;
    case DWG_TYPE_XLINE:
	strcpy(name, "XLINE");
	break;
    case DWG_TYPE_MTEXT:
	strcpy(name, "MTEXT");
	break;
    case DWG_TYPE_LEADER:
	strcpy(name, "LEADER");
	break;
    case DWG_TYPE_TOLERANCE:
	strcpy(name, "TOLERANCE");
	break;
    case DWG_TYPE_MLINE:
	strcpy(name, "MLINE");
	break;
    case DWG_TYPE_BODY:
	strcpy(name, "BODY");
	break;
    case DWG_TYPE_REGION:
	strcpy(name, "REGION");
	break;
    default:
       strcpy(name, "UNKNOWN");
       /*
	if (adenhd->enttype == adOle2frameEnttype(dwghandle))
	    strcpy(name, "OLE2FRAME");
	else if (adenhd->enttype == adLwplineEnttype(dwghandle))
	    strcpy(name, "LWPOLYLINE");
	else if (adenhd->enttype == adHatchEnttype(dwghandle))
	    strcpy(name, "HATCH");
	else if (adenhd->enttype == adImageEnttype(dwghandle))
	    strcpy(name, "IMAGE");
	else if (adenhd->enttype == adArcAlignedTextEnttype(dwghandle))
	    strcpy(name, "ArcAlignedText");
	else if (adenhd->enttype == adWipeoutEnttype(dwghandle))
	    strcpy(name, "Wipeout");
	else if (adenhd->enttype == adRtextEnttype(dwghandle))
	    strcpy(name, "Rtext");
	else {

	    G_debug(3, "adenhd->enttype: %d", adenhd->enttype);
	    strcpy(name, "Proxy");
	}
	*/
	break;
    }
}

int write_line(Dwg_Object * obj, int type, int level)
{
    int i, l;
    double x, y, z, r, ang;

    /*
    adSeekLayer(dwghandle, obj->entlayerobjhandle, Layer);
    */

    /* Transformation, go up through all levels of transformation */
    /* not sure what is the right order of transformation */
    for (l = level; l >= 0; l--) {
	for (i = 0; i < Points->n_points; i++) {
	    /* scale */
	    x = Points->x[i] * Trans[l].xscale;
	    y = Points->y[i] * Trans[l].yscale;
	    z = Points->z[i] * Trans[l].zscale;
	    /* rotate */
	    r = sqrt(x * x + y * y);
	    ang = atan2(y, x) + Trans[l].rotang;
	    x = r * cos(ang);
	    y = r * sin(ang);
	    /* move */
	    x += Trans[l].dx;
	    y += Trans[l].dy;
	    z += Trans[l].dz;
	    Points->x[i] = x;
	    Points->y[i] = y;
	    Points->z[i] = z;
	}
    }

    Vect_reset_cats(Cats);
    Vect_cat_set(Cats, 1, cat);
    Vect_write_line(&Map, type, Points, Cats);

    /* Cat */
    sprintf(buf, "insert into %s values ( %d", Fi->table, cat);
    db_set_string(&sql, buf);

    /* Entity name */
    getEntTypeName(obj, buf2);
    sprintf(buf, ", '%s'", buf2);
    db_append_string(&sql, buf);

    /* Color */
    sprintf(buf, ", %lu", obj->tio.entity->color.rgb);
    db_append_string(&sql, buf);

    /* Weight */
    sprintf(buf, ", %d", obj->tio.entity->linewt);
    db_append_string(&sql, buf);

    /* Layer name */

    /*!Layer->purgedflag && */

    printf("This should be a layer: " );
    Dwg_Object * should_be_layer = obj->tio.entity->layer->obj;
    Dwg_Object_LAYER * layer;
    unsigned int _type = should_be_layer->type;
    //dwg_print_object(should_be_layer);
    printf("type = %u ", _type);
    if (_type == 51)
      {
        layer = obj->tio.entity->layer->obj->tio.object->tio.LAYER;
        printf ("IS A LAYER! name = %s", layer->name);
      }
    else printf("NOT A LAYER!");
    printf("\n");

    if (layer) {
      if (layer->name) {
	db_set_string(&str, layer->name);
	db_double_quote_string(&str);
	sprintf(buf, ", '%s'", db_get_string(&str));
      }
    }
    else {
	sprintf(buf, ", ''");
    }
    db_append_string(&sql, buf);

    /* Block name */
    if (Block != NULL) {
	db_set_string(&str, Block);
	db_double_quote_string(&str);
    }
    else {
	db_set_string(&str, "");
    }
    sprintf(buf, ", '%s'", db_get_string(&str));
    db_append_string(&sql, buf);

    /* Text */
    if (Txt != NULL) {
	db_set_string(&str, Txt);
	db_double_quote_string(&str);
    }
    else {
	db_set_string(&str, "");
    }
    sprintf(buf, ", '%s'", db_get_string(&str));
    db_append_string(&sql, buf);

    db_append_string(&sql, ")");
    G_debug(3, db_get_string(&sql));

    if (db_execute_immediate(driver, &sql) != DB_OK) {
	db_close_database(driver);
	db_shutdown_driver(driver);
	G_fatal_error("Cannot insert new row: %s", db_get_string(&sql));
    }

    cat++;
    return 0;
}

/* Returns 1 if element has geometry and may be written to vector */
int is_low_level(Dwg_Object *obj)
{
    if (obj->type == DWG_TYPE_BLOCK || obj->type == DWG_TYPE_ENDBLK ||
        obj->type == DWG_TYPE_SEQEND || obj->type == DWG_TYPE_INSERT)
    {
	return 0;
    }
    return 1;
}

void write_entity(Dwg_Object *obj, Dwg_Object ** objects,
      long unsigned int *ent_counter, int level)
{
    double x, y, z, ang;

    /* DWG entity pointers */
    Dwg_Entity_LINE *line;
    Dwg_Entity__3DFACE *face3d;
    Dwg_Entity_SOLID *solid;
    Dwg_Entity_TEXT *text;
    Dwg_Entity_POINT *point;
    Dwg_Entity_ARC *arc;
    Dwg_Entity_CIRCLE *circle;
    Dwg_Entity_BLOCK *block;
    Dwg_Entity_INSERT *insert;
    Dwg_Object *_obj;
    Dwg_Object_Object *_obj_obj;
    Dwg_Object_BLOCK_HEADER *blockhdr;


    *ent_counter += 1;
    if (is_low_level(obj))
	n_elements++;


    getEntTypeName(obj, buf);
    G_debug(1, "Entity: %s", buf);
    fprintf(stdout, "Entity: %s %u\n", buf, obj->type);

    Txt = NULL;
    Vect_reset_line(Points);

    /* Check space for lower level */
    if (level + 1 == atrans) {
	atrans += 10;
	Trans = (TRANS *) G_realloc(Trans, atrans * sizeof(TRANS));
    }

    switch (obj->type) {
    case DWG_TYPE_LINE:
        line = obj->tio.entity->tio.LINE;
	Vect_append_point(Points, line->start.x, line->start.y,
	    line->start.z);
	Vect_append_point(Points, line->end.x, line->end.y,
	            line->end.z);
	write_line(obj, GV_LINE, level);
	break;

    case DWG_TYPE__3DFACE:
        face3d = obj->tio.entity->tio._3DFACE;
	Vect_append_point(Points, face3d->corner1.x, face3d->corner1.y,
	    face3d->corner1.z);
        Vect_append_point(Points, face3d->corner2.x, face3d->corner2.y,
            face3d->corner2.z);
        Vect_append_point(Points, face3d->corner3.x, face3d->corner3.y,
            face3d->corner3.z);
        Vect_append_point(Points, face3d->corner4.x, face3d->corner4.y,
            face3d->corner4.z);
	write_line(obj, GV_FACE, level);
	break;

    case DWG_TYPE_SOLID:
        solid = obj->tio.entity->tio.SOLID;
        Vect_append_point(Points, solid->corner1.x, solid->corner1.y,
            solid->elevation);
        Vect_append_point(Points, solid->corner2.x, solid->corner2.y,
            solid->elevation);
        Vect_append_point(Points, solid->corner3.x, solid->corner3.y,
            solid->elevation);
        Vect_append_point(Points, solid->corner4.x, solid->corner4.y,
            solid->elevation);
	write_line(obj, GV_FACE, level);
	break;

    case DWG_TYPE_TEXT:
        text = obj->tio.entity->tio.TEXT;
	Txt = (char *)text->text_value;
	Vect_append_point(Points, text->ins_pt.x, text->ins_pt.y,
			  0); // ins_pt.z ??
	write_line(obj, GV_POINT, level);
	break;


    case DWG_TYPE_POINT:
        point = obj->tio.entity->tio.POINT;
	Vect_append_point(Points, point->x, point->y,
			  point->z);
	write_line(obj, GV_POINT, level);
	break;

    case DWG_TYPE_ARC:
        arc = obj->tio.entity->tio.ARC;
	for (ang = arc->start_angle; ang < arc->end_angle;
	     ang += 2 * LOCPI / 360) {
	    x = arc->center.x + arc->radius * cos(ang);
	    y = arc->center.y + arc->radius * sin(ang);
	    z = arc->center.z + arc->radius;
	    Vect_append_point(Points, x, y, z);
	}
	x = arc->center.x + arc->radius * cos(arc->end_angle);
	y = arc->center.y + arc->radius * sin(arc->end_angle);
	z = arc->center.z + arc->radius;
	Vect_append_point(Points, x, y, z);
	write_line(obj, GV_LINE, level);
	break;

    case DWG_TYPE_CIRCLE:
        circle = obj->tio.entity->tio.CIRCLE;
	if (circle_flag->answer) {
	    Vect_append_point(Points, circle->center.x,
	        circle->center.y, circle->center.z);
	    write_line(obj, GV_POINT, level);
	}
	else {
	    for (ang = 0; ang < 2 * LOCPI; ang += 2 * LOCPI / 360) {
                x = circle->center.x + circle->radius * cos(ang);
                y = circle->center.y + circle->radius * sin(ang);
                z = circle->center.z + circle->radius;
		Vect_append_point(Points, x, y, z);
	    }
	    Vect_append_point(Points, Points->x[0], Points->y[0],
			      Points->z[0]);
	    write_line(obj, GV_LINE, level);
	}
	break;

	/* BLOCK starts block of entities but makes no transformation - is it right ? 
	 *  -> do nothing just warn for xref */
    case DWG_TYPE_BLOCK:
        block = obj->tio.entity->tio.BLOCK;

	//FIXME figure out how to do it with LibreDWG
        /*
        if (block->namexrefpath[0]) {
	    G_warning
		("External reference for block not supported.\n  xref: %s",
		 ent->block.xrefpath);
	}
        */
	Block = G_store((char*)block->name);
	break;

    case DWG_TYPE_ENDBLK:	/* endblk - no data */
	G_free(Block);
	Block = NULL;
	break;

    case DWG_TYPE_INSERT:	/* insert */
        insert = obj->tio.entity->tio.INSERT;

	/* get transformation */
	/* TODO: fix rotation for CIRCLE and ARC */
	G_debug(3, " x,y,z: %f, %f, %f", insert->ins_pt.x,
	    insert->ins_pt.y, insert->ins_pt.z);
	G_debug(3, " xscale, yscale, zscale: %f, %f, %f", insert->scale.x,
	    insert->scale.y, insert->scale.z);
	G_debug(3, " rotang: %f", insert->rotation);
	/*
	G_debug(3, " ncols, nrows: %d, %d", ent->insert.numcols,
		ent->insert.numrows);
	G_debug(3, " coldist, rowdist: %f, %f", ent->insert.coldist,
		ent->insert.rowdist);
        */

	/* write block entities */
	//FIXME how to check purgedflag?
	/*
	if (!adblkh->purgedflag) {
	    adStartEntityGet(adblkh->entitylist);
        */
        printf("Handle do insert: %lu ", obj->handle.value);
        printf("Handle do block header do insert: %lu\n", insert->block_header->absolute_ref);
        fflush(stdout);

	//Dwg_Object_BLOCK_HEADER *blockhdr =
        _obj = insert->block_header->obj;
        _obj_obj = _obj->tio.object;
        blockhdr = _obj_obj->tio.BLOCK_HEADER;
	if (blockhdr->name[0] == ((unsigned char)'*')) //PSPACE OR MSPACE
	  {
            printf("Skipping PSPACE or MSPACE block\n");
            break;
	  }
        Dwg_Object *ent = blockhdr->first_entity->obj;
        while(42)
          {
            printf("Dentro do LOOP42\n");
            if (ent->type == DWG_TYPE_ENDBLK)
              {
                printf("Found ENDBLK, breaking\n");
                break;
              }
            else
              {
                Trans[level + 1].dx = insert->ins_pt.x;
                Trans[level + 1].dy = insert->ins_pt.y;
                Trans[level + 1].dz = insert->ins_pt.z;
                Trans[level + 1].xscale = insert->scale.x;
                Trans[level + 1].yscale = insert->scale.y;
                Trans[level + 1].zscale = insert->scale.z;
                Trans[level + 1].rotang = insert->rotation;
                printf("Writing inserted entity. Level = %d\n", level+1);
                write_entity(ent, objects, ent_counter, level+1);
                ent = dwg_next_object(ent);
                if (!ent) break;
              }
          }
        break;

    case DWG_TYPE_SEQEND:	/* seqend */
	break;

    default:
          getEntTypeName(obj, buf);
          G_warning("%s entity not supported", buf);
	break;

    }				/* end of switch */
}
